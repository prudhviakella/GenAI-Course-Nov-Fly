"""
================================================================================
Lambda Function: CSV Parser (Container-based)
================================================================================

PURPOSE
-------
Ingest vendor-uploaded CSV files from S3 and persist each row as a
pending-validation record in DynamoDB.

ARCHITECTURE
------------
S3 (CSV Upload)
    → CSV Parser Lambda (this function)
        → RDS (vendor validation + upload audit)
        → DynamoDB (raw product records, status=pending_validation)
        → CloudWatch Metrics

DESIGN PRINCIPLES
-----------------
- Separation of concerns (ingestion ≠ validation)
- Schema firewall at CSV boundary
- Idempotent & auditable ingestion
- Strong observability (logs + metrics + tracebacks)
"""

# =============================================================================
# 1️⃣ STANDARD LIBRARIES
# =============================================================================

import json
import csv
import os
import io
import logging
import traceback
from datetime import datetime
from decimal import Decimal

# =============================================================================
# 2️⃣ AWS + THIRD-PARTY LIBRARIES
# =============================================================================

import boto3
from botocore.exceptions import ClientError
import psycopg2
from psycopg2.extras import RealDictCursor
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig

# =============================================================================
# 3️⃣ LOGGING CONFIGURATION
# =============================================================================

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)

# =============================================================================
# 4️⃣ ENVIRONMENT VARIABLES
# =============================================================================

DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "UploadRecords")
RDS_SECRET_NAME = os.environ.get("RDS_SECRET_NAME", "ecommerce/rds/credentials")
REGION = os.environ.get("AWS_REGION", "us-east-1")

# =============================================================================
# 5️⃣ AWS CLIENTS (REUSED ACROSS INVOCATIONS)
# =============================================================================

s3_client = boto3.client("s3", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)
cloudwatch = boto3.client("cloudwatch", region_name=REGION)
secretsmanager = boto3.client("secretsmanager", region_name=REGION)

# =============================================================================
# 6️⃣ SECRETS MANAGER CACHE
# =============================================================================

# Secrets Manager calls are cached per Lambda container to:
# - reduce latency
# - reduce API cost
# - support secret rotation transparently
cache = SecretCache(
    config=SecretCacheConfig(),
    client=secretsmanager
)

# =============================================================================
# 7️⃣ RDS CONNECTION HELPERS
# =============================================================================

