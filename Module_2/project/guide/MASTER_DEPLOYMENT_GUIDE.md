# 🚀 Complete E-Commerce Product Onboarding System - Master Deployment Guide

## 📋 Overview

This guide provides **complete step-by-step instructions** to deploy the entire product onboarding system from scratch.

**What You're Building:**
```
Vendor → CSV Upload → S3 → Lambda → DynamoDB → Lambda → RDS/SQS → Lambda → S3/SNS → Email
```

**Time to Deploy:** 2-3 hours (first time) | 30 minutes (with automation)

**AWS Services Used:**
- S3 (file storage)
- Lambda (3 functions)
- ECR (container registry)
- DynamoDB (upload records + streams)
- RDS PostgreSQL (product catalog)
- SQS (error queue)
- SNS (email notifications)
- Secrets Manager (credentials)
- CloudWatch (logs + metrics)
- IAM (permissions)
- VPC (networking)

---

## 🎯 Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                     PRODUCT ONBOARDING PIPELINE                              │
└──────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐
    │   VENDOR    │ Uploads CSV
    └──────┬──────┘
           │
           ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │  S3 BUCKET: ecommerce-product-uploads-{account-id}             │
    │  ├─ uploads/VEND001/VEND001_20241221_103045.csv                │
    │  └─ errors/VEND001/UPLOAD_20241221_103045_errors.csv           │
    └──────┬──────────────────────────────────────────────────────────┘
           │ S3 Event Notification
           ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │  LAMBDA 1: CSV Parser (Container - ECR)                         │
    │  ├─ Verifies vendor in RDS                                      │
    │  ├─ Parses CSV rows                                             │
    │  └─ Inserts to DynamoDB (status: pending_validation)            │
    └──────┬──────────────────────────────────────────────────────────┘
           │
           ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │  DYNAMODB TABLE: UploadRecords (with Streams enabled)           │
    │  ├─ PK: upload_id, SK: record_id                                │
    │  ├─ Attributes: vendor_id, product_data, status                 │
    │  └─ Streams: NEW_IMAGE                                          │
    └──────┬──────────────────────────────────────────────────────────┘
           │ DynamoDB Streams
           ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │  LAMBDA 2: Product Validator (Container - ECR)                  │
    │  ├─ Runs 7 validation rules                                     │
    │  ├─ VALID → RDS products table                                  │
    │  └─ INVALID → SQS error queue + RDS validation_errors           │
    └──────┬──────────────────────────────────────────────────────────┘
           │
           ├─────────────────────┬──────────────────────┐
           ↓                     ↓                      ↓
    ┌────────────┐      ┌───────────────┐      ┌──────────────┐
    │ RDS TABLES │      │ SQS QUEUE     │      │  DYNAMODB    │
    │            │      │               │      │              │
    │ products   │      │ product-      │      │ Status       │
    │ validation │      │ validation-   │      │ Updated      │
    │ _errors    │      │ errors        │      │              │
    │ upload_    │      │               │      │              │
    │ history    │      └───────┬───────┘      └──────────────┘
    └────────────┘              │
                                │ SQS Event
                                ↓
                    ┌───────────────────────────────────────────┐
                    │  LAMBDA 3: Error Processor (Container)    │
                    │  ├─ Groups errors by upload_id            │
                    │  ├─ Generates error CSV                   │
                    │  ├─ Uploads to S3 errors/                 │
                    │  └─ Triggers SNS notification             │
                    └───────┬────────────────────────────────────┘
                            │
                            ↓
                    ┌───────────────┐
                    │  SNS TOPIC    │
                    │  product-     │
                    │  upload-      │
                    │  notifications│
                    └───────┬───────┘
                            │
                            ↓
                    ┌───────────────┐
                    │  EMAIL        │
                    │  Vendor       │
                    │  receives     │
                    │  notification │
                    └───────────────┘
```

---

## 📦 Prerequisites

### Required Tools

```bash
# AWS CLI
aws --version
# aws-cli/2.15.0 or higher

# Docker
docker --version
# Docker version 24.0.0 or higher

# PostgreSQL client (for RDS testing)
psql --version
# psql (PostgreSQL) 14.0 or higher

# Python (for local testing)
python3 --version
# Python 3.11 or higher
```

### Required AWS Resources

- AWS Account with admin access
- AWS CLI configured with credentials
- VPC with private subnets (for RDS)
- Domain for email notifications (optional)

### Set Environment Variables

```bash
# Set your AWS region
export AWS_REGION=us-east-1

