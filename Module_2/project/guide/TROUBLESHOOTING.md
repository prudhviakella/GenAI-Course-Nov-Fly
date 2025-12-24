# 🔧 Product Onboarding System - Troubleshooting Playbook

## 📋 Quick Diagnostics

### Check Overall System Health

```bash
#!/bin/bash

echo "=== SYSTEM HEALTH CHECK ==="
echo ""

# S3 Bucket
echo "1. S3 Bucket:"
aws s3 ls s3://ecommerce-product-uploads-${ACCOUNT_ID}/ && echo "✓ OK" || echo "✗ FAIL"

# DynamoDB Table
echo "2. DynamoDB Table:"
aws dynamodb describe-table --table-name UploadRecords --query 'Table.TableStatus' && echo "✓ OK" || echo "✗ FAIL"

# Lambda Functions
echo "3. Lambda Functions:"
for FUNC in csv-parser product-validator error-processor; do
    STATUS=$(aws lambda get-function --function-name ${FUNC} --query 'Configuration.State' --output text 2>/dev/null)
    echo "   ${FUNC}: ${STATUS}"
done

# SQS Queue
echo "4. SQS Queue:"
aws sqs get-queue-attributes \
    --queue-url $(aws sqs get-queue-url --queue-name product-validation-errors --query 'QueueUrl' --output text) \
    --attribute-names ApproximateNumberOfMessages \
    --query 'Attributes.ApproximateNumberOfMessages' && echo "✓ OK" || echo "✗ FAIL"

# SNS Topic
echo "5. SNS Topic:"
aws sns list-topics | grep -q "product-upload-notifications" && echo "✓ OK" || echo "✗ FAIL"

# RDS Instance
echo "6. RDS Instance:"
aws rds describe-db-instances \
    --db-instance-identifier ecommerce-db \
    --query 'DBInstances[0].DBInstanceStatus' && echo "✓ OK" || echo "✗ FAIL"

echo ""
echo "=== END HEALTH CHECK ==="
```

---

## 🚨 Common Issues & Solutions

### Issue 1: CSV Parser Lambda Not Triggered

**Symptoms:**
- File uploaded to S3
- No Lambda execution in CloudWatch Logs
- No records in DynamoDB

**Diagnosis:**

```bash
# Check S3 event notification configuration
aws s3api get-bucket-notification-configuration \
    --bucket ecommerce-product-uploads-${ACCOUNT_ID}

# Check Lambda function exists
aws lambda get-function --function-name csv-parser

# Check Lambda permissions for S3
aws lambda get-policy --function-name csv-parser
```

**Common Causes:**

1. **S3 notification not configured**
   ```bash
   # Fix: Add notification
   aws lambda add-permission \
       --function-name csv-parser \
       --statement-id s3-trigger \
       --action lambda:InvokeFunction \
       --principal s3.amazonaws.com \
       --source-arn arn:aws:s3:::ecommerce-product-uploads-${ACCOUNT_ID}
   
   # Configure S3 event
   aws s3api put-bucket-notification-configuration \
       --bucket ecommerce-product-uploads-${ACCOUNT_ID} \
       --notification-configuration file://s3-notification-config.json
   ```

2. **Wrong S3 prefix/suffix**
   - File must be in `uploads/` prefix
   - File must have `.csv` extension
   - Fix: Upload to correct location

3. **Lambda in failed state**
   ```bash
   # Check Lambda state
   aws lambda get-function --function-name csv-parser --query 'Configuration.State'
   
   # If "Failed", check LastUpdateStatus
   aws lambda get-function --function-name csv-parser --query 'Configuration.LastUpdateStatus'
   ```

**Solution Steps:**

1. Verify S3 event configuration
2. Check Lambda permissions
3. Re-upload CSV to correct location
4. Monitor CloudWatch Logs

---

### Issue 2: Lambda "Task timed out after X seconds"

**Symptoms:**
- Lambda runs but times out
- CloudWatch Logs show partial execution
- Error: "Task timed out after 300.00 seconds"

**Diagnosis:**

```bash
# Check Lambda timeout setting
aws lambda get-function-configuration \
    --function-name csv-parser \
    --query 'Timeout'

# Check recent executions
aws logs tail /aws/lambda/csv-parser --since 30m
```

**Common Causes:**

1. **Timeout too short for large files**
2. **Database connection issues**
3. **Infinite loops in code**

**Solutions:**

```bash
# Increase timeout (max 15 minutes)
aws lambda update-function-configuration \
    --function-name csv-parser \
    --timeout 600

# Increase memory (often speeds up execution)
aws lambda update-function-configuration \
    --function-name csv-parser \
    --memory-size 1024
```

---

### Issue 3: "Unable to connect to RDS"