def get_rds_credentials():
    """
    Retrieve PostgreSQL credentials from AWS Secrets Manager.

    Returns
    -------
    dict
        {
            host,
            port,
            dbname,
            username,
            password
        }

    Raises
    ------
    ClientError
        If secret retrieval fails
    """
    try:
        secret_string = cache.get_secret_string(RDS_SECRET_NAME)
        secret = json.loads(secret_string)

        # Log safe metadata only (never log secrets)
        logger.info(
            "RDS credentials retrieved",
            extra={"db_host": secret.get("host"), "db_name": secret.get("dbname")}
        )
        return secret

    except ClientError as e:
        logger.error(
            "Failed to retrieve RDS credentials",
            extra={
                "secret_name": RDS_SECRET_NAME,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )
        raise


def get_db_connection():
    """
    Create a new PostgreSQL connection.

    Notes
    -----
    - Lambda execution time is short-lived
    - Connection pooling is intentionally avoided
    - RDS Proxy can be added later if needed

    Returns
    -------
    psycopg2.connection
        Active database connection
    """
    creds = get_rds_credentials()
    return psycopg2.connect(
        host=creds["host"],
        port=creds.get("port", 5432),
        database=creds["dbname"],
        user=creds["username"],
        password=creds["password"],
        connect_timeout=5
    )

# =============================================================================
# 8️⃣ DATA TYPE CONVERSION HELPERS
# =============================================================================

def convert_to_decimal(value):
    """
    Convert numeric input to Decimal (required by DynamoDB).

    Returns
    -------
    Decimal | None
    """
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def convert_to_int(value):
    """
    Convert numeric input to integer safely.

    Returns
    -------
    int | None
    """
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except Exception:
        return None

# =============================================================================
# 9️⃣ CSV NORMALIZATION (SCHEMA FIREWALL)
# =============================================================================

def parse_csv_row(row, row_number):
    """
    Normalize a single CSV row into structured product data.

    This function acts as a **schema firewall**:
    - Raw CSV data never leaks beyond this boundary
    - CSV format changes are isolated here

    Parameters
    ----------
    row : dict
        Raw CSV row from csv.DictReader
    row_number : int
        Line number in the CSV file

    Returns
    -------
    dict
        Normalized product payload
    """
    return {
        "vendor_product_id": row.get("vendor_product_id", ""),
        "product_name": row.get("product_name", ""),
        "category": row.get("category", ""),
        "subcategory": row.get("subcategory", ""),
        "description": row.get("description", ""),
        "sku": row.get("sku", ""),
        "brand": row.get("brand", ""),
        "price": convert_to_decimal(row.get("price")),
        "compare_at_price": convert_to_decimal(row.get("compare_at_price")),
        "stock_quantity": convert_to_int(row.get("stock_quantity")),
        "unit": row.get("unit", "piece"),
        "weight_kg": convert_to_decimal(row.get("weight_kg")),
        "dimensions_cm": row.get("dimensions_cm", ""),
        "image_url": row.get("image_url", "")
    }


def extract_vendor_id_from_filename(filename):
    """
    Extract vendor_id from the uploaded filename.

    Expected format:
    ----------------
    VENDOR001_YYYYMMDD_HHMMSS.csv

    Returns
    -------
    str | None
    """
    try:
        return filename.split("_")[0]
    except Exception:
        return None

# =============================================================================
# 🔟 BUSINESS RULES (RDS LOOKUPS)
# =============================================================================

def verify_vendor_exists(vendor_id):
    """
    Validate vendor existence and active status.

    Parameters
    ----------
    vendor_id : str

    Returns
    -------
    bool
        True if vendor exists and is active
    """
    conn = cursor = None
    try:
        logger.info("Verifying vendor", extra={"vendor_id": vendor_id})

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            "SELECT vendor_id, status FROM vendors WHERE vendor_id = %s",
            (vendor_id,)
        )
        vendor = cursor.fetchone()

        if not vendor:
            logger.warning("Vendor not found", extra={"vendor_id": vendor_id})
            return False

        if vendor["status"] != "active":
            logger.warning(
                "Vendor inactive",
                extra={"vendor_id": vendor_id, "status": vendor["status"]}
            )
            return False

        logger.info("Vendor verified", extra={"vendor_id": vendor_id})
        return True

    except Exception as e:
        logger.error(
            "Vendor verification failed",
            extra={
                "vendor_id": vendor_id,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# =============================================================================
# 1️⃣1️⃣ UPLOAD HISTORY (AUDIT TRAIL)
# =============================================================================

def create_upload_history_record(upload_id, vendor_id, file_name, s3_key):
    """
    Create an audit record for the current upload.

    This enables:
    - Retry tracking
    - Reconciliation
    - Operational dashboards
    """
    conn = cursor = None
    try:
        logger.info(
            "Creating upload history",
            extra={"upload_id": upload_id, "vendor_id": vendor_id}
        )

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO upload_history (
                upload_id, vendor_id, file_name, s3_key,
                status, upload_timestamp, processing_started_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (upload_id) DO NOTHING
        """, (
            upload_id,
            vendor_id,
            file_name,
            s3_key,
            "processing",
            datetime.utcnow(),
            datetime.utcnow()
        ))

        conn.commit()

    except Exception as e:
        logger.error(
            "Failed to create upload history",
            extra={
                "upload_id": upload_id,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def update_upload_history_counts(upload_id, total_records):
    """
    Update total record count after CSV parsing.
    """
    conn = cursor = None
    try:
        logger.info(
            "Updating upload history counts",
            extra={"upload_id": upload_id, "total_records": total_records}
        )

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE upload_history
            SET total_records = %s
            WHERE upload_id = %s
        """, (total_records, upload_id))

        conn.commit()

    except Exception as e:
        logger.error(
            "Failed to update upload history",
            extra={
                "upload_id": upload_id,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# =============================================================================
# 1️⃣2️⃣ DYNAMODB INGESTION
# =============================================================================

def batch_insert_dynamodb_records(records):
    """
    Insert records into DynamoDB in batches of 25.

    DynamoDB batch_writer handles retries automatically.
    """
    table = dynamodb.Table(DYNAMODB_TABLE)
    successful = failed = 0

    logger.info("Starting DynamoDB batch insert", extra={"total": len(records)})

    for i in range(0, len(records), 25):
        with table.batch_writer() as writer:
            for record in records[i:i + 25]:
                try:
                    writer.put_item(Item=record)
                    successful += 1
                except Exception as e:
                    failed += 1
                    logger.error(
                        "DynamoDB insert failed",
                        extra={
                            "upload_id": record.get("upload_id"),
                            "record_id": record.get("record_id"),
                            "error": str(e),
                            "traceback": traceback.format_exc()
                        }
                    )

    return successful, failed

# =============================================================================
# 1️⃣3️⃣ CLOUDWATCH METRICS
# =============================================================================

def publish_metrics(upload_id, total, success, failed, duration):
    """
    Publish ingestion metrics to CloudWatch.
    """
    cloudwatch.put_metric_data(
        Namespace="EcommerceProductOnboarding",
        MetricData=[
            {"MetricName": "CSVRecordsProcessed", "Value": total},
            {"MetricName": "CSVRecordsSuccessful", "Value": success},
            {"MetricName": "CSVProcessingTime", "Value": duration}
        ]
    )

# =============================================================================
# 1️⃣4️⃣ LAMBDA HANDLER
# =============================================================================

def lambda_handler(event, context):
    """
    Lambda entry point.

    Triggered by:
    - S3 ObjectCreated events for CSV uploads
    """
    start_time = datetime.utcnow()

    logger.info(
        "CSV ingestion started",
        extra={"request_id": context.aws_request_id}
    )

    try:
        # Extract S3 event details
        s3_info = event["Records"][0]["s3"]
        bucket = s3_info["bucket"]["name"]
        key = s3_info["object"]["key"]
        filename = key.split("/")[-1]

        # Generate upload identifier
        timestamp = filename.replace(".csv", "").split("_", 1)[1]
        upload_id = f"UPLOAD_{timestamp}"

        # Resolve vendor
        vendor_id = extract_vendor_id_from_filename(filename)
        if not verify_vendor_exists(vendor_id):
            raise ValueError("Vendor validation failed")

        # Create audit record
        create_upload_history_record(upload_id, vendor_id, filename, key)

        # Download CSV content
        csv_content = s3_client.get_object(
            Bucket=bucket,
            Key=key
        )["Body"].read().decode("utf-8")

        # Parse CSV rows
        reader = csv.DictReader(io.StringIO(csv_content))
        records = []

        for i, row in enumerate(reader, 1):
            records.append({
                "upload_id": upload_id,
                "record_id": f"REC_{i:05d}",
                "vendor_id": vendor_id,
                "row_number": i,
                "product_data": parse_csv_row(row, i),
                "status": "pending_validation",
                "error_reason": None,
                "error_details": None,
                "processed_at": None,
                "created_at": datetime.utcnow().isoformat()
            })

        # Persist to DynamoDB
        success, failed = batch_insert_dynamodb_records(records)

        # Update audit counts
        update_upload_history_counts(upload_id, len(records))

        # Publish metrics
        duration = (datetime.utcnow() - start_time).total_seconds()
        publish_metrics(upload_id, len(records), success, failed, duration)

        logger.info(
            "CSV ingestion completed",
            extra={
                "upload_id": upload_id,
                "success": success,
                "failed": failed,
                "duration_sec": duration
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "upload_id": upload_id,
                "vendor_id": vendor_id,
                "total_records": len(records),
                "successful_records": success,
                "failed_records": failed,
                "processing_time_seconds": duration
            })
        }

    except Exception as e:
        logger.critical(
            "CSV ingestion failed",
            extra={
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "message": "CSV parsing failed"
            })
        }