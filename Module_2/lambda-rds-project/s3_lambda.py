import json, logging, boto3, csv
from io import StringIO
from datetime import datetime
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client = boto3.client('s3')


def lambda_handler(event, context):
    logger.info("Lambda execution started")
    try:
        # Get bucket and key from event
        if 'Records' in event:
            bucket = event['Records'][0]['s3']['bucket']['name']
            key = event['Records'][0]['s3']['object']['key']
        else:
            bucket, key = event['bucket'], event['key']

        # Download and process
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        content = obj['Body'].read().decode('utf-8')

        # Parse CSV
        reader = csv.DictReader(StringIO(content))
        customers = [row for row in reader if row.get('customer_id')]

        # Log results
        logger.info("=" * 80)
        for i, c in enumerate(customers, 1):
            logger.info(f"\n[Customer {i}]")
            logger.info(f"  ID: {c.get('customer_id')}")
            logger.info(f"  Name: {c.get('customer_name')}")
            logger.info(f"  Email: {c.get('email')}")
            logger.info(f"  City: {c.get('city')}, State: {c.get('state')}")
        logger.info(f"\nTotal: {len(customers)}")

        return {'statusCode': 200, 'body': json.dumps({'processed': len(customers)})}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}