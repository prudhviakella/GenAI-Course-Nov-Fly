"""
================================================================================
Lambda Function: Error Processor (Container-based)
================================================================================

PURPOSE
-------
Processes validation error messages from SQS, aggregates them per upload,
generates an error CSV, uploads it to S3, updates upload history in RDS,
and triggers vendor notification via SNS when processing is complete.

ARCHITECTURE
------------
DynamoDB Streams → Validator Lambda → SQS (error queue)
    → Error Processor Lambda (this)
        → S3 (error CSV)
        → RDS (upload_history update)
        → SNS (vendor notification)

DESIGN PRINCIPLES
-----------------
- Event-driven, idempotent processing
- Batch aggregation by upload_id
- Clear audit trail (CSV + DB metadata)
- Production-grade observability (logs + tracebacks + metrics)
"""

# =============================================================================
# STANDARD LIBRARIES
# =============================================================================

import json
import csv
import os
import io
import logging
import traceback
from datetime import datetime
from collections import defaultdict

# =============================================================================
# AWS & THIRD-PARTY LIBRARIES
# =============================================================================

import boto3
import psycopg2
from psycopg2.extras import RealDictCursor
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)

# =============================================================================
# ENVIRONMENT VARIABLES
# =============================================================================

RDS_SECRET_NAME = os.environ.get("RDS_SECRET_NAME", "ecommerce/rds/credentials")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
REGION = os.environ.get("AWS_REGION", "us-east-1")

# =============================================================================
# AWS CLIENTS (REUSED ACROSS INVOCATIONS)
# =============================================================================

s3_client = boto3.client("s3", region_name=REGION)
sns_client = boto3.client("sns", region_name=REGION)
cloudwatch = boto3.client("cloudwatch", region_name=REGION)
secretsmanager = boto3.client("secretsmanager", region_name=REGION)

# =============================================================================
# SECRETS MANAGER CACHE
# =============================================================================

cache = SecretCache(
    config=SecretCacheConfig(),
    client=secretsmanager
)

# =============================================================================
# DATABASE CONNECTION (GLOBAL)
# =============================================================================

db_connection = None

# =============================================================================
# SECRETS & DATABASE HELPERS
# =============================================================================

def get_rds_credentials():
    """
    Retrieve RDS credentials from AWS Secrets Manager.

    Returns
    -------
    dict
        Database connection parameters
    """
    try:
        secret_string = cache.get_secret_string(RDS_SECRET_NAME)
        return json.loads(secret_string)
    except Exception as e:
        logger.critical(
            "Failed to retrieve RDS credentials",
            extra={"error": str(e), "traceback": traceback.format_exc()}
        )
        raise


def get_db_connection():
    """
    Reuse or create a PostgreSQL database connection.

    Returns
    -------
    psycopg2.connection
    """
    global db_connection

    try:
        if db_connection and not db_connection.closed:
            with db_connection.cursor() as cur:
                cur.execute("SELECT 1")
            return db_connection
    except Exception:
        db_connection = None

    try:
        creds = get_rds_credentials()
        db_connection = psycopg2.connect(
            host=creds["host"],
            port=creds.get("port", 5432),
            database=creds["dbname"],
            user=creds["username"],
            password=creds["password"],
            connect_timeout=5
        )
        logger.info("Connected to RDS successfully")
        return db_connection
    except Exception as e:
        logger.critical(
            "Database connection failed",
            extra={"error": str(e), "traceback": traceback.format_exc()}
        )
        raise

# =============================================================================
# ERROR PROCESSING UTILITIES
# =============================================================================

def parse_sqs_message(message):
    """
    Parse and normalize a single SQS error message.

    Parameters
    ----------
    message : dict
        Raw SQS message

    Returns
    -------
    dict | None
        Parsed error payload
    """
    try:
        body = json.loads(message["Body"])
        return {
            "upload_id": body.get("upload_id"),
            "vendor_id": body.get("vendor_id"),
            "record_id": body.get("record_id"),
            "row_number": body.get("row_number"),
            "error_type": body.get("error_type"),
            "error_message": body.get("error_message"),
            "product_data": body.get("product_data", {}),
            "timestamp": body.get("timestamp"),
            "receipt_handle": message["ReceiptHandle"]
        }
    except Exception:
        logger.error(
            "Failed to parse SQS message",
            extra={"traceback": traceback.format_exc()}
        )
        return None


def group_errors_by_upload(errors):
    """
    Group error records by upload_id.
    """
    grouped = defaultdict(list)
    for err in errors:
        if err and err.get("upload_id"):
            grouped[err["upload_id"]].append(err)
    return dict(grouped)