# Get your AWS account ID
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Set common names
export PROJECT_NAME=ecommerce-product-onboarding
export S3_BUCKET_NAME="ecommerce-product-uploads-${ACCOUNT_ID}"

echo "Account ID: ${ACCOUNT_ID}"
echo "Region: ${AWS_REGION}"
echo "S3 Bucket: ${S3_BUCKET_NAME}"
```

---

## 🏗️ Deployment Steps

### Phase 1: Foundation Infrastructure (30 minutes)

#### Step 1.1: Create S3 Bucket

```bash
# Create S3 bucket for uploads and errors
aws s3api create-bucket \
    --bucket ${S3_BUCKET_NAME} \
    --region ${AWS_REGION}

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket ${S3_BUCKET_NAME} \
    --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
    --bucket ${S3_BUCKET_NAME} \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'

# Create folder structure
aws s3api put-object --bucket ${S3_BUCKET_NAME} --key uploads/
aws s3api put-object --bucket ${S3_BUCKET_NAME} --key errors/

echo "✓ S3 bucket created: ${S3_BUCKET_NAME}"
```

#### Step 1.2: Create DynamoDB Table with Streams

```bash
# Create UploadRecords table
aws dynamodb create-table \
    --table-name UploadRecords \
    --attribute-definitions \
        AttributeName=upload_id,AttributeType=S \
        AttributeName=record_id,AttributeType=S \
        AttributeName=vendor_id,AttributeType=S \
    --key-schema \
        AttributeName=upload_id,KeyType=HASH \
        AttributeName=record_id,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --stream-specification StreamEnabled=true,StreamViewType=NEW_IMAGE \
    --global-secondary-indexes \
        "[{
            \"IndexName\": \"VendorIndex\",
            \"KeySchema\": [{\"AttributeName\":\"vendor_id\",\"KeyType\":\"HASH\"}],
            \"Projection\": {\"ProjectionType\":\"ALL\"}
        }]" \
    --tags Key=Project,Value=${PROJECT_NAME}

# Wait for table to be active
aws dynamodb wait table-exists --table-name UploadRecords

# Get stream ARN (save for later)
export DYNAMODB_STREAM_ARN=$(aws dynamodb describe-table \
    --table-name UploadRecords \
    --query 'Table.LatestStreamArn' \
    --output text)

echo "✓ DynamoDB table created with Streams"
echo "Stream ARN: ${DYNAMODB_STREAM_ARN}"
```

#### Step 1.3: Create RDS PostgreSQL Database

```bash
# Create DB subnet group (if not exists)
aws rds create-db-subnet-group \
    --db-subnet-group-name ecommerce-db-subnet-group \
    --db-subnet-group-description "Subnet group for ecommerce database" \
    --subnet-ids subnet-xxxxx subnet-yyyyy \
    --tags Key=Project,Value=${PROJECT_NAME}

# Create security group for RDS
export RDS_SG=$(aws ec2 create-security-group \
    --group-name ecommerce-rds-sg \
    --description "Security group for ecommerce RDS" \
    --vpc-id vpc-xxxxx \
    --query 'GroupId' \
    --output text)

# Allow PostgreSQL from Lambda security group
aws ec2 authorize-security-group-ingress \
    --group-id ${RDS_SG} \
    --protocol tcp \
    --port 5432 \
    --source-group ${LAMBDA_SG}

# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier ecommerce-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 14.10 \
    --master-username postgres \
    --master-user-password "YourSecurePassword123!" \
    --allocated-storage 20 \
    --db-subnet-group-name ecommerce-db-subnet-group \
    --vpc-security-group-ids ${RDS_SG} \
    --backup-retention-period 7 \
    --no-publicly-accessible \
    --tags Key=Project,Value=${PROJECT_NAME}

# Wait for RDS to be available (10-15 minutes)
echo "Waiting for RDS to be available... (this takes ~15 minutes)"
aws rds wait db-instance-available --db-instance-identifier ecommerce-db

# Get RDS endpoint
export RDS_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier ecommerce-db \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)

echo "✓ RDS database created"
echo "Endpoint: ${RDS_ENDPOINT}"
```

#### Step 1.4: Initialize RDS Schema

```bash
# Connect to RDS and run schema
psql -h ${RDS_ENDPOINT} \
     -U postgres \
     -d postgres \
     -c "CREATE DATABASE ecommerce_platform;"