**Symptoms:**
- Error: `psycopg2.OperationalError: timeout expired`
- Error: `could not connect to server`
- Lambda logs show database connection failures

**Diagnosis:**

```bash
# Check Lambda VPC configuration
aws lambda get-function-configuration \
    --function-name csv-parser \
    --query 'VpcConfig'

# Check RDS security group
RDS_SG=$(aws rds describe-db-instances \
    --db-instance-identifier ecommerce-db \
    --query 'DBInstances[0].VpcSecurityGroups[0].VpcSecurityGroupId' \
    --output text)

aws ec2 describe-security-groups --group-ids ${RDS_SG}

# Check if RDS is accessible
RDS_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier ecommerce-db \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)

echo "RDS Endpoint: ${RDS_ENDPOINT}"
```

**Common Causes:**

1. **Lambda not in VPC**
   ```bash
   # Fix: Update Lambda VPC configuration
   aws lambda update-function-configuration \
       --function-name csv-parser \
       --vpc-config SubnetIds=subnet-xxx,subnet-yyy,SecurityGroupIds=sg-zzz
   ```

2. **Security group doesn't allow Lambda**
   ```bash
   # Get Lambda security group
   LAMBDA_SG=$(aws lambda get-function-configuration \
       --function-name csv-parser \
       --query 'VpcConfig.SecurityGroupIds[0]' \
       --output text)
   
   # Add inbound rule to RDS security group
   aws ec2 authorize-security-group-ingress \
       --group-id ${RDS_SG} \
       --protocol tcp \
       --port 5432 \
       --source-group ${LAMBDA_SG}
   ```

3. **Wrong Secrets Manager credentials**
   ```bash
   # Verify secret
   aws secretsmanager get-secret-value \
       --secret-id ecommerce/rds/credentials \
       --query 'SecretString' \
       --output text | jq .
   ```

4. **RDS in different VPC**
   - Lambda and RDS must be in same VPC
   - Check VPC IDs match

**Solution Checklist:**
- [ ] Lambda in same VPC as RDS
- [ ] Lambda in private subnets
- [ ] Security group allows Lambda → RDS (port 5432)
- [ ] NAT Gateway configured (if Lambda needs internet)
- [ ] Secrets Manager has correct RDS endpoint

---

### Issue 4: DynamoDB Streams Not Triggering Validator Lambda

**Symptoms:**
- Records inserted to DynamoDB
- Validator Lambda not invoked
- No validation errors or products

**Diagnosis:**

```bash
# Check event source mapping
aws lambda list-event-source-mappings \
    --function-name product-validator

# Check mapping state
MAPPING_UUID=$(aws lambda list-event-source-mappings \
    --function-name product-validator \
    --query 'EventSourceMappings[0].UUID' \
    --output text)

aws lambda get-event-source-mapping --uuid ${MAPPING_UUID}
```

**Common Causes:**

1. **Event source mapping disabled**
   ```bash
   # Enable mapping
   aws lambda update-event-source-mapping \
       --uuid ${MAPPING_UUID} \
       --enabled
   ```

2. **Wrong stream ARN**
   ```bash
   # Get correct stream ARN
   STREAM_ARN=$(aws dynamodb describe-table \
       --table-name UploadRecords \
       --query 'Table.LatestStreamArn' \
       --output text)
   
   # Recreate mapping
   aws lambda delete-event-source-mapping --uuid ${MAPPING_UUID}
   
   aws lambda create-event-source-mapping \
       --function-name product-validator \
       --event-source-arn ${STREAM_ARN} \
       --starting-position LATEST \
       --batch-size 100
   ```

3. **IAM permissions missing**
   ```bash
   # Lambda role needs dynamodb:GetRecords, GetShardIterator
   # Check role policies
   aws iam get-role-policy \
       --role-name lambda-product-validator-role \
       --policy-name product-validator-policy
   ```

4. **StartingPosition set to TRIM_HORIZON but stream empty**
   - Set to LATEST and insert new test record

---

### Issue 5: SQS Messages Not Processed

**Symptoms:**
- Messages in SQS queue
- Error Processor Lambda not invoked
- Messages going to DLQ

**Diagnosis:**

```bash
# Check queue depth
aws sqs get-queue-attributes \
    --queue-url $(aws sqs get-queue-url --queue-name product-validation-errors --query 'QueueUrl' --output text) \
    --attribute-names ApproximateNumberOfMessages,ApproximateNumberOfMessagesNotVisible

# Check DLQ
aws sqs get-queue-attributes \
    --queue-url $(aws sqs get-queue-url --queue-name product-validation-errors-dlq --query 'QueueUrl' --output text) \
    --attribute-names ApproximateNumberOfMessages

# Check event source mapping
aws lambda list-event-source-mappings \
    --function-name error-processor
```

