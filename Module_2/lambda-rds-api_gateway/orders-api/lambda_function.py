"""
Orders API Lambda Function
=========================

This Lambda function exposes REST-style endpoints for managing orders.
It performs CRUD operations on the `demo.orders` table by delegating
all database access to a shared Generic Query Executor Lambda.

Architecture Pattern
--------------------
API Gateway
    -> Orders API Lambda (this file)
        -> Generic Query Executor Lambda
            -> RDS PostgreSQL

Why this design?
----------------
- Keeps business logic separate from database access
- Ensures consistent DB access patterns across services
- Centralizes security, secrets, and connection pooling
"""

import json
import os
import boto3
import logging
import traceback
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
lambda_client = boto3.client("lambda")

# Name of the generic query executor Lambda
# Can be overridden using environment variables
QUERY_EXECUTOR_FUNCTION = os.environ.get(
    "QUERY_EXECUTOR_FUNCTION",
    "generic-query-executor"
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
    Invoke the Generic Query Executor Lambda.

    Parameters
    ----------
    query : str
        Parameterized SQL query (%s placeholders).
    params : list, optional
        Parameters for the SQL query.
    fetch : bool
        Whether results should be fetched and returned.

    Returns
    -------
    Dict[str, Any]
        Normalized response containing:
        - success
        - data (optional)
        - rowcount (optional)
        - error (optional)
    """

    logger.info(f"Invoking query executor function: {QUERY_EXECUTOR_FUNCTION}, query: {query[:100]}, params: {len(params or [])}, fetch: {fetch}")

    payload = {
        "query": query,
        "params": params or [],
        "fetch": fetch
    }

    try:
        # Synchronous invocation so caller waits for DB result
        response = lambda_client.invoke(
            FunctionName=QUERY_EXECUTOR_FUNCTION,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload)
        )

        logger.info(f"Query executor invocation successful, status code: {response.get('StatusCode')}")

        response_payload = json.loads(response["Payload"].read())

        # Handle API Gateway-style responses
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
# POST /orders
# ---------------------------------------------------------

def create_order(event_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new order.

    Endpoint
    --------
    POST /orders

    Expected Request Body
    ---------------------
    {
        "order_id": "ORD001",
        "customer_id": "CUST001",
        "status": "pending",
        "total_amount": 150.75
    }

    Business Rules
    --------------
    - customer_id must exist in customers table
    - status defaults to 'pending' if not provided
    """

    logger.info(f"Creating new order, order_id: {event_body.get('order_id')}, customer_id: {event_body.get('customer_id')}, total_amount: {event_body.get('total_amount')}")

    # Validate required fields
    required_fields = ["order_id", "customer_id", "total_amount"]
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

    # Ensure referenced customer exists (FK-style validation)
    logger.info(f"Validating customer exists, customer_id: {event_body['customer_id']}")

    check_query = """
    SELECT customer_id
    FROM demo.customers
    WHERE customer_id = %s
    """

    check_result = invoke_query_executor(
        check_query,
        [event_body["customer_id"]],
        fetch=True
    )

    if not check_result.get("success") or not check_result.get("data"):
        logger.warning(f"Customer does not exist, customer_id: {event_body['customer_id']}")
        return {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "error": f"Customer {event_body['customer_id']} does not exist"
            })
        }

    logger.info(f"Customer validation successful, customer_id: {event_body['customer_id']}")

    # Insert new order - let PostgreSQL handle the timestamp
    query = """
    INSERT INTO demo.orders
    (order_id, customer_id, order_date, status, total_amount)
    VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s)
    RETURNING order_id, customer_id, order_date, status, total_amount
    """

    params = [
        event_body["order_id"],
        event_body["customer_id"],
        event_body.get("status", "pending"),     # Default order status
        event_body["total_amount"]
    ]

    logger.info(f"Executing order insert, order_id: {event_body['order_id']}, status: {event_body.get('status', 'pending')}")

    result = invoke_query_executor(query, params, fetch=True)

    if result.get("success"):
        logger.info(f"Order created successfully, order_id: {event_body['order_id']}")
        return {
            "statusCode": 201,
            "body": json.dumps({
                "success": True,
                "message": "Order created successfully",
                "data": result.get("data", [])[0] if result.get("data") else None
            }, default=str)
        }

    logger.error(f"Failed to create order, order_id: {event_body['order_id']}, error: {result.get('error')}")
    return {
        "statusCode": 500,
        "body": json.dumps({
            "success": False,
            "error": result.get("error", "Unknown error")
        })
    }


# ---------------------------------------------------------
# GET /orders
# ---------------------------------------------------------