# Run schema creation
psql -h ${RDS_ENDPOINT} \
     -U postgres \
     -d ecommerce_platform \
     -f database_schema.sql

echo "✓ RDS schema initialized"
```

#### Step 1.5: Create Secrets Manager Secret

```bash
# Create secret for RDS credentials
aws secretsmanager create-secret \
    --name ecommerce/rds/credentials \
    --secret-string "{
        \"username\": \"postgres\",
        \"password\": \"YourSecurePassword123!\",
        \"host\": \"${RDS_ENDPOINT}\",
        \"port\": 5432,
        \"dbname\": \"ecommerce_platform\"
    }" \
    --tags Key=Project,Value=${PROJECT_NAME}

# Get secret ARN
export SECRET_ARN=$(aws secretsmanager describe-secret \
    --secret-id ecommerce/rds/credentials \
    --query 'ARN' \
    --output text)

echo "✓ Secrets Manager secret created"
echo "Secret ARN: ${SECRET_ARN}"
```

#### Step 1.6: Create SQS Error Queue

```bash
# Create dead-letter queue
aws sqs create-queue \
    --queue-name product-validation-errors-dlq \
    --attributes VisibilityTimeout=300,MessageRetentionPeriod=1209600

export DLQ_ARN=$(aws sqs get-queue-attributes \
    --queue-url $(aws sqs get-queue-url --queue-name product-validation-errors-dlq --query 'QueueUrl' --output text) \
    --attribute-names QueueArn \
    --query 'Attributes.QueueArn' \
    --output text)

# Create main error queue with DLQ
aws sqs create-queue \
    --queue-name product-validation-errors \
    --attributes "{
        \"VisibilityTimeout\": \"300\",
        \"MessageRetentionPeriod\": \"345600\",
        \"RedrivePolicy\": \"{\\\"deadLetterTargetArn\\\":\\\"${DLQ_ARN}\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"
    }"

export SQS_QUEUE_URL=$(aws sqs get-queue-url \
    --queue-name product-validation-errors \
    --query 'QueueUrl' \
    --output text)

export SQS_QUEUE_ARN=$(aws sqs get-queue-attributes \
    --queue-url ${SQS_QUEUE_URL} \
    --attribute-names QueueArn \
    --query 'Attributes.QueueArn' \
    --output text)

echo "✓ SQS queues created"
echo "Queue URL: ${SQS_QUEUE_URL}"
```

#### Step 1.7: Create SNS Topic

```bash
# Create SNS topic
aws sns create-topic \
    --name product-upload-notifications \
    --tags Key=Project,Value=${PROJECT_NAME}

export SNS_TOPIC_ARN=$(aws sns list-topics \
    --query 'Topics[?contains(TopicArn, `product-upload-notifications`)].TopicArn' \
    --output text)

# Subscribe email addresses
aws sns subscribe \
    --topic-arn ${SNS_TOPIC_ARN} \
    --protocol email \
    --notification-endpoint your-email@example.com

echo "✓ SNS topic created"
echo "Topic ARN: ${SNS_TOPIC_ARN}"
echo "Check email and confirm subscription!"
```

---

### Phase 2: Lambda Functions Deployment (45 minutes)

#### Step 2.1: Create ECR Repositories

```bash
# CSV Parser repository
aws ecr create-repository \
    --repository-name csv-parser-lambda \
    --image-scanning-configuration scanOnPush=true \
    --tags Key=Project,Value=${PROJECT_NAME}

# Product Validator repository
aws ecr create-repository \
    --repository-name product-validator-lambda \
    --image-scanning-configuration scanOnPush=true \
    --tags Key=Project,Value=${PROJECT_NAME}

# Error Processor repository
aws ecr create-repository \
    --repository-name error-processor-lambda \
    --image-scanning-configuration scanOnPush=true \
    --tags Key=Project,Value=${PROJECT_NAME}

# Get repository URIs
export ECR_CSV_PARSER="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/csv-parser-lambda"
export ECR_VALIDATOR="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/product-validator-lambda"
export ECR_ERROR_PROCESSOR="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/error-processor-lambda"

echo "✓ ECR repositories created"
```

#### Step 2.2: Build and Push Docker Images

```bash
# Authenticate to ECR
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin \
    ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Build and push CSV Parser