**Common Causes:**

1. **Visibility timeout too short**
   ```bash
   # Increase visibility timeout
   aws sqs set-queue-attributes \
       --queue-url $(aws sqs get-queue-url --queue-name product-validation-errors --query 'QueueUrl' --output text) \
       --attributes VisibilityTimeout=600
   ```

2. **Lambda failing repeatedly**
   ```bash
   # Check Lambda logs
   aws logs tail /aws/lambda/error-processor --since 1h --filter-pattern "ERROR"
   
   # Fix Lambda code issue, then purge DLQ
   aws sqs purge-queue \
       --queue-url $(aws sqs get-queue-url --queue-name product-validation-errors-dlq --query 'QueueUrl' --output text)
   ```

3. **Event source mapping disabled**
   ```bash
   MAPPING_UUID=$(aws lambda list-event-source-mappings \
       --function-name error-processor \
       --query 'EventSourceMappings[0].UUID' \
       --output text)
   
   aws lambda update-event-source-mapping \
       --uuid ${MAPPING_UUID} \
       --enabled
   ```

**Manual Processing:**

```bash
# Manually receive and process message
aws sqs receive-message \
    --queue-url $(aws sqs get-queue-url --queue-name product-validation-errors --query 'QueueUrl' --output text) \
    --max-number-of-messages 1

# Invoke Lambda manually with message
aws lambda invoke \
    --function-name error-processor \
    --payload file://test-sqs-event.json \
    response.json
```

---

### Issue 6: Email Notifications Not Received

**Symptoms:**
- Error Processor completes successfully
- Vendor doesn't receive email
- SNS shows message sent

**Diagnosis:**

```bash
# Check SNS subscriptions
aws sns list-subscriptions-by-topic \
    --topic-arn ${SNS_TOPIC_ARN}

# Check for "PendingConfirmation"
aws sns list-subscriptions-by-topic \
    --topic-arn ${SNS_TOPIC_ARN} \
    --query 'Subscriptions[?SubscriptionArn==`PendingConfirmation`]'
```

**Common Causes:**

1. **Subscription not confirmed**
   - Check spam folder for confirmation email
   - Click "Confirm subscription" link
   - Resend confirmation:
     ```bash
     # Unsubscribe old
     aws sns unsubscribe --subscription-arn ${OLD_SUB_ARN}
     
     # Subscribe again
     aws sns subscribe \
         --topic-arn ${SNS_TOPIC_ARN} \
         --protocol email \
         --notification-endpoint vendor@example.com
     ```

2. **Email in spam folder**
   - Check spam/junk folder
   - Add noreply@sns.amazonaws.com to contacts

3. **SNS topic ARN incorrect in Lambda**
   ```bash
   # Check Lambda environment variable
   aws lambda get-function-configuration \
       --function-name error-processor \
       --query 'Environment.Variables.SNS_TOPIC_ARN'
   ```

4. **IAM permissions missing**
   ```bash
   # Lambda role needs sns:Publish
   aws iam get-role-policy \
       --role-name lambda-error-processor-role \
       --policy-name error-processor-policy | grep sns:Publish
   ```

---

### Issue 7: Error CSV Not Created in S3

**Symptoms:**
- Error Processor runs successfully
- No CSV file in S3 errors/ folder
- Upload history not updated

**Diagnosis:**

```bash
# Check S3 bucket
aws s3 ls s3://ecommerce-product-uploads-${ACCOUNT_ID}/errors/ --recursive

# Check Lambda logs
aws logs tail /aws/lambda/error-processor --since 30m | grep -i "s3\|csv"

# Check S3 permissions
aws iam get-role-policy \
    --role-name lambda-error-processor-role \
    --policy-name error-processor-policy | grep s3:PutObject
```

**Common Causes:**

1. **Wrong S3 bucket name**
   ```bash
   # Check Lambda environment variable
   aws lambda get-function-configuration \
       --function-name error-processor \
       --query 'Environment.Variables.S3_BUCKET_NAME'
   ```

2. **IAM permissions missing**
   ```bash
   # Add S3 put permission
   # Edit IAM policy to include:
   # {
   #   "Effect": "Allow",
   #   "Action": "s3:PutObject",
   #   "Resource": "arn:aws:s3:::ecommerce-product-uploads-*/errors/*"
   # }
   ```

3. **Lambda timeout before S3 upload**
   ```bash
   # Increase timeout
   aws lambda update-function-configuration \
       --function-name error-processor \
       --timeout 300
   ```

---

### Issue 8: High Lambda Costs

**Symptoms:**
- Unexpected AWS bill
- High Lambda invocation count
- High Lambda duration charges

