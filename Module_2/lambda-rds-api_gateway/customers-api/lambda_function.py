"""
Customers API Lambda Function
=============================

This Lambda function exposes a REST-style API for managing customers.
It supports CRUD operations (Create, Read, Update, Delete) by delegating
all database access to a generic query executor Lambda.

Architecture Pattern
--------------------
API Gateway
    -> Customers API Lambda (this file)
        -> Generic Query Executor Lambda
            -> Database (Postgres / Aurora / RDS etc.)

Why this design?
----------------
- Keeps DB logic centralized and reusable
- Simplifies security (single DB-access Lambda)
- Enables consistent logging, retries, and monitoring
"""

import json
import os
import traceback
import boto3
import logging
from typing import Dict, Any
from datetime import datetime, UTC

# ---------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ---------------------------------------------------------
# AWS Clients
# ---------------------------------------------------------

# Lambda client used to invoke the generic query executor
lambda_client = boto3.client('lambda')

# Name of the query executor Lambda
# Can be overridden via environment variables
QUERY_EXECUTOR_FUNCTION = os.environ.get(
    'QUERY_EXECUTOR_FUNCTION',
    'generic-query-executor'
)

logger.info(f"Initialized with QUERY_EXECUTOR_FUNCTION: {QUERY_EXECUTOR_FUNCTION}")

# ---------------------------------------------------------
# Helper: Invoke Generic Query Executor
# ---------------------------------------------------------

def invoke_query_executor(
    query: str,
    params: list = None,
    fetch: bool = True
) -> Dict[str, Any]:
    """
    Invokes the generic query executor Lambda.

    Parameters
    ----------
    query : str
        SQL query to execute (parameterized).
    params : list, optional
        Query parameters corresponding to %s placeholders.
    fetch : bool
        If True, returns query results (SELECT / RETURNING).
        If False, executes without fetching data (DELETE).

    Returns
    -------
    Dict[str, Any]
        Normalized response from query executor:
        {
            "success": bool,
            "data": list (optional),
            "rowcount": int (optional),
            "error": str (optional)
        }
    """

    logger.info(f"Invoking query executor function: {QUERY_EXECUTOR_FUNCTION}, query: {query[:100]}, params: {len(params or [])}, fetch: {fetch}")

    # Payload expected by the query executor Lambda
    payload = {
        "query": query,
        "params": params or [],
        "fetch": fetch
    }

    try:
        # Synchronous Lambda invocation
        response = lambda_client.invoke(
            FunctionName=QUERY_EXECUTOR_FUNCTION,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload)
        )

        logger.info(f"Query executor invocation successful, status code: {response.get('StatusCode')}")

        # Read raw payload
        response_payload = json.loads(response["Payload"].read())

        # Handle API Gateway–style responses (body is a string)
        if isinstance(response_payload.get("body"), str):
            result = json.loads(response_payload["body"])
        else:
            result = response_payload

        if result.get("success"):
            logger.info(f"Query executed successfully, rowcount: {result.get('rowcount')}, data_count: {len(result.get('data', []))}")
        else:
            logger.error(f"Query execution failed, error: {result.get('error')}")

        return result

    except Exception as e:
        logger.error(f"Failed to invoke query executor: {QUERY_EXECUTOR_FUNCTION}, error: {str(e)}, type: {type(e).__name__}, trace: {traceback.format_exc()}")
        return {
            "success": False,
            "error": f"Lambda invocation failed: {str(e)}"
        }


# ---------------------------------------------------------
# POST /customers
# ---------------------------------------------------------