cd lambda_csv_parser/
docker build -t csv-parser-lambda:latest .
docker tag csv-parser-lambda:latest ${ECR_CSV_PARSER}:latest
docker push ${ECR_CSV_PARSER}:latest
cd ..

# Build and push Product Validator
cd lambda_product_validator/
docker build -t product-validator-lambda:latest .
docker tag product-validator-lambda:latest ${ECR_VALIDATOR}:latest
docker push ${ECR_VALIDATOR}:latest
cd ..

# Build and push Error Processor
cd lambda_error_processor/
docker build -t error-processor-lambda:latest .
docker tag error-processor-lambda:latest ${ECR_ERROR_PROCESSOR}:latest
docker push ${ECR_ERROR_PROCESSOR}:latest
cd ..

echo "✓ All Docker images pushed to ECR"
```

#### Step 2.3: Create IAM Roles

```bash
# Create CSV Parser role
aws iam create-role \
    --role-name lambda-csv-parser-role \
    --assume-role-policy-document file://trust-policy-lambda.json

aws iam attach-role-policy \
    --role-name lambda-csv-parser-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole

aws iam put-role-policy \
    --role-name lambda-csv-parser-role \
    --policy-name csv-parser-policy \
    --policy-document file://lambda-csv-parser-policy.json

# Create Product Validator role
aws iam create-role \
    --role-name lambda-product-validator-role \
    --assume-role-policy-document file://trust-policy-lambda.json

aws iam attach-role-policy \
    --role-name lambda-product-validator-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole

aws iam put-role-policy \
    --role-name lambda-product-validator-role \
    --policy-name product-validator-policy \
    --policy-document file://lambda-product-validator-policy.json

# Create Error Processor role
aws iam create-role \
    --role-name lambda-error-processor-role \
    --assume-role-policy-document file://trust-policy-lambda.json

aws iam attach-role-policy \
    --role-name lambda-error-processor-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole

aws iam put-role-policy \
    --role-name lambda-error-processor-role \
    --policy-name error-processor-policy \
    --policy-document file://lambda-error-processor-policy.json

# Get role ARNs
export CSV_PARSER_ROLE_ARN=$(aws iam get-role --role-name lambda-csv-parser-role --query 'Role.Arn' --output text)
export VALIDATOR_ROLE_ARN=$(aws iam get-role --role-name lambda-product-validator-role --query 'Role.Arn' --output text)
export ERROR_PROCESSOR_ROLE_ARN=$(aws iam get-role --role-name lambda-error-processor-role --query 'Role.Arn' --output text)

# Wait for roles to propagate
sleep 10

echo "✓ IAM roles created"
```

#### Step 2.4: Create Lambda Functions

```bash
# Create CSV Parser Lambda
aws lambda create-function \
    --function-name csv-parser \
    --package-type Image \
    --code ImageUri=${ECR_CSV_PARSER}:latest \
    --role ${CSV_PARSER_ROLE_ARN} \
    --timeout 300 \
    --memory-size 512 \
    --environment Variables="{
        DYNAMODB_TABLE=UploadRecords,
        RDS_SECRET_NAME=ecommerce/rds/credentials,
        AWS_REGION=${AWS_REGION}
    }" \
    --tags Key=Project,Value=${PROJECT_NAME}

# Create Product Validator Lambda
aws lambda create-function \
    --function-name product-validator \
    --package-type Image \
    --code ImageUri=${ECR_VALIDATOR}:latest \
    --role ${VALIDATOR_ROLE_ARN} \
    --timeout 300 \
    --memory-size 512 \
    --environment Variables="{
        DYNAMODB_TABLE=UploadRecords,
        RDS_SECRET_NAME=ecommerce/rds/credentials,
        SQS_ERROR_QUEUE_URL=${SQS_QUEUE_URL},
        AWS_REGION=${AWS_REGION}
    }" \
    --tags Key=Project,Value=${PROJECT_NAME}

