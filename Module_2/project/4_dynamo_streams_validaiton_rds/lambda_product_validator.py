"""
Lambda Function: Product Validator (Container-based)
====================================================

PURPOSE
-------
Validates product records ingested into DynamoDB via vendor CSV uploads.

FLOW
----
DynamoDB Stream (INSERT)
    → Validate product fields
    → If valid:
         - Mark record as validated in DynamoDB
         - (Optionally) Insert into RDS products table
    → If invalid:
         - Mark record as error in DynamoDB
         - Persist error in RDS
         - Send error payload to SQS

DESIGN PRINCIPLES
-----------------
- Separation of ingestion vs validation
- Idempotent processing
- Explicit error handling & traceability
- Production-grade logging with stack traces
"""

# =============================================================================
# STANDARD LIBRARIES
# =============================================================================

import json
import os
import logging
import traceback
from datetime import datetime
from decimal import Decimal

# =============================================================================
# AWS & THIRD-PARTY LIBRARIES
# =============================================================================

import boto3
from botocore.exceptions import ClientError
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

DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "UploadRecords")
RDS_SECRET_NAME = os.environ.get("RDS_SECRET_NAME", "ecommerce/rds/credentials")
SQS_ERROR_QUEUE_URL = os.environ.get("SQS_ERROR_QUEUE_URL")
REGION = os.environ.get("AWS_REGION", "us-east-1")

# =============================================================================
# AWS CLIENTS (REUSED ACROSS INVOCATIONS)
# =============================================================================

dynamodb = boto3.resource("dynamodb", region_name=REGION)
sqs_client = boto3.client("sqs", region_name=REGION)
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
# DATABASE CONNECTION (GLOBAL FOR REUSE)
# =============================================================================

db_connection = None

# =============================================================================
# VALIDATION RULE DEFINITIONS
# =============================================================================

VALIDATION_RULES = {
    "required_fields": [
        "vendor_product_id",
        "product_name",
        "category",
        "sku",
        "price",
        "stock_quantity"
    ],
    "price": {"min": Decimal("0.01"), "max": Decimal("999999.99")},
    "stock": {"min": 0, "max": 1_000_000},
    "field_lengths": {
        "product_name": 200,
        "description": 2000,
        "sku": 100,
        "brand": 100,
        "vendor_product_id": 100
    }
}

# =============================================================================
# SECRETS & DATABASE HELPERS
# =============================================================================

def get_rds_credentials():
    """
    Retrieve RDS credentials from AWS Secrets Manager.

    Uses caching to avoid repeated Secrets Manager API calls.

    Returns
    -------
    dict
        Dictionary containing host, port, dbname, username, password

    Raises
    ------
    Exception
        If secret retrieval fails
    """
    try:
        secret_string = cache.get_secret_string(RDS_SECRET_NAME)
        return json.loads(secret_string)
    except Exception as e:
        logger.error(
            "Failed to retrieve RDS credentials",
            extra={"error": str(e), "traceback": traceback.format_exc()}
        )
        raise


def get_db_connection():
    """
    Get an active PostgreSQL connection.

    Reuses an existing connection if still alive.
    Recreates connection if stale or closed.

    Returns
    -------
    psycopg2.connection
        Active database connection
    """
    global db_connection

    # Attempt to reuse existing connection
    try:
        if db_connection and not db_connection.closed:
            with db_connection.cursor() as cur:
                cur.execute("SELECT 1")
            return db_connection
    except Exception:
        # Connection is unhealthy → recreate
        db_connection = None

    # Create a new database connection
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
# VALIDATION FUNCTIONS
# =============================================================================

def validate_required_fields(product_data):
    """
    Ensure mandatory fields are present and non-empty.

    Returns
    -------
    (bool, str | None)
        Validation result and error message
    """
    missing = [
        field for field in VALIDATION_RULES["required_fields"]
        if not product_data.get(field)
    ]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    return True, None


def validate_price(price):
    """
    Validate price value and bounds.
    """
    try:
        price = Decimal(str(price))
        if price < VALIDATION_RULES["price"]["min"]:
            return False, "Price below minimum allowed"
        if price > VALIDATION_RULES["price"]["max"]:
            return False, "Price exceeds maximum allowed"
        return True, None
    except Exception as e:
        return False, f"Invalid price format: {str(e)}"


def validate_stock_quantity(stock):
    """
    Validate stock quantity bounds.
    """
    try:
        stock = int(stock)
        if stock < VALIDATION_RULES["stock"]["min"]:
            return False, "Stock cannot be negative"
        if stock > VALIDATION_RULES["stock"]["max"]:
            return False, "Stock exceeds maximum allowed"
        return True, None
    except Exception as e:
        return False, f"Invalid stock format: {str(e)}"


def validate_field_lengths(product_data):
    """
    Validate string field lengths against configured limits.
    """
    errors = []
    for field, max_len in VALIDATION_RULES["field_lengths"].items():
        value = product_data.get(field)
        if value and len(str(value)) > max_len:
            errors.append(f"{field} exceeds {max_len} characters")

    if errors:
        return False, "; ".join(errors)
    return True, None


def validate_category(category):
    """
    Ensure category exists and is active in reference table.
    """
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT 1
                FROM product_categories
                WHERE category_name = %s
                  AND is_active = TRUE
                """,
                (category,)
            )
            return (True, None) if cur.fetchone() else (False, "Invalid category")
    except Exception:
        logger.error(
            "Category validation failed",
            extra={"category": category, "traceback": traceback.format_exc()}
        )
        return False, "Category validation error"


def validate_sku_uniqueness(sku):
    """
    Ensure SKU is globally unique across all vendors.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM products WHERE sku = %s", (sku,))
            return (False, "Duplicate SKU") if cur.fetchone() else (True, None)
    except Exception:
        logger.error(
            "SKU uniqueness validation failed",
            extra={"sku": sku, "traceback": traceback.format_exc()}
        )
        return False, "SKU uniqueness check failed"