def create_customer(event_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new customer record.

    Endpoint
    --------
    POST /customers

    Expected Request Body
    ---------------------
    {
        "customer_id": "CUST001",
        "customer_name": "John Doe",
        "email": "john@example.com",
        "city": "New York",
        "state": "NY"
    }

    Returns
    -------
    201 Created
        Customer record if successful
    400 Bad Request
        Missing required fields
    500 Internal Server Error
        DB or execution error
    """

    logger.info(f"Creating new customer, customer_id: {event_body.get('customer_id')}, email: {event_body.get('email')}")

    # Required fields validation
    required_fields = ["customer_id", "customer_name", "email"]
    for field in required_fields:
        if field not in event_body:
            logger.warning(f"Missing required field: {field}")
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "success": False,
                    "error": f"Missing required field: {field}"
                })
            }

    # SQL INSERT with RETURNING to fetch created record
    query = """
    INSERT INTO demo.customers
    (customer_id, customer_name, email, city, state, created_at)
    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    RETURNING customer_id, customer_name, email, city, state, created_at
    """

    # Parameter order must match query placeholders
    params = [
        event_body["customer_id"],
        event_body["customer_name"],
        event_body["email"],
        event_body.get("city"),
        event_body.get("state")
    ]

    result = invoke_query_executor(query, params, fetch=True)

    if result.get("success"):
        logger.info(f"Customer created successfully, customer_id: {event_body['customer_id']}")
        return {
            "statusCode": 201,
            "body": json.dumps({
                "success": True,
                "message": "Customer created successfully",
                "data": result.get("data", [])[0] if result.get("data") else None
            }, default=str)
        }

    logger.error(f"Failed to create customer, customer_id: {event_body['customer_id']}, error: {result.get('error')}")
    return {
        "statusCode": 500,
        "body": json.dumps({
            "success": False,
            "error": result.get("error", "Unknown error")
        })
    }


# ---------------------------------------------------------
# GET /customers
# ---------------------------------------------------------

def get_customers(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetches customers.

    Endpoint
    --------
    GET /customers
    GET /customers?customer_id=CUST001

    Behavior
    --------
    - If customer_id is provided → fetch single customer
    - Else → fetch all customers ordered by creation date
    """

    customer_id = query_params.get("customer_id")
    logger.info(f"Fetching customers, customer_id: {customer_id}, type: {'single' if customer_id else 'all'}")

    if customer_id:
        query = """
        SELECT customer_id, customer_name, email, city, state, created_at
        FROM demo.customers
        WHERE customer_id = %s
        """
        params = [customer_id]
    else:
        query = """
        SELECT customer_id, customer_name, email, city, state, created_at
        FROM demo.customers
        ORDER BY created_at DESC
        """
        params = []

    logger.info(f"Executing query: {query}")

    result = invoke_query_executor(query, params, fetch=True)

    if result.get("success"):
        data = result.get("data", [])
        logger.info(f"Customers fetched successfully, customer_id: {customer_id}, count: {len(data)}")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "data": data,
                "count": len(data)
            }, default=str)
        }

    logger.error(f"Failed to fetch customers, customer_id: {customer_id}, error: {result.get('error')}")
    return {
        "statusCode": 500,
        "body": json.dumps({
            "success": False,
            "error": result.get("error", "Unknown error")
        })
    }


# ---------------------------------------------------------
# PUT /customers/{customer_id}
# ---------------------------------------------------------