# Create Error Processor Lambda
aws lambda create-function \
    --function-name error-processor \
    --package-type Image \
    --code ImageUri=${ECR_ERROR_PROCESSOR}:latest \
    --role ${ERROR_PROCESSOR_ROLE_ARN} \
    --timeout 300 \
    --memory-size 256 \
    --environment Variables="{
        RDS_SECRET_NAME=ecommerce/rds/credentials,
        S3_BUCKET_NAME=${S3_BUCKET_NAME},
        SNS_TOPIC_ARN=${SNS_TOPIC_ARN},
        AWS_REGION=${AWS_REGION}
    }" \
    --tags Key=Project,Value=${PROJECT_NAME}

echo "✓ Lambda functions created"
```

#### Step 2.5: Configure VPC for Lambda Functions

```bash
# Get VPC details from RDS
export RDS_VPC=$(aws rds describe-db-instances \
    --db-instance-identifier ecommerce-db \
    --query 'DBInstances[0].DBSubnetGroup.VpcId' \
    --output text)

export SUBNET_IDS=$(aws rds describe-db-instances \
    --db-instance-identifier ecommerce-db \
    --query 'DBInstances[0].DBSubnetGroup.Subnets[*].SubnetIdentifier' \
    --output text | tr '\t' ',')

# Update Lambda VPC configurations
for FUNCTION in csv-parser product-validator error-processor; do
    aws lambda update-function-configuration \
        --function-name ${FUNCTION} \
        --vpc-config SubnetIds=${SUBNET_IDS},SecurityGroupIds=${RDS_SG}
    
    echo "✓ VPC configured for ${FUNCTION}"
    sleep 5
done

echo "✓ All Lambda functions configured for VPC"
```

---

### Phase 3: Event Integrations (15 minutes)

#### Step 3.1: Configure S3 Event Notification

```bash
# Add Lambda permission for S3
aws lambda add-permission \
    --function-name csv-parser \
    --statement-id s3-trigger \
    --action lambda:InvokeFunction \
    --principal s3.amazonaws.com \
    --source-arn arn:aws:s3:::${S3_BUCKET_NAME}

# Configure S3 notification
aws s3api put-bucket-notification-configuration \
    --bucket ${S3_BUCKET_NAME} \
    --notification-configuration "{
        \"LambdaFunctionConfigurations\": [{
            \"Id\": \"csv-upload-trigger\",
            \"LambdaFunctionArn\": \"$(aws lambda get-function --function-name csv-parser --query 'Configuration.FunctionArn' --output text)\",
            \"Events\": [\"s3:ObjectCreated:*\"],
            \"Filter\": {
                \"Key\": {
                    \"FilterRules\": [{
                        \"Name\": \"prefix\",
                        \"Value\": \"uploads/\"
                    }, {
                        \"Name\": \"suffix\",
                        \"Value\": \".csv\"
                    }]
                }
            }
        }]
    }"

echo "✓ S3 event notification configured"
```

#### Step 3.2: Configure DynamoDB Streams Trigger

```bash
# Create event source mapping for Validator Lambda
aws lambda create-event-source-mapping \
    --function-name product-validator \
    --event-source-arn ${DYNAMODB_STREAM_ARN} \
    --starting-position LATEST \
    --batch-size 100 \
    --maximum-batching-window-in-seconds 0

echo "✓ DynamoDB Streams trigger configured"
```

#### Step 3.3: Configure SQS Trigger

```bash
# Create event source mapping for Error Processor Lambda
aws lambda create-event-source-mapping \
    --function-name error-processor \
    --event-source-arn ${SQS_QUEUE_ARN} \
    --batch-size 10 \
    --maximum-batching-window-in-seconds 30

echo "✓ SQS trigger configured"
```

---

### Phase 4: Testing & Validation (15 minutes)

#### Step 4.1: Upload Test Data

```bash
# Upload test CSV
aws s3 cp test-data/VEND001_test.csv \
    s3://${S3_BUCKET_NAME}/uploads/VEND001/

echo "✓ Test CSV uploaded"
echo "Monitoring logs... (wait 60 seconds)"
sleep 60
```

#### Step 4.2: Monitor Execution

```bash
# Watch CSV Parser logs
echo "=== CSV Parser Logs ==="
aws logs tail /aws/lambda/csv-parser --since 5m

# Watch Validator logs
echo "=== Validator Logs ==="
aws logs tail /aws/lambda/product-validator --since 5m

# Watch Error Processor logs
echo "=== Error Processor Logs ==="
aws logs tail /aws/lambda/error-processor --since 5m
```

#### Step 4.3: Verify Results

```bash
# Check DynamoDB records
aws dynamodb scan \
    --table-name UploadRecords \
    --limit 5