**Diagnosis:**

```bash
# Check invocations (last 7 days)
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value=csv-parser \
    --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 86400 \
    --statistics Sum

# Check duration
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Duration \
    --dimensions Name=FunctionName,Value=csv-parser \
    --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 86400 \
    --statistics Average
```

**Common Causes:**

1. **Infinite loop / Recursive invocations**
   - CSV Parser creates file → triggers itself
   - Fix: Use different S3 prefixes (uploads/ vs processed/)

2. **Memory over-provisioned**
   ```bash
   # Check actual memory usage
   aws logs filter-log-events \
       --log-group-name /aws/lambda/csv-parser \
       --filter-pattern "Max Memory Used" \
       --max-items 10
   
   # Reduce if needed
   aws lambda update-function-configuration \
       --function-name csv-parser \
       --memory-size 256
   ```

3. **Unnecessary retries**
   - Check error rates
   - Fix underlying errors

**Cost Optimization:**

```bash
# Set reserved concurrency to limit parallel executions
aws lambda put-function-concurrency \
    --function-name csv-parser \
    --reserved-concurrent-executions 5

# Enable Lambda Insights for monitoring
aws lambda update-function-configuration \
    --function-name csv-parser \
    --layers arn:aws:lambda:us-east-1:580247275435:layer:LambdaInsightsExtension:14
```

---

## 🔍 Debugging Techniques

### Enable Detailed Logging

```python
# Add to Lambda function
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Log everything
logger.debug(f"Event: {json.dumps(event)}")
logger.debug(f"Product data: {product_data}")
logger.debug(f"Validation result: {is_valid}")
```

### Test Lambda Locally

```bash
# Create test event
cat > test-event.json << EOF
{
  "Records": [{
    "s3": {
      "bucket": {"name": "test-bucket"},
      "object": {"key": "uploads/VEND001/test.csv"}
    }
  }]
}
EOF

# Invoke Lambda
aws lambda invoke \
    --function-name csv-parser \
    --payload file://test-event.json \
    --log-type Tail \
    response.json

# View response
cat response.json | jq .
```

### Query CloudWatch Logs Insights

```sql
-- Find errors in last hour
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 20

-- Find slow executions
fields @timestamp, @duration
| filter @type = "REPORT"
| stats avg(@duration), max(@duration), min(@duration)

-- Find specific upload
fields @timestamp, @message
| filter @message like /UPLOAD_20241221_103045/
| sort @timestamp asc
```

---

## 📊 Monitoring Dashboard

Create CloudWatch Dashboard:

```bash
aws cloudwatch put-dashboard \
    --dashboard-name ProductOnboardingPipeline \
    --dashboard-body file://dashboard-config.json
```

**dashboard-config.json:**
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Invocations", {"stat": "Sum", "label": "CSV Parser"}],
          ["...", {"stat": "Sum", "label": "Validator"}],
          ["...", {"stat": "Sum", "label": "Error Processor"}]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "Lambda Invocations"
      }
    }
  ]
}
```

---

## ✅ Health Check Script

Save as `health-check.sh`:

```bash
#!/bin/bash

ERRORS=0

check() {
    if [ $? -eq 0 ]; then
        echo "✓ $1"
    else
        echo "✗ $1"
        ((ERRORS++))
    fi
}

echo "Running health check..."

# Check each component
aws s3 ls s3://${S3_BUCKET_NAME}/ > /dev/null 2>&1
check "S3 Bucket"

aws dynamodb describe-table --table-name UploadRecords > /dev/null 2>&1
check "DynamoDB Table"

aws lambda get-function --function-name csv-parser > /dev/null 2>&1
check "CSV Parser Lambda"

aws lambda get-function --function-name product-validator > /dev/null 2>&1
check "Validator Lambda"

aws lambda get-function --function-name error-processor > /dev/null 2>&1
check "Error Processor Lambda"

if [ $ERRORS -eq 0 ]; then
    echo "All systems operational!"
    exit 0
else
    echo "$ERRORS issues found"
    exit 1
fi
```

---

## 📞 Getting Help

If issues persist:

1. **Check AWS Service Health**: https://status.aws.amazon.com/
2. **Review CloudWatch Logs**: Filter for ERROR, WARN
3. **Enable X-Ray Tracing**: For detailed execution traces
4. **Contact AWS Support**: For service-level issues

---

## 📚 Additional Resources

- [AWS Lambda Troubleshooting Guide](https://docs.aws.amazon.com/lambda/latest/dg/lambda-troubleshooting.html)
- [DynamoDB Streams Troubleshooting](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.Troubleshooting.html)
- [RDS Connectivity Issues](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Troubleshooting.html)
