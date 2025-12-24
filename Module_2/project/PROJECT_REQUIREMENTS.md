# 📋 E-Commerce Product Onboarding System - Project Requirements Document

## 🎯 Overview

**Project Type:** Real-World AWS Serverless Application  
**Difficulty Level:** Intermediate to Advanced  
**Estimated Time:** 40-60 hours  
**Prerequisites:** Basic Python, AWS fundamentals, SQL knowledge

---

## 📖 Table of Contents

1. [Problem Statement](#problem-statement)
2. [Business Requirements](#business-requirements)
3. [Technical Requirements](#technical-requirements)
4. [AWS Services Overview](#aws-services-overview)
5. [System Design Guidelines](#system-design-guidelines)
6. [Implementation Phases](#implementation-phases)
7. [Acceptance Criteria](#acceptance-criteria)
8. [Evaluation Rubric](#evaluation-rubric)

---

## 1. Problem Statement

### 🏢 The Business Scenario

**TechMart** is a growing e-commerce marketplace that allows third-party vendors to sell their products on the platform. Currently, vendors manually submit product information through a web form, entering one product at a time. This process is:

- ⏰ **Extremely slow** - Large vendors have 1000+ products
- 😫 **Error-prone** - Manual data entry leads to mistakes
- 💸 **Expensive** - Requires dedicated data entry staff
- 🐌 **Not scalable** - Can't handle multiple vendors simultaneously

### 💡 The Solution Needed

Build an **automated product onboarding system** that:

1. **Accepts bulk uploads** - Vendors upload CSV files with hundreds of products
2. **Validates data** - Ensures product information meets quality standards
3. **Provides feedback** - Notifies vendors about success/failures
4. **Maintains catalog** - Stores validated products in the database
5. **Tracks history** - Complete audit trail of all uploads

### 🎯 Real-World Impact

Similar systems are used by:
- **Amazon Seller Central** - Bulk product uploads for 3rd party sellers
- **Shopify** - CSV imports for store owners
- **eBay** - Bulk listing tools
- **Walmart Marketplace** - Vendor product management

---

## 2. Business Requirements

### 2.1 Functional Requirements

#### FR1: Bulk Product Upload
- **What:** Vendors can upload CSV files containing product information
- **Why:** Enables vendors to onboard hundreds of products in minutes instead of hours
- **Success Criteria:** 
  - Support CSV files up to 10MB
  - Process up to 10,000 products per upload
  - Complete processing within 5 minutes

#### FR2: Data Validation
- **What:** System validates each product against business rules
- **Why:** Prevents bad data from entering the catalog, maintains quality
- **Validation Rules Required:**
  1. **Required Fields** - vendor_product_id, product_name, category, SKU, price, stock_quantity
  2. **Price Range** - Between $0.01 and $999,999.99
  3. **Stock Quantity** - Between 0 and 1,000,000
  4. **Category Whitelist** - Must be from approved categories
  5. **SKU Uniqueness** - No duplicate SKUs across platform
  6. **Vendor Product ID Uniqueness** - No duplicates per vendor
  7. **Field Length Limits** - product_name ≤ 200 chars, description ≤ 2000 chars

#### FR3: Error Reporting
- **What:** System generates detailed error reports for failed validations
- **Why:** Vendors need to know exactly what to fix
- **Success Criteria:**
  - Error report as downloadable CSV
  - Shows row number, product ID, error type, error message
  - Available within 1 minute of upload completion

#### FR4: Vendor Notification
- **What:** Email notification when upload completes
- **Why:** Vendors shouldn't have to constantly check status
- **Success Criteria:**
  - Email within 2 minutes of completion
  - Contains success/failure statistics
  - Includes link to error report (if errors exist)

#### FR5: Audit Trail
- **What:** Complete history of all uploads and their results
- **Why:** Compliance, troubleshooting, analytics
- **Success Criteria:**
  - Track: upload timestamp, vendor, file name, total/valid/error counts
  - Queryable by vendor, date range, status
  - Retained for minimum 90 days

### 2.2 Non-Functional Requirements

#### NFR1: Performance
- Process 1000 products in under 3 minutes
- Handle 100 concurrent uploads
- 99.9% uptime during business hours

#### NFR2: Scalability
- Auto-scale to handle peak loads (holiday seasons)
- No manual intervention required for scaling
- Support growth to 10,000 vendors

#### NFR3: Security
- Vendors can only access their own uploads
- Secure credential management (no hardcoded passwords)
- All data encrypted at rest and in transit
- Audit logs for compliance

#### NFR4: Cost Efficiency
- Pay-per-use model (no idle resource costs)
- Target: < $20/month for 1000 uploads
- Optimize for minimal data transfer costs

#### NFR5: Maintainability
- Clear separation of concerns
- Comprehensive logging
- Easy to update validation rules
- Automated deployment

---

## 3. Technical Requirements

### 3.1 Input Specifications

#### CSV File Format
```csv
vendor_product_id,product_name,category,subcategory,description,sku,brand,price,compare_at_price,stock_quantity,unit,weight_kg,dimensions_cm,image_url
PROD0001,Wireless Mouse - Model 651,Computer Accessories,Mice & Keyboards,Ergonomic wireless mouse...,CA-VEND001-0001,TechGear,19.99,,150,piece,0.25,12x8x4,https://images.example.com/mouse.jpg
```

**Required Columns:**
- vendor_product_id (String, max 100 chars)
- product_name (String, max 200 chars)
- category (String, from whitelist)
- sku (String, max 100 chars, globally unique)
- price (Decimal, 2 decimal places)
- stock_quantity (Integer, >= 0)

**Optional Columns:**
- subcategory, description, brand, compare_at_price, unit, weight_kg, dimensions_cm, image_url

### 3.2 Database Schema Requirements

#### Products Table (RDS PostgreSQL)
```sql
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    vendor_id VARCHAR(50) NOT NULL,
    vendor_product_id VARCHAR(100) NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    sku VARCHAR(100) UNIQUE NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Additional fields...
    UNIQUE(vendor_id, vendor_product_id)
);
```

#### Upload History Table
```sql
CREATE TABLE upload_history (
    upload_id VARCHAR(50) PRIMARY KEY,
    vendor_id VARCHAR(50) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    total_records INTEGER,
    valid_records INTEGER DEFAULT 0,
    error_records INTEGER DEFAULT 0,
    status VARCHAR(20), -- 'processing', 'completed', 'partial', 'failed'
    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Validation Errors Table
```sql
CREATE TABLE validation_errors (
    error_id SERIAL PRIMARY KEY,
    upload_id VARCHAR(50) NOT NULL,
    row_number INTEGER NOT NULL,
    error_type VARCHAR(50) NOT NULL,
    error_message TEXT NOT NULL,
    original_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.3 API Specifications

#### Email Notification Format
```
Subject: Product Upload Complete - [filename] ([success_rate]% Success)

Body:
Upload ID: UPLOAD_20241221_103045
File Name: VEND001_products.csv
Total Products: 1000
Valid Products: 950 (95%)
Invalid Products: 50 (5%)

Status: PARTIAL

[If errors exist]
Download Error Report: [presigned_url]
(Link expires in 7 days)
```

### 3.4 Error CSV Format
```csv
Row Number,Vendor Product ID,SKU,Product Name,Error Type,Error Message,Price,Stock Quantity
5,PROD0005,SKU-005,Invalid Product,INVALID_PRICE,Price must be at least 0.01,-10.00,100
15,PROD0015,SKU-003,Duplicate Item,DUPLICATE_SKU,Duplicate SKU: SKU-003 already exists,29.99,50
```

---

## 4. AWS Services Overview

### Why Serverless Architecture?

**Traditional Server Approach:**
```
Problems:
- Must provision servers even when idle
- Manual scaling required
- OS/security patching overhead
- Pay for 24/7 uptime
- Complex infrastructure management
```

**Serverless Approach:**
```
Benefits:
✓ Pay only for actual usage (per request)
✓ Automatic scaling (0 to 1000s)
✓ No server management
✓ Built-in high availability
✓ Focus on business logic
```

---

### 4.1 Amazon S3 (Simple Storage Service)

#### What is S3?
Object storage service for storing and retrieving any amount of data from anywhere.

#### Why Use S3 for This Project?
1. **Durability** - 99.999999999% (11 9's) - your files won't get lost
2. **Scalability** - Store unlimited files, any size
3. **Event Notifications** - Can trigger Lambda when file uploaded
4. **Cost** - $0.023 per GB/month, first 5GB free
5. **Security** - Fine-grained access control, encryption

#### How It Works in Our System
```
Vendor uploads CSV → S3 bucket → Triggers Lambda function
                  → Stores error reports for download
```

#### Key Concepts to Learn
- **Buckets** - Containers for objects (like folders)
- **Objects** - Files stored in buckets
- **Prefixes** - Organize objects (uploads/, errors/)
- **Event Notifications** - Trigger actions on upload
- **Presigned URLs** - Temporary download links

#### What You'll Do
1. Create S3 bucket with versioning
2. Configure folder structure (uploads/, errors/)
3. Set up event notifications to trigger Lambda
4. Generate presigned URLs for error reports
5. Implement lifecycle policies (optional)

---

### 4.2 AWS Lambda

#### What is Lambda?
Run code without provisioning servers. Pay only for compute time used.

#### Why Use Lambda for This Project?
1. **Event-Driven** - Automatically runs when CSV uploaded
2. **Scalable** - Handles 1 or 1000 uploads simultaneously
3. **Cost-Effective** - First 1M requests/month free
4. **No Server Management** - Focus on code, not infrastructure
5. **Container Support** - Deploy complex dependencies (like psycopg2)

#### How It Works in Our System
```
3 Lambda Functions:

1. CSV Parser (Trigger: S3 upload)
   - Downloads CSV from S3
   - Parses rows
   - Inserts to DynamoDB

2. Validator (Trigger: DynamoDB Streams)
   - Validates product data
   - Inserts valid → RDS
   - Sends invalid → SQS

3. Error Processor (Trigger: SQS messages)
   - Generates error CSV
   - Uploads to S3
   - Sends email notification
```

#### Key Concepts to Learn
- **Functions** - Discrete units of code
- **Triggers** - Events that invoke functions
- **Container Images** - Package code + dependencies
- **Environment Variables** - Configuration
- **VPC Integration** - Access private resources (RDS)
- **Execution Role** - Permissions for AWS service access

#### What You'll Do
1. Write 3 Python functions (CSV parser, validator, error processor)
2. Create Dockerfiles for each function
3. Push container images to ECR
4. Configure triggers (S3, DynamoDB Streams, SQS)
5. Set up VPC access for RDS connectivity
6. Implement error handling and logging

---

### 4.3 Amazon DynamoDB

#### What is DynamoDB?
Fully managed NoSQL database with single-digit millisecond performance.

#### Why Use DynamoDB for This Project?
1. **Streams** - Real-time change capture (perfect for triggering validation)
2. **Scalability** - Auto-scales to millions of requests/second
3. **Performance** - Consistent low latency
4. **Serverless** - No servers to manage
5. **Pay-per-Request** - Only pay for what you use

#### Why Not Use Only RDS?
```
RDS Challenges:
- Expensive to scale for temporary spikes
- Complex to set up change data capture
- Requires VPC (adds complexity)
- Connection pooling needed (limited connections)

DynamoDB Advantages:
+ Built-in Streams (automatic change capture)
+ Infinite scaling
+ No connection limits
+ Simple event-driven architecture
```

#### How It Works in Our System
```
CSV Parser → DynamoDB (temporary staging)
          → DynamoDB Streams captures changes
          → Triggers Validator Lambda
          → Updates record status after validation
```

#### Key Concepts to Learn
- **Tables** - Store items (like rows)
- **Partition Key + Sort Key** - Unique identifier
- **Global Secondary Index (GSI)** - Alternative query patterns
- **Streams** - Ordered log of item changes
- **Items** - Individual records (like JSON documents)

#### What You'll Do
1. Design table schema (partition key: upload_id, sort key: record_id)
2. Create GSI for querying by vendor
3. Enable Streams with NEW_IMAGE view type
4. Implement batch write operations
5. Update item status after validation

---

### 4.4 Amazon RDS (Relational Database Service)

#### What is RDS?
Managed relational database service supporting PostgreSQL, MySQL, etc.

#### Why Use RDS for This Project?
1. **ACID Transactions** - Data integrity for product catalog
2. **Relational Model** - Complex queries with JOINs
3. **Foreign Keys** - Enforce referential integrity
4. **Unique Constraints** - Prevent duplicate SKUs
5. **Audit Trail** - Detailed error tracking

#### Why PostgreSQL?
```
Benefits:
✓ Advanced data types (JSONB for flexible data)
✓ Full-text search capabilities
✓ Excellent performance
✓ Strong consistency guarantees
✓ Free and open source
```

#### How It Works in Our System
```
RDS Stores:
- Vendors (master data)
- Product Categories (whitelist)
- Products (validated catalog)
- Upload History (audit trail)
- Validation Errors (detailed errors)
```

#### Key Concepts to Learn
- **Tables & Schemas** - Structured data
- **Primary Keys** - Unique identifiers
- **Foreign Keys** - Relationships between tables
- **Indexes** - Fast lookups
- **Transactions** - All-or-nothing operations
- **VPC Security** - Private database access

#### What You'll Do
1. Design 5-table schema with proper relationships
2. Create unique constraints (SKU, vendor_product_id)
3. Implement foreign key constraints
4. Write SQL for validation queries
5. Use transactions for data integrity
6. Configure VPC security groups

---

### 4.5 Amazon SQS (Simple Queue Service)

#### What is SQS?
Fully managed message queuing service for decoupling application components.

#### Why Use SQS for This Project?
1. **Decoupling** - Validator and Error Processor run independently
2. **Buffering** - Handles traffic spikes gracefully
3. **Retry Logic** - Automatic retries on failure
4. **Dead-Letter Queue** - Captures permanently failed messages
5. **Batch Processing** - Process multiple errors at once

#### Why Not Process Errors Immediately?
```
Without SQS:
Validator finds error → Immediately generate CSV → Send email
Problem: 100 errors = 100 CSV files = 100 emails! 😱

With SQS:
Validator finds error → Send to queue
All errors collected → Process once → 1 CSV, 1 email ✓
```

#### How It Works in Our System
```
Validator Lambda → SQS (collects errors)
                → Waits for batch or timeout
                → Triggers Error Processor Lambda
                → Process all errors together
```

#### Key Concepts to Learn
- **Queues** - Store messages temporarily
- **Messages** - Individual units of work
- **Visibility Timeout** - Prevents duplicate processing
- **Dead-Letter Queue** - Handle failed messages
- **Batch Processing** - Process multiple at once

#### What You'll Do
1. Create SQS queue for validation errors
2. Create Dead-Letter Queue for failed processing
3. Configure visibility timeout (5 minutes)
4. Implement batch message sending
5. Set up Lambda trigger with batching window

---

### 4.6 Amazon SNS (Simple Notification Service)

#### What is SNS?
Pub/sub messaging service for sending notifications to multiple subscribers.

#### Why Use SNS for This Project?
1. **Multiple Subscribers** - Email, SMS, webhooks, etc.
2. **Filtering** - Send different notifications to different people
3. **Scalability** - Millions of messages per second
4. **Reliability** - Message delivery guarantees
5. **Cost** - First 1000 emails free monthly

#### How It Works in Our System
```
Error Processor → SNS Topic → Email Subscription
                           → (Future) SMS Subscription
                           → (Future) Slack Webhook
```

#### Key Concepts to Learn
- **Topics** - Named channels for messages
- **Subscriptions** - How messages are delivered
- **Email Protocol** - Confirmation required
- **Message Attributes** - Metadata for filtering

#### What You'll Do
1. Create SNS topic for upload notifications
2. Subscribe vendor email addresses
3. Send formatted email with upload summary
4. Include presigned URL for error downloads

---

### 4.7 AWS Secrets Manager

#### What is Secrets Manager?
Securely store and manage sensitive information like database passwords.

#### Why Use Secrets Manager?
1. **Security** - Never hardcode passwords in code
2. **Rotation** - Automatically rotate credentials
3. **Audit** - Track who accessed secrets when
4. **Encryption** - Encrypted using AWS KMS
5. **Caching** - Reduce API calls with client-side cache

#### Why Not Environment Variables?
```
Environment Variables:
- Visible in console
- Included in logs
- No rotation support
- No audit trail

Secrets Manager:
✓ Never exposed
✓ Automatic rotation
✓ Complete audit trail
✓ Versioned (rollback support)
```

#### How It Works in Our System
```
Lambda starts → Retrieves RDS credentials from Secrets Manager
            → Caches credentials (1 hour)
            → Connects to database
            → (Next invocation reuses cache)
```

#### Key Concepts to Learn
- **Secrets** - Encrypted key-value pairs
- **Versioning** - Multiple versions (AWSCURRENT, AWSPREVIOUS)
- **Rotation** - Automatic password changes
- **Caching** - Client-side cache for performance

#### What You'll Do
1. Store RDS credentials in Secrets Manager
2. Implement caching in Lambda (reduce costs)
3. Retrieve secrets at runtime
4. Handle secret rotation (optional)

---

### 4.8 Amazon ECR (Elastic Container Registry)

#### What is ECR?
Fully managed Docker container registry for storing container images.

#### Why Use ECR for This Project?
1. **Container-Based Lambda** - Deploy complex dependencies
2. **Large Packages** - Up to 10GB vs 250MB for ZIP
3. **Docker Workflow** - Familiar development process
4. **Security** - Image scanning for vulnerabilities
5. **Integration** - Native Lambda support

#### Why Containers vs ZIP Files?
```
ZIP Deployment Challenges:
- Max 250MB (too small for many dependencies)
- Must compile binaries for Lambda environment
- Complex dependency management
- psycopg2 requires native libraries

Container Deployment:
✓ Up to 10GB size
✓ Include any dependencies
✓ Easy local testing (Docker)
✓ Consistent environments
```

#### How It Works in Our System
```
Developer → Build Docker image locally
         → Push to ECR
         → Lambda pulls from ECR on deploy/cold start
```

#### Key Concepts to Learn
- **Repositories** - Store container images
- **Images** - Packaged applications
- **Tags** - Version identifiers (latest, v1.0.0)
- **Image Scanning** - Security vulnerability detection

#### What You'll Do
1. Create 3 ECR repositories (one per Lambda)
2. Write Dockerfiles with Python + dependencies
3. Build container images
4. Push images to ECR
5. Configure Lambda to use ECR images

---

### 4.9 Amazon CloudWatch

#### What is CloudWatch?
Monitoring and observability service for AWS resources and applications.

#### Why Use CloudWatch?
1. **Logs** - Centralized log storage and analysis
2. **Metrics** - Performance monitoring
3. **Alarms** - Alert on anomalies
4. **Dashboards** - Visualize system health
5. **Insights** - Query logs with SQL-like syntax

#### How It Works in Our System
```
Every Lambda execution → CloudWatch Logs
Custom metrics → CloudWatch Metrics
Errors/anomalies → CloudWatch Alarms → Notifications
```

#### Key Concepts to Learn
- **Log Groups** - Container for log streams
- **Log Streams** - Sequence of log events
- **Metrics** - Numeric measurements over time
- **Alarms** - Automated responses to metric thresholds

#### What You'll Do
1. Configure Lambda logging
2. Publish custom metrics (products validated, errors)
3. Query logs with CloudWatch Insights
4. Create dashboards (optional)
5. Set up alarms (optional)

---

### 4.10 Amazon VPC (Virtual Private Cloud)

#### What is VPC?
Isolated network within AWS where you can launch resources.

#### Why Use VPC for This Project?
1. **Security** - RDS not publicly accessible
2. **Isolation** - Network segmentation
3. **Control** - Define security groups, network ACLs
4. **Compliance** - Meet regulatory requirements

#### How It Works in Our System
```
Lambda Functions → VPC → RDS (private subnet)
                      → Internet (via NAT Gateway for AWS API calls)
```

#### Key Concepts to Learn
- **Subnets** - Subdivisions of VPC (public, private)
- **Security Groups** - Firewall rules (stateful)
- **NAT Gateway** - Allow private resources to reach internet
- **Route Tables** - Control traffic routing

#### What You'll Do
1. Use existing VPC (or create new)
2. Configure Lambda in private subnets
3. Set up security groups (Lambda → RDS on port 5432)
4. Ensure NAT Gateway for internet access

---

## 5. System Design Guidelines

### 5.1 Architecture Decisions

#### Decision 1: Why DynamoDB + RDS (Hybrid Approach)?

**Question:** Why not use just one database?

**Answer:**

**DynamoDB for Staging:**
```
Advantages:
✓ Built-in Streams (real-time change capture)
✓ Scales instantly for upload spikes
✓ No connection limits
✓ Simple event-driven triggers

Use Case: Temporary storage during validation
```

**RDS for Catalog:**
```
Advantages:
✓ ACID transactions (data integrity)
✓ Complex queries with JOINs
✓ Foreign key constraints
✓ Unique constraints (prevent duplicate SKUs)

Use Case: Permanent product catalog
```

**The Flow:**
```
Upload → DynamoDB (staging + streams)
      → Validate → RDS (persistent catalog)
      → Delete from DynamoDB (optional cleanup)
```

---

#### Decision 2: Why 3 Separate Lambda Functions?

**Question:** Why not one big Lambda?

**Answer:**

**Single Lambda Approach:**
```
Problems:
- Timeout issues (CSV parsing + validation + error processing)
- Hard to scale independently
- Difficult to debug
- All-or-nothing (one failure breaks everything)
```

**3 Lambda Approach:**
```
Benefits:
✓ Separation of concerns (each does one thing well)
✓ Independent scaling (validation scales separately)
✓ Easier debugging (isolate issues)
✓ Fault tolerance (one failure doesn't break others)
✓ Different triggers (S3, Streams, SQS)
```

**The Lambdas:**
```
1. CSV Parser (Triggered by S3)
   - Simple: Parse CSV, insert to DynamoDB
   - Fast: Completes in 2-3 seconds
   
2. Validator (Triggered by DynamoDB Streams)
   - Complex: 7 validation rules + DB queries
   - Scales: Processes batches independently
   
3. Error Processor (Triggered by SQS)
   - Batching: Waits for all errors
   - Efficient: One CSV, one email per upload
```

---

#### Decision 3: Why SQS Between Validator and Error Processor?

**Question:** Why not call Error Processor directly?

**Answer:**

**Direct Call:**
```
Validator finds error 1 → Call Error Processor → Generate CSV → Send email
Validator finds error 2 → Call Error Processor → Generate CSV → Send email
...
Validator finds error 50 → Call Error Processor → Generate CSV → Send email

Result: 50 CSV files, 50 emails! 😱
```

**SQS Queue:**
```
Validator finds error 1 → Send to SQS queue
Validator finds error 2 → Send to SQS queue
...
Validator finds error 50 → Send to SQS queue
        ↓
Wait for batch timeout (30 seconds)
        ↓
Error Processor triggered with ALL 50 errors
        ↓
Generate 1 CSV with all errors, send 1 email ✓

Result: 1 CSV file, 1 email!
```

**Additional Benefits:**
- **Retry Logic**: Failed processing automatically retried
- **Dead-Letter Queue**: Permanently failed messages captured
- **Decoupling**: Validator and Error Processor run independently

---

#### Decision 4: Why Container Images for Lambda?

**Question:** Why not use ZIP deployment?

**Answer:**

**ZIP Deployment:**
```
Problems:
- 250MB size limit (too small for psycopg2 + dependencies)
- Must compile for Amazon Linux 2
- Complex layer management
- Difficult local testing
```

**Container Deployment:**
```
Benefits:
✓ Up to 10GB size
✓ Include any dependencies (psycopg2, pandas, etc.)
✓ Local testing with Docker
✓ Familiar workflow (Dockerfile)
✓ Version control for environments
```

**Our Use Case:**
```
Need: psycopg2 (PostgreSQL driver) + PostgreSQL libraries
ZIP: Complex compilation, dependency issues
Container: Simple Dockerfile, works first try ✓
```

---

### 5.2 Data Flow Design

#### The Complete Journey of a CSV Upload

```
Step 1: UPLOAD
├─ Vendor uploads VEND001_products.csv to S3
├─ S3 stores in: s3://bucket/uploads/VEND001/VEND001_products.csv
└─ S3 triggers S3 Event Notification

Step 2: PARSE (CSV Parser Lambda)
├─ Lambda downloads CSV from S3
├─ Verifies vendor exists in RDS
├─ Creates upload_history record (status: 'processing')
├─ Parses CSV rows (e.g., 1000 products)
├─ Converts to DynamoDB format
├─ Batch inserts to DynamoDB (status: 'pending_validation')
└─ Each insert creates a DynamoDB Stream record

Step 3: VALIDATE (Validator Lambda)
├─ DynamoDB Streams triggers Lambda with batch (100 records)
├─ For EACH record:
│   ├─ Run 7 validation rules
│   ├─ IF VALID:
│   │   ├─ INSERT to RDS products table
│   │   └─ UPDATE DynamoDB status = 'validated'
│   └─ IF INVALID:
│       ├─ SEND error to SQS queue
│       ├─ INSERT to RDS validation_errors table
│       └─ UPDATE DynamoDB status = 'error'
└─ Update RDS upload_history counts

Step 4: REPORT (Error Processor Lambda)
├─ SQS waits for batch or 30-second timeout
├─ Lambda triggered with all errors for upload
├─ Groups errors by upload_id
├─ Generates error CSV
├─ Uploads to S3: s3://bucket/errors/VEND001/UPLOAD_xxx_errors.csv
├─ Updates upload_history with error_file_s3_key
├─ Checks if upload complete (valid + error = total)
├─ IF COMPLETE:
│   └─ Triggers SNS notification
└─ SNS sends email to vendor
```

---

### 5.3 Error Handling Strategy

#### Multi-Level Error Handling

**Level 1: Prevention (Validation)**
```python
# Prevent errors before they occur
if price < 0.01:
    return False, "INVALID_PRICE", "Price must be at least 0.01"
```

**Level 2: Detection (Try-Catch)**
```python
try:
    conn = psycopg2.connect(...)
except psycopg2.OperationalError as e:
    logger.error(f"Database connection failed: {e}")
    # Retry or fail gracefully
```

**Level 3: Recovery (Retry Logic)**
```python
# Lambda automatic retries
MaximumRetryAttempts: 2

# SQS automatic retries
maxReceiveCount: 3 (then → DLQ)
```

**Level 4: Notification (Logging + Alerts)**
```python
logger.error(f"Upload {upload_id} failed: {error}")
cloudwatch.put_metric_data(...)  # Trigger alarms
```

**Level 5: Audit (Database Recording)**
```sql
INSERT INTO validation_errors (upload_id, error_type, error_message, ...)
```

---

### 5.4 Security Design

#### Defense in Depth

**Layer 1: Network Security**
```
- RDS in private subnet (no internet access)
- Lambda in VPC to reach RDS
- Security groups: only Lambda → RDS on port 5432
```

**Layer 2: Access Control**
```
- IAM roles with least privilege
- Lambda role: only required permissions
- No long-term credentials in code
```

**Layer 3: Data Protection**
```
- S3: Server-side encryption (AES-256)
- RDS: Encrypted storage
- Secrets Manager: KMS encryption
- TLS for all network traffic
```

**Layer 4: Secret Management**
```
- No hardcoded passwords
- Secrets Manager for RDS credentials
- Client-side caching to reduce costs
```

**Layer 5: Audit & Compliance**
```
- CloudWatch logs: all Lambda executions
- S3 access logs: who uploaded what
- RDS query logs: what was modified
- upload_history: complete audit trail
```

---

## 6. Implementation Phases

### Phase 1: Foundation Setup (Week 1)

#### Objectives
- Set up AWS account and services
- Create database schemas
- Generate test data

#### Tasks

**1.1 AWS Account Setup**
- [ ] Create AWS account (if needed)
- [ ] Install and configure AWS CLI
- [ ] Set up IAM user with appropriate permissions
- [ ] Install Docker Desktop

**1.2 Database Design**
- [ ] Design RDS schema (5 tables)
- [ ] Create ERD (Entity Relationship Diagram)
- [ ] Write SQL schema with constraints
- [ ] Design DynamoDB table schema

**1.3 Test Data Generation**
- [ ] Create product category list
- [ ] Generate 3 vendor profiles
- [ ] Create sample CSV files (100 products each)
- [ ] Include intentional errors for testing

**Deliverables:**
- AWS CLI configured
- `database_schema.sql` file
- 3 test CSV files
- ERD diagram

---

### Phase 2: Infrastructure Deployment (Week 2)

#### Objectives
- Create all AWS resources
- Configure networking
- Set up security

#### Tasks

**2.1 Storage Setup**
- [ ] Create S3 bucket with versioning
- [ ] Configure folder structure (uploads/, errors/)
- [ ] Enable encryption and lifecycle policies

**2.2 Database Setup**
- [ ] Launch RDS PostgreSQL instance
- [ ] Configure VPC and security groups
- [ ] Run schema creation SQL
- [ ] Populate category whitelist
- [ ] Insert test vendor data

**2.3 DynamoDB Setup**
- [ ] Create UploadRecords table
- [ ] Configure partition key and sort key
- [ ] Create GSI for vendor queries
- [ ] Enable Streams with NEW_IMAGE

**2.4 Messaging Setup**
- [ ] Create SQS error queue
- [ ] Create Dead-Letter Queue
- [ ] Configure visibility timeout
- [ ] Create SNS topic
- [ ] Subscribe email address

**2.5 Security Setup**
- [ ] Store RDS credentials in Secrets Manager
- [ ] Configure VPC for Lambda access
- [ ] Set up security groups

**Deliverables:**
- All AWS resources created
- RDS populated with test data
- Secrets Manager configured
- Network diagram

---

### Phase 3: Lambda Development (Week 3-4)

#### Objectives
- Develop 3 Lambda functions
- Implement business logic
- Create Docker containers

#### Tasks

**3.1 CSV Parser Lambda**
- [ ] Write Dockerfile with Python 3.11
- [ ] Implement CSV download from S3
- [ ] Implement vendor verification
- [ ] Implement CSV parsing logic
- [ ] Implement DynamoDB batch insert
- [ ] Add logging and error handling
- [ ] Test locally with Docker

**3.2 Product Validator Lambda**
- [ ] Write Dockerfile with psycopg2
- [ ] Implement DynamoDB Streams event handler
- [ ] Implement 7 validation rules
- [ ] Implement RDS insertion for valid products
- [ ] Implement SQS messaging for errors
- [ ] Implement connection pooling
- [ ] Add logging and metrics

**3.3 Error Processor Lambda**
- [ ] Write Dockerfile
- [ ] Implement SQS batch processing
- [ ] Implement error CSV generation
- [ ] Implement S3 upload for error files
- [ ] Implement presigned URL generation
- [ ] Implement SNS notification
- [ ] Add email template formatting

**Deliverables:**
- 3 Dockerfiles
- 3 Python Lambda functions
- requirements.txt for each
- Local test scripts

---

### Phase 4: Container Deployment (Week 5)

#### Objectives
- Build and push Docker images
- Deploy Lambda functions
- Configure triggers

#### Tasks

**4.1 ECR Setup**
- [ ] Create 3 ECR repositories
- [ ] Authenticate Docker to ECR
- [ ] Tag images appropriately

**4.2 Image Build & Push**
- [ ] Build csv-parser image
- [ ] Build product-validator image
- [ ] Build error-processor image
- [ ] Push all images to ECR
- [ ] Verify image availability

**4.3 Lambda Deployment**
- [ ] Create IAM roles for each Lambda
- [ ] Create CSV Parser from ECR image
- [ ] Create Validator from ECR image
- [ ] Create Error Processor from ECR image
- [ ] Configure environment variables
- [ ] Configure VPC settings
- [ ] Set memory and timeout

**4.4 Event Configuration**
- [ ] Configure S3 event notification
- [ ] Configure DynamoDB Streams trigger
- [ ] Configure SQS trigger
- [ ] Verify all triggers active

**Deliverables:**
- ECR repositories with images
- 3 deployed Lambda functions
- All triggers configured
- Deployment scripts

---

### Phase 5: Integration Testing (Week 6)

#### Objectives
- Test end-to-end flow
- Verify all components
- Fix bugs

#### Tasks

**5.1 Happy Path Testing**
- [ ] Upload valid CSV file
- [ ] Verify CSV Parser execution
- [ ] Verify DynamoDB records
- [ ] Verify Validator execution
- [ ] Verify products in RDS
- [ ] Verify email notification

**5.2 Error Path Testing**
- [ ] Upload CSV with errors
- [ ] Verify validation failures
- [ ] Verify SQS messages
- [ ] Verify Error Processor execution
- [ ] Verify error CSV generated
- [ ] Verify email with error link

**5.3 Edge Case Testing**
- [ ] Empty CSV file
- [ ] Duplicate SKUs
- [ ] Invalid category
- [ ] Missing required fields
- [ ] Large file (1000+ products)
- [ ] Concurrent uploads

**5.4 Performance Testing**
- [ ] Measure processing time
- [ ] Test concurrent uploads
- [ ] Monitor CloudWatch metrics
- [ ] Verify auto-scaling

**Deliverables:**
- Test cases documented
- Test results
- Bug fixes implemented
- Performance report

---

### Phase 6: Monitoring & Documentation (Week 7)

#### Objectives
- Set up monitoring
- Create documentation
- Prepare demo

#### Tasks

**6.1 Monitoring Setup**
- [ ] Review CloudWatch Logs
- [ ] Create custom metrics
- [ ] Set up CloudWatch alarms
- [ ] Create dashboard (optional)

**6.2 Documentation**
- [ ] Architecture diagram
- [ ] README with setup instructions
- [ ] API documentation (email format, CSV format)
- [ ] Troubleshooting guide
- [ ] Cost analysis

**6.3 Demo Preparation**
- [ ] Prepare demo script
- [ ] Create demo slides
- [ ] Record demo video (optional)
- [ ] Prepare Q&A

**Deliverables:**
- Complete documentation
- CloudWatch dashboard
- Demo materials
- Final presentation

---

## 7. Acceptance Criteria

### 7.1 Functional Criteria

#### CSV Upload & Processing
- [ ] Accepts CSV files up to 10MB
- [ ] Processes 1000 products in < 5 minutes
- [ ] Validates vendor before processing
- [ ] Creates upload history record
- [ ] Updates counts correctly

#### Data Validation
- [ ] All 7 validation rules implemented
- [ ] Validates against RDS categories
- [ ] Prevents duplicate SKUs globally
- [ ] Prevents duplicate vendor_product_id per vendor
- [ ] All validation errors captured

#### Error Reporting
- [ ] Error CSV generated with correct format
- [ ] Error CSV uploaded to S3
- [ ] Error CSV downloadable via presigned URL
- [ ] Upload history updated with error file location

#### Notifications
- [ ] Email sent within 2 minutes of completion
- [ ] Email contains correct statistics
- [ ] Email includes error download link (if errors)
- [ ] Email formatted professionally

#### Audit Trail
- [ ] All uploads recorded in upload_history
- [ ] All errors recorded in validation_errors
- [ ] Complete lineage traceable
- [ ] Queryable by vendor and date

### 7.2 Non-Functional Criteria

#### Performance
- [ ] Processes 1000 products in < 5 minutes
- [ ] Handles 10 concurrent uploads
- [ ] No timeouts under normal load
- [ ] Database queries < 100ms average

#### Scalability
- [ ] Auto-scales with load
- [ ] No manual intervention needed
- [ ] Handles 10,000 product uploads

#### Security
- [ ] No hardcoded credentials
- [ ] RDS not publicly accessible
- [ ] All data encrypted
- [ ] IAM roles follow least privilege
- [ ] Secrets Manager used correctly

#### Cost
- [ ] Monthly cost < $20 for 1000 uploads
- [ ] No idle resources
- [ ] Optimized batch sizes

#### Code Quality
- [ ] Clean, readable code
- [ ] Proper error handling
- [ ] Comprehensive logging
- [ ] Comments where needed
- [ ] Follows Python best practices

#### Documentation
- [ ] README complete
- [ ] Architecture diagram clear
- [ ] Setup instructions accurate
- [ ] Code commented
- [ ] API formats documented

---

## 8. Evaluation Rubric

### Total Points: 100

#### Architecture & Design (25 points)
- **Service Selection (10 points)**
  - Appropriate AWS services chosen
  - Justification for each service
  - Hybrid database approach explained

- **System Design (10 points)**
  - Clear data flow
  - Proper separation of concerns
  - Scalable architecture

- **Security Design (5 points)**
  - No hardcoded credentials
  - Proper IAM roles
  - Network isolation

#### Implementation (35 points)
- **CSV Parser Lambda (10 points)**
  - Correctly downloads from S3
  - Proper CSV parsing
  - DynamoDB batch insert
  - Error handling

- **Validator Lambda (15 points)**
  - All 7 validation rules implemented
  - Correct stream processing
  - RDS integration working
  - SQS integration working
  - Connection pooling

- **Error Processor Lambda (10 points)**
  - SQS batch processing
  - CSV generation correct
  - S3 upload working
  - SNS notification working

#### Infrastructure (20 points)
- **Database Setup (10 points)**
  - RDS schema correct
  - Constraints properly defined
  - DynamoDB table configured
  - Streams enabled

- **Event Configuration (10 points)**
  - S3 trigger working
  - DynamoDB Streams trigger working
  - SQS trigger working
  - All triggers properly configured

#### Testing & Quality (10 points)
- **Testing (5 points)**
  - End-to-end test successful
  - Error cases tested
  - Edge cases handled

- **Code Quality (5 points)**
  - Clean code
  - Proper logging
  - Error handling
  - Comments

#### Documentation (10 points)
- **Technical Documentation (5 points)**
  - README complete
  - Architecture diagram
  - Setup instructions

- **Code Documentation (5 points)**
  - Functions documented
  - Complex logic explained
  - API formats documented

---

## 9. Helpful Resources

### AWS Documentation
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [Amazon DynamoDB Developer Guide](https://docs.aws.amazon.com/dynamodb/)
- [Amazon RDS User Guide](https://docs.aws.amazon.com/rds/)
- [Amazon S3 User Guide](https://docs.aws.amazon.com/s3/)

### Python Libraries
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)
- [Python CSV Module](https://docs.python.org/3/library/csv.html)

### Docker
- [Docker Documentation](https://docs.docker.com/)
- [AWS Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)

### Tutorials
- [Building Event-Driven Architectures](https://aws.amazon.com/event-driven-architecture/)
- [Serverless Patterns](https://serverlessland.com/patterns)

---

## 10. Frequently Asked Questions

### Q1: Can I use a different programming language?
**A:** Yes, but Python is recommended for boto3 support and simplicity. If using Node.js or Java, adjust accordingly.

### Q2: Can I use MySQL instead of PostgreSQL?
**A:** Yes, the concepts are the same. Adjust the SQL syntax and use appropriate drivers.

### Q3: Do I need to use Docker?
**A:** Yes, for Lambda deployment with psycopg2. Alternatively, use Lambda Layers (more complex).

### Q4: How much will this cost to run?
**A:** Minimal during development (~$15/month). RDS is the main cost. Use db.t3.micro free tier if eligible.

### Q5: Can I use LocalStack for local testing?
**A:** Yes! LocalStack can simulate AWS services locally. Great for testing before deploying.

### Q6: What if I get stuck?
**A:** 
1. Check CloudWatch Logs for errors
2. Review AWS service documentation
3. Use AWS re:Post for community help
4. Check Stack Overflow
5. Ask your instructor

### Q7: Can I add extra features?
**A:** Absolutely! Consider:
- API Gateway for programmatic uploads
- Real-time dashboard with QuickSight
- ML-based validation
- Multi-region deployment

### Q8: How do I know if my design is correct?
**A:** Ask yourself:
- Does it meet all requirements?
- Is it scalable?
- Is it secure?
- Is it cost-effective?
- Can you explain each design decision?

---

## 11. Getting Started Checklist

### Before You Begin
- [ ] Read this entire document
- [ ] Understand the problem statement
- [ ] Review all AWS services explanations
- [ ] Set up AWS account
- [ ] Install required tools (AWS CLI, Docker, psql)

### Phase 1 (Week 1)
- [ ] Design database schema
- [ ] Create ERD
- [ ] Generate test data
- [ ] Document design decisions

### Ready to Start?
**Next Steps:**
1. Draw your architecture diagram
2. Create database schema SQL
3. Generate test CSV files
4. Review with instructor (recommended)
5. Begin Phase 2 implementation

---

## 12. Success Tips

### DO:
✅ Start with database design
✅ Test each component independently
✅ Use CloudWatch Logs extensively
✅ Implement error handling everywhere
✅ Document as you go
✅ Ask questions early
✅ Follow AWS best practices
✅ Version control your code

### DON'T:
❌ Hardcode credentials
❌ Skip testing
❌ Ignore CloudWatch Logs
❌ Make everything public
❌ Copy code without understanding
❌ Forget to clean up resources
❌ Overcomplicate the solution

---

## 13. Final Notes

This project is designed to teach you **real-world AWS development**. You'll face challenges, debug issues, and learn by doing. That's the point!

**Remember:**
- It's okay to make mistakes
- Debugging is part of learning
- Ask for help when stuck
- Document your learnings
- Be proud of what you build

**You're building something real** - a system that could actually be used in production!

Good luck! 🚀

---

**Questions? Clarifications needed? Start by:**
1. Re-reading relevant sections
2. Checking AWS documentation
3. Reviewing CloudWatch Logs
4. Asking your instructor

**Ready to build? Let's go!** 💪