# Check S3 for error files
aws s3 ls s3://${S3_BUCKET_NAME}/errors/ --recursive

# Check SQS queue depth
aws sqs get-queue-attributes \
    --queue-url ${SQS_QUEUE_URL} \
    --attribute-names ApproximateNumberOfMessages

# Query RDS
psql -h ${RDS_ENDPOINT} -U postgres -d ecommerce_platform -c "
SELECT 
  upload_id,
  total_records,
  valid_records,
  error_records,
  status
FROM upload_history
ORDER BY upload_timestamp DESC
LIMIT 5;
"
```

---

## 📊 Deployment Verification Checklist

- [ ] S3 bucket created and accessible
- [ ] DynamoDB table created with Streams enabled
- [ ] RDS instance created and schema initialized
- [ ] Secrets Manager secret created
- [ ] SQS queues created (main + DLQ)
- [ ] SNS topic created and subscription confirmed
- [ ] ECR repositories created
- [ ] Docker images built and pushed
- [ ] IAM roles created with correct policies
- [ ] Lambda functions created from ECR images
- [ ] Lambda VPC configuration completed
- [ ] S3 event notification configured
- [ ] DynamoDB Streams trigger configured
- [ ] SQS trigger configured
- [ ] Test upload successful
- [ ] All Lambda functions executed
- [ ] Products inserted to RDS
- [ ] Errors captured in SQS
- [ ] Error CSV generated
- [ ] Email notification received

---

## 🧹 Cleanup (if needed)

**Warning:** This will delete all resources!

```bash
# Delete Lambda functions
for FUNCTION in csv-parser product-validator error-processor; do
    aws lambda delete-function --function-name ${FUNCTION}
done

# Delete ECR repositories
for REPO in csv-parser-lambda product-validator-lambda error-processor-lambda; do
    aws ecr delete-repository --repository-name ${REPO} --force
done

# Delete IAM roles
for ROLE in lambda-csv-parser-role lambda-product-validator-role lambda-error-processor-role; do
    # Detach policies first
    aws iam delete-role-policy --role-name ${ROLE} --policy-name ${ROLE%-role}-policy
    aws iam detach-role-policy --role-name ${ROLE} --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole
    aws iam delete-role --role-name ${ROLE}
done

# Delete SNS topic
aws sns delete-topic --topic-arn ${SNS_TOPIC_ARN}

# Delete SQS queues
aws sqs delete-queue --queue-url ${SQS_QUEUE_URL}
aws sqs delete-queue --queue-url $(aws sqs get-queue-url --queue-name product-validation-errors-dlq --query 'QueueUrl' --output text)

# Delete Secrets Manager secret
aws secretsmanager delete-secret --secret-id ecommerce/rds/credentials --force-delete-without-recovery

# Delete RDS instance
aws rds delete-db-instance \
    --db-instance-identifier ecommerce-db \
    --skip-final-snapshot

# Delete DynamoDB table
aws dynamodb delete-table --table-name UploadRecords

# Empty and delete S3 bucket
aws s3 rm s3://${S3_BUCKET_NAME} --recursive
aws s3api delete-bucket --bucket ${S3_BUCKET_NAME}

echo "✓ All resources deleted"
```

---

## 📚 Additional Resources

- [ECR Lambda Deployment Guide](./ECR_LAMBDA_DEPLOYMENT.md)
- [DynamoDB Streams Validator Guide](./DYNAMODB_STREAMS_VALIDATOR_GUIDE.md)
- [SQS Error Processor Guide](./SQS_ERROR_PROCESSOR_GUIDE.md)
- [Database Setup README](./DATABASE_SETUP_README.md)

---

## 🆘 Common Issues & Solutions

See [Troubleshooting Guide](./TROUBLESHOOTING.md) for detailed solutions.

---

## ✅ Success!

If all checklist items are complete, you now have a **fully functional, production-ready product onboarding system**!

**What you built:**
- ✅ Automated CSV processing pipeline
- ✅ Multi-stage data validation
- ✅ Error tracking and reporting
- ✅ Email notifications
- ✅ Complete audit trail
- ✅ Scalable, serverless architecture

**Next steps:**
- Monitor CloudWatch metrics
- Set up alarms for error rates
- Create vendor onboarding documentation
- Build API for programmatic uploads
- Add data quality dashboards