def update_customer(customer_id: str, event_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates an existing customer.

    Endpoint
    --------
    PUT /customers/{customer_id}

    Notes
    -----
    - Only provided fields are updated
    - Dynamic SQL is constructed safely using placeholders
    """

    logger.info(f"Updating customer, customer_id: {customer_id}, fields: {list(event_body.keys())}")

    if not customer_id:
        logger.warning("Update attempted without customer_id")
        return {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "error": "customer_id is required"
            })
        }

    update_fields = []
    params = []

    # Build update fields dynamically
    for field in ["customer_name", "email", "city", "state"]:
        if field in event_body:
            update_fields.append(f"{field} = %s")
            params.append(event_body[field])

    if not update_fields:
        logger.warning(f"No fields to update for customer_id: {customer_id}")
        return {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "error": "No fields to update"
            })
        }

    # customer_id is always last param
    params.append(customer_id)

    query = f"""
    UPDATE demo.customers
    SET {', '.join(update_fields)}
    WHERE customer_id = %s
    RETURNING customer_id, customer_name, email, city, state, created_at
    """

    logger.info(f"Executing update query: {query}, params: {params}")

    result = invoke_query_executor(query, params, fetch=True)

    if result.get("success"):
        if result.get("rowcount", 0) == 0:
            logger.warning(f"Customer not found for update, customer_id: {customer_id}")
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "success": False,
                    "error": f"Customer {customer_id} not found"
                })
            }

        logger.info(f"Customer updated successfully, customer_id: {customer_id}")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "message": "Customer updated successfully",
                "data": result.get("data", [])[0] if result.get("data") else None
            }, default=str)
        }

    logger.error(f"Failed to update customer, customer_id: {customer_id}, error: {result.get('error')}")
    return {
        "statusCode": 500,
        "body": json.dumps({
            "success": False,
            "error": result.get("error", "Unknown error")
        })
    }


# ---------------------------------------------------------
# DELETE /customers/{customer_id}
# ---------------------------------------------------------

def delete_customer(customer_id: str) -> Dict[str, Any]:
    """
    Deletes a customer.

    Safety Checks
    -------------
    - Prevents deletion if customer has existing orders
    """

    logger.info(f"Deleting customer, customer_id: {customer_id}")

    if not customer_id:
        logger.warning("Delete attempted without customer_id")
        return {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "error": "customer_id is required"
            })
        }

    # Referential integrity check
    logger.info(f"Checking for existing orders for customer_id: {customer_id}")

    check_query = """
    SELECT COUNT(*) AS order_count
    FROM demo.orders
    WHERE customer_id = %s
    """

    check_result = invoke_query_executor(check_query, [customer_id], fetch=True)

    if check_result.get("success") and check_result.get("data"):
        order_count = check_result["data"][0].get("order_count", 0)
        logger.info(f"Order count check completed, customer_id: {customer_id}, order_count: {order_count}")

        if order_count > 0:
            logger.warning(f"Delete blocked - customer has existing orders, customer_id: {customer_id}, order_count: {order_count}")
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "success": False,
                    "error": "Cannot delete customer with existing orders"
                })
            }

    delete_query = """
    DELETE FROM demo.customers
    WHERE customer_id = %s
    """

    logger.info(f"Executing delete query: {delete_query}, customer_id: {customer_id}")

    result = invoke_query_executor(delete_query, [customer_id], fetch=False)

    if result.get("success"):
        logger.info(f"Customer deleted successfully, customer_id: {customer_id}")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "message": f"Customer {customer_id} deleted successfully"
            })
        }

    logger.error(f"Failed to delete customer, customer_id: {customer_id}, error: {result.get('error')}")
    return {
        "statusCode": 500,
        "body": json.dumps({
            "success": False,
            "error": result.get("error", "Unknown error")
        })
    }


# ---------------------------------------------------------
# Lambda Entry Point
# ---------------------------------------------------------

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda entry point.

    Responsibilities
    ----------------
    - Parse API Gateway request
    - Route based on HTTP method
    - Attach CORS headers
    - Handle unexpected exceptions safely
    """

    logger.info("Lambda invocation started")

    try:
        http_method = event.get(
            "httpMethod",
            event.get("requestContext", {}).get("http", {}).get("method")
        )

        path_parameters = event.get("pathParameters") or {}
        query_parameters = event.get("queryStringParameters") or {}

        logger.info(f"Request received, method: {http_method}, path: {event.get('path')}, query_params: {query_parameters}")

        body = {}
        if event.get("body"):
            try:
                body = json.loads(event["body"])
                logger.info(f"Request body parsed, keys: {list(body.keys())}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in request body, error: {str(e)}")
                return {
                    "statusCode": 400,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    },
                    "body": json.dumps({
                        "success": False,
                        "error": "Invalid JSON in request body"
                    })
                }

        # Route requests
        logger.info(f"Routing request, method: {http_method}")

        if http_method == "POST":
            response = create_customer(body)
        elif http_method == "GET":
            response = get_customers(query_parameters)
        elif http_method == "PUT":
            response = update_customer(
                query_parameters.get("customer_id") or query_parameters.get("id"),
                body
            )
        elif http_method == "DELETE":
            response = delete_customer(
                query_parameters.get("customer_id") or query_parameters.get("id")
            )
        else:
            logger.warning(f"Unsupported HTTP method: {http_method}")
            response = {
                "statusCode": 405,
                "body": json.dumps({
                    "success": False,
                    "error": f"Method {http_method} not allowed"
                })
            }

        # Add standard CORS headers
        response.setdefault("headers", {})
        response["headers"].update({
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        })

        logger.info(f"Lambda invocation completed, status_code: {response.get('statusCode')}")

        return response

    except Exception as e:
        logger.error(f"Unhandled exception in lambda_handler, error: {str(e)}, type: {type(e).__name__}, trace: {traceback.format_exc()}")

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "success": False,
                "error": str(e)
            })
        }