def validate_vendor_product_id_uniqueness(vendor_product_id, vendor_id):
    """
    Ensure vendor_product_id is unique per vendor.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM products
                WHERE vendor_id = %s
                  AND vendor_product_id = %s
                """,
                (vendor_id, vendor_product_id)
            )
            return (False, "Duplicate vendor product ID") if cur.fetchone() else (True, None)
    except Exception:
        logger.error(
            "Vendor product ID uniqueness validation failed",
            extra={"vendor_id": vendor_id, "traceback": traceback.format_exc()}
        )
        return False, "Vendor product ID uniqueness check failed"


def validate_product(product_data, vendor_id):
    """
    Run all validation checks sequentially.

    Short-circuits on first failure.

    Returns
    -------
    (bool, str | None, str | None)
        is_valid, error_type, error_message
    """
    validations = [
        (validate_required_fields, "MISSING_REQUIRED_FIELDS"),
        (lambda d: validate_price(d.get("price")), "INVALID_PRICE"),
        (lambda d: validate_stock_quantity(d.get("stock_quantity")), "INVALID_STOCK"),
        (validate_field_lengths, "FIELD_LENGTH_EXCEEDED"),
        (lambda d: validate_category(d.get("category")), "INVALID_CATEGORY"),
        (lambda d: validate_sku_uniqueness(d.get("sku")), "DUPLICATE_SKU"),
        (lambda d: validate_vendor_product_id_uniqueness(
            d.get("vendor_product_id"), vendor_id
        ), "DUPLICATE_VENDOR_PRODUCT_ID"),
    ]

    for fn, error_type in validations:
        is_valid, error_message = fn(product_data)
        if not is_valid:
            return False, error_type, error_message

    return True, None, None

# =============================================================================
# DYNAMODB & SQS OPERATIONS
# =============================================================================

def update_dynamodb_record_status(upload_id, record_id, status,
                                  error_reason=None, error_details=None):
    """
    Update validation status of a record in DynamoDB.
    """
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)

        update_expr = "SET #s = :s, processed_at = :p"
        expr_vals = {
            ":s": status,
            ":p": datetime.utcnow().isoformat()
        }
        expr_names = {"#s": "status"}

        if error_reason:
            update_expr += ", error_reason = :r, error_details = :d"
            expr_vals.update({
                ":r": error_reason,
                ":d": error_details
            })

        table.update_item(
            Key={"upload_id": upload_id, "record_id": record_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_vals,
            ExpressionAttributeNames=expr_names
        )
    except Exception:
        logger.error(
            "Failed to update DynamoDB record",
            extra={
                "upload_id": upload_id,
                "record_id": record_id,
                "traceback": traceback.format_exc()
            }
        )


def send_error_to_sqs(message):
    """
    Send validation error payload to SQS for downstream handling.
    """
    try:
        sqs_client.send_message(
            QueueUrl=SQS_ERROR_QUEUE_URL,
            MessageBody=json.dumps(message, default=str)
        )
    except Exception:
        logger.error(
            "Failed to send error message to SQS",
            extra={"traceback": traceback.format_exc()}
        )

# =============================================================================
# MAIN LAMBDA HANDLER
# =============================================================================

def lambda_handler(event, context):
    """
    Lambda entry point.

    Triggered by DynamoDB Streams INSERT events.
    """
    start_time = datetime.utcnow()
    logger.info(
        "Product Validator Lambda started",
        extra={"request_id": context.aws_request_id}
    )

    total = valid = error = 0

    try:
        for record in event["Records"]:
            # Process only INSERT events
            if record["eventName"] != "INSERT":
                continue

            total += 1
            image = record["dynamodb"]["NewImage"]

            # Extract primary identifiers
            upload_id = image["upload_id"]["S"]
            record_id = image["record_id"]["S"]
            vendor_id = image["vendor_id"]["S"]
            row_number = int(image["row_number"]["N"])

            # Convert DynamoDB Map → Python dict
            product_data = {
                k: (
                    v.get("S") if "S" in v else
                    Decimal(v["N"]) if "N" in v else
                    None
                )
                for k, v in image["product_data"]["M"].items()
            }

            # Validate product
            is_valid, error_type, error_message = validate_product(product_data, vendor_id)

            if is_valid:
                valid += 1
                update_dynamodb_record_status(upload_id, record_id, "validated")
                logger.info(
                    "Product validated",
                    extra={"upload_id": upload_id, "record_id": record_id}
                )
            else:
                error += 1
                update_dynamodb_record_status(
                    upload_id, record_id, "error", error_type, error_message
                )
                send_error_to_sqs({
                    "upload_id": upload_id,
                    "vendor_id": vendor_id,
                    "record_id": record_id,
                    "row_number": row_number,
                    "error_type": error_type,
                    "error_message": error_message,
                    "product_data": product_data
                })
                logger.warning(
                    "Product validation failed",
                    extra={
                        "upload_id": upload_id,
                        "record_id": record_id,
                        "error_type": error_type,
                        "error_message": error_message
                    }
                )

        duration = (datetime.utcnow() - start_time).total_seconds()

        logger.info(
            "Validation completed",
            extra={
                "total": total,
                "valid": valid,
                "errors": error,
                "duration_sec": duration
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "total_records": total,
                "valid_records": valid,
                "error_records": error,
                "processing_time_seconds": duration
            })
        }

    except Exception as e:
        logger.critical(
            "Validator Lambda failed",
            extra={
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "message": "Validation failed"
            })
        }