def get_orders(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve orders.

    Endpoint
    --------
    GET /orders
    GET /orders?order_id=ORD001
    GET /orders?customer_id=CUST001

    Query Parameters
    ----------------
    - order_id: Fetch specific order
    - customer_id: Fetch all orders for a customer
    - (no parameters): Fetch all orders

    Behavior
    --------
    - order_id → fetch specific order
    - customer_id → fetch all orders for a customer
    - no filters → fetch all orders
    """

    order_id = query_params.get("order_id")
    customer_id = query_params.get("customer_id")

    logger.info(f"Fetching orders, order_id: {order_id}, customer_id: {customer_id}")

    if order_id:
        query = """
        SELECT o.order_id, o.customer_id, o.order_date, o.status, o.total_amount,
               c.customer_name, c.email
        FROM demo.orders o
        JOIN demo.customers c ON o.customer_id = c.customer_id
        WHERE o.order_id = %s
        """
        params = [order_id]

    elif customer_id:
        query = """
        SELECT o.order_id, o.customer_id, o.order_date, o.status, o.total_amount,
               c.customer_name, c.email
        FROM demo.orders o
        JOIN demo.customers c ON o.customer_id = c.customer_id
        WHERE o.customer_id = %s
        ORDER BY o.order_date DESC
        """
        params = [customer_id]

    else:
        query = """
        SELECT o.order_id, o.customer_id, o.order_date, o.status, o.total_amount,
               c.customer_name, c.email
        FROM demo.orders o
        JOIN demo.customers c ON o.customer_id = c.customer_id
        ORDER BY o.order_date DESC
        """
        params = []

    logger.info(f"Executing query: {query}")

    result = invoke_query_executor(query, params, fetch=True)

    if result.get("success"):
        data = result.get("data", [])
        logger.info(f"Orders fetched successfully, order_id: {order_id}, customer_id: {customer_id}, count: {len(data)}")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "data": data,
                "count": len(data)
            }, default=str)
        }

    logger.error(f"Failed to fetch orders, order_id: {order_id}, customer_id: {customer_id}, error: {result.get('error')}")
    return {
        "statusCode": 500,
        "body": json.dumps({
            "success": False,
            "error": result.get("error", "Unknown error")
        })
    }


# ---------------------------------------------------------
# PUT /orders/{order_id}
# ---------------------------------------------------------

def update_order(order_id: str, event_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing order.

    Endpoint
    --------
    PUT /orders?order_id=ORD001

    Query Parameters
    ----------------
    - order_id: Required - ID of the order to update

    Updatable Fields
    ----------------
    - status
    - total_amount
    """

    logger.info(f"Updating order, order_id: {order_id}, fields: {list(event_body.keys())}")

    if not order_id:
        logger.warning("Update attempted without order_id")
        return {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "error": "order_id is required"
            })
        }

    update_fields = []
    params = []

    # Build dynamic update query safely
    if "status" in event_body:
        update_fields.append("status = %s")
        params.append(event_body["status"])

    if "total_amount" in event_body:
        update_fields.append("total_amount = %s")
        params.append(event_body["total_amount"])

    if not update_fields:
        logger.warning(f"No fields to update for order_id: {order_id}")
        return {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "error": "No fields to update"
            })
        }

    # order_id used in WHERE clause
    params.append(order_id)

    query = f"""
    UPDATE demo.orders
    SET {', '.join(update_fields)}
    WHERE order_id = %s
    RETURNING order_id, customer_id, order_date, status, total_amount
    """

    logger.info(f"Executing update query: {query}, params: {params}")

    result = invoke_query_executor(query, params, fetch=True)

    if result.get("success"):
        if result.get("rowcount", 0) == 0:
            logger.warning(f"Order not found for update, order_id: {order_id}")
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "success": False,
                    "error": f"Order {order_id} not found"
                })
            }

        logger.info(f"Order updated successfully, order_id: {order_id}")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "message": "Order updated successfully",
                "data": result.get("data", [])[0] if result.get("data") else None
            }, default=str)
        }

    logger.error(f"Failed to update order, order_id: {order_id}, error: {result.get('error')}")
    return {
        "statusCode": 500,
        "body": json.dumps({
            "success": False,
            "error": result.get("error", "Unknown error")
        })
    }


# ---------------------------------------------------------
# DELETE /orders/{order_id}
# ---------------------------------------------------------

def delete_order(order_id: str) -> Dict[str, Any]:
    """
    Delete an order.

    Endpoint
    --------
    DELETE /orders?order_id=ORD001

    Query Parameters
    ----------------
    - order_id: Required - ID of the order to delete
    """

    logger.info(f"Deleting order, order_id: {order_id}")

    if not order_id:
        logger.warning("Delete attempted without order_id")
        return {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "error": "order_id is required"
            })
        }

    query = """
    DELETE FROM demo.orders
    WHERE order_id = %s
    """

    logger.info(f"Executing delete query: {query}, order_id: {order_id}")

    result = invoke_query_executor(query, [order_id], fetch=False)

    if result.get("success"):
        if result.get("rowcount", 0) == 0:
            logger.warning(f"Order not found for deletion, order_id: {order_id}")
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "success": False,
                    "error": f"Order {order_id} not found"
                })
            }

        logger.info(f"Order deleted successfully, order_id: {order_id}")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "message": f"Order {order_id} deleted successfully"
            })
        }

    logger.error(f"Failed to delete order, order_id: {order_id}, error: {result.get('error')}")
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
    - Handle unexpected failures safely
    """

    logger.info("Lambda invocation started")

    try:
        http_method = event.get(
            "httpMethod",
            event.get("requestContext", {}).get("http", {}).get("method")
        )

        path_parameters = event.get("pathParameters") or {}
        query_parameters = event.get("queryStringParameters") or {}

        logger.info(f"Request received, method: {http_method}, path: {event.get('path')}, query_params: {query_parameters}, path_params: {path_parameters}")

        body = {}
        if event.get("body"):
            try:
                body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
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

        # Route request
        logger.info(f"Routing request, method: {http_method}")

        if http_method == "POST":
            response = create_order(body)
        elif http_method == "GET":
            response = get_orders(query_parameters)
        elif http_method == "PUT":
            response = update_order(
                query_parameters.get("order_id") or query_parameters.get("id"),
                body
            )
        elif http_method == "DELETE":
            response = delete_order(
                query_parameters.get("order_id") or query_parameters.get("id")
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

        # Standard CORS headers
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