def create_error_csv(errors):
    """
    Generate CSV content summarizing validation errors.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # CSV header
    writer.writerow([
        "Row Number",
        "Vendor Product ID",
        "SKU",
        "Product Name",
        "Category",
        "Error Type",
        "Error Message",
        "Price",
        "Stock Quantity",
        "Brand",
        "Description"
    ])

    # Sort by CSV row number for readability
    for err in sorted(errors, key=lambda x: x.get("row_number", 0)):
        pd = err.get("product_data", {})
        writer.writerow([
            err.get("row_number"),
            pd.get("vendor_product_id"),
            pd.get("sku"),
            pd.get("product_name"),
            pd.get("category"),
            err.get("error_type"),
            err.get("error_message"),
            pd.get("price"),
            pd.get("stock_quantity"),
            pd.get("brand"),
            (pd.get("description") or "")[:100]
        ])

    return output.getvalue()

# =============================================================================
# S3 / RDS / SNS OPERATIONS
# =============================================================================

def upload_error_csv_to_s3(upload_id, vendor_id, csv_content):
    """
    Upload error CSV to S3 under errors/ prefix.
    """
    try:
        key = f"errors/{vendor_id}/{upload_id}_errors.csv"
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            Body=csv_content.encode("utf-8"),
            ContentType="text/csv"
        )
        logger.info("Uploaded error CSV to S3", extra={"s3_key": key})
        return key
    except Exception:
        logger.error(
            "Failed to upload error CSV to S3",
            extra={"traceback": traceback.format_exc()}
        )
        return None


def update_upload_history_with_error_file(upload_id, s3_key):
    """
    Persist error file location in upload_history.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE upload_history
                SET error_file_s3_key = %s
                WHERE upload_id = %s
                """,
                (s3_key, upload_id)
            )
            conn.commit()
        logger.info("Upload history updated with error file",
                    extra={"upload_id": upload_id})
    except Exception:
        logger.error(
            "Failed to update upload_history",
            extra={"upload_id": upload_id, "traceback": traceback.format_exc()}
        )


def check_upload_completion(upload_id):
    """
    Determine whether all records for an upload are processed.
    """
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM upload_history
                WHERE upload_id = %s
                """,
                (upload_id,)
            )
            info = cur.fetchone()

        if not info:
            return False, None

        processed = info["valid_records"] + info["error_records"]
        return processed == info["total_records"], dict(info)

    except Exception:
        logger.error(
            "Failed to check upload completion",
            extra={"upload_id": upload_id, "traceback": traceback.format_exc()}
        )
        return False, None


def trigger_sns_notification(upload_info, error_file_s3_key):
    """
    Notify vendor via SNS once upload processing is complete.
    """
    if not SNS_TOPIC_ARN:
        logger.warning("SNS_TOPIC_ARN not configured")
        return

    try:
        subject = f"Product Upload Complete - {upload_info['file_name']}"
        message = f"""
Upload ID: {upload_info['upload_id']}
Status: {upload_info['status']}
Valid Records: {upload_info['valid_records']}
Error Records: {upload_info['error_records']}
Error File: {error_file_s3_key}
"""
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
        logger.info("SNS notification sent",
                    extra={"upload_id": upload_info["upload_id"]})
    except Exception:
        logger.error(
            "Failed to send SNS notification",
            extra={"traceback": traceback.format_exc()}
        )

# =============================================================================
# CLOUDWATCH METRICS
# =============================================================================

def publish_metrics(upload_id, error_count, duration):
    """
    Publish error processing metrics to CloudWatch.
    """
    try:
        cloudwatch.put_metric_data(
            Namespace="EcommerceProductOnboarding",
            MetricData=[
                {"MetricName": "ErrorsProcessed", "Value": error_count},
                {"MetricName": "ErrorProcessingTime", "Value": duration}
            ]
        )
    except Exception:
        logger.warning(
            "Failed to publish CloudWatch metrics",
            extra={"traceback": traceback.format_exc()}
        )

# =============================================================================
# MAIN LAMBDA HANDLER
# =============================================================================

def lambda_handler(event, context):
    """
    Lambda entry point.

    Triggered by:
    - SQS messages from product-validation-errors queue
    """
    start_time = datetime.utcnow()
    logger.info("Error Processor Lambda started",
                extra={"request_id": context.aws_request_id})

    total = processed = 0

    try:
        errors = []
        for msg in event["Records"]:
            total += 1
            parsed = parse_sqs_message(msg)
            if parsed:
                errors.append(parsed)
                processed += 1

        grouped = group_errors_by_upload(errors)

        for upload_id, upload_errors in grouped.items():
            vendor_id = upload_errors[0]["vendor_id"]
            csv_content = create_error_csv(upload_errors)
            s3_key = upload_error_csv_to_s3(upload_id, vendor_id, csv_content)

            if s3_key:
                update_upload_history_with_error_file(upload_id, s3_key)

            complete, info = check_upload_completion(upload_id)
            if complete:
                trigger_sns_notification(info, s3_key)

            publish_metrics(
                upload_id,
                error_count=len(upload_errors),
                duration=(datetime.utcnow() - start_time).total_seconds()
            )

        logger.info(
            "Error processing completed",
            extra={
                "total_messages": total,
                "processed": processed,
                "unique_uploads": len(grouped)
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "total_messages": total,
                "processed": processed,
                "unique_uploads": len(grouped)
            })
        }

    except Exception as e:
        logger.critical(
            "Error Processor Lambda failed",
            extra={"error": str(e), "traceback": traceback.format_exc()}
        )
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "message": "Error processing failed"
            })
        }