"""
Orders API Lambda Function
Handles CRUD operations for orders table by invoking generic query executor.
"""
import json
import os
import boto3
from typing import Dict, Any
from datetime import datetime

# Initialize Lambda client
lambda_client = boto3.client('lambda')

# Generic query executor Lambda function name
QUERY_EXECUTOR_FUNCTION = os.environ.get('QUERY_EXECUTOR_FUNCTION', 'generic-query-executor')

def invoke_query_executor(query: str, params: list = None, fetch: bool = True) -> Dict[str, Any]:
    """
    Invoke the generic query executor Lambda function.
    """
    payload = {
        'query': query,
        'params': params or [],
        'fetch': fetch
    }
    
    response = lambda_client.invoke(
        FunctionName=QUERY_EXECUTOR_FUNCTION,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    response_payload = json.loads(response['Payload'].read())
    
    # Parse the body if it's a string (API Gateway format)
    if isinstance(response_payload.get('body'), str):
        return json.loads(response_payload['body'])
    
    return response_payload

def create_order(event_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /orders - Create new order
    Expected body: {
        "order_id": "ORD001",
        "customer_id": "CUST001",
        "status": "pending",
        "total_amount": 150.75
    }
    """
    # Validate required fields
    required_fields = ['order_id', 'customer_id', 'total_amount']
    for field in required_fields:
        if field not in event_body:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': f'Missing required field: {field}'
                })
            }
    
    # Verify customer exists
    check_query = """
    SELECT customer_id FROM demo.customers WHERE customer_id = %s
    """
    
    check_result = invoke_query_executor(check_query, [event_body['customer_id']], fetch=True)
    
    if not check_result.get('success') or not check_result.get('data'):
        return {
            'statusCode': 400,
            'body': json.dumps({
                'success': False,
                'error': f"Customer {event_body['customer_id']} does not exist"
            })
        }
    
    # Prepare INSERT query
    query = """
    INSERT INTO demo.orders 
    (order_id, customer_id, order_date, status, total_amount)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING order_id, customer_id, order_date, status, total_amount
    """
    
    params = [
        event_body['order_id'],
        event_body['customer_id'],
        datetime.utcnow(),
        event_body.get('status', 'pending'),
        event_body['total_amount']
    ]
    
    # Execute query
    result = invoke_query_executor(query, params, fetch=True)
    
    if result.get('success'):
        return {
            'statusCode': 201,
            'body': json.dumps({
                'success': True,
                'message': 'Order created successfully',
                'data': result.get('data', [])[0] if result.get('data') else None
            }, default=str)
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': result.get('error', 'Unknown error')
            })
        }

def get_orders(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    GET /orders - Get all orders or filter by order_id or customer_id
    Query params: ?order_id=ORD001 or ?customer_id=CUST001
    """
    order_id = query_params.get('order_id')
    customer_id = query_params.get('customer_id')
    
    if order_id:
        # Get specific order
        query = """
        SELECT o.order_id, o.customer_id, o.order_date, o.status, o.total_amount,
               c.customer_name, c.email
        FROM demo.orders o
        JOIN demo.customers c ON o.customer_id = c.customer_id
        WHERE o.order_id = %s
        """
        params = [order_id]
    elif customer_id:
        # Get orders for specific customer
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
        # Get all orders
        query = """
        SELECT o.order_id, o.customer_id, o.order_date, o.status, o.total_amount,
               c.customer_name, c.email
        FROM demo.orders o
        JOIN demo.customers c ON o.customer_id = c.customer_id
        ORDER BY o.order_date DESC
        """
        params = []
    
    result = invoke_query_executor(query, params, fetch=True)
    
    if result.get('success'):
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'data': result.get('data', []),
                'count': len(result.get('data', []))
            }, default=str)
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': result.get('error', 'Unknown error')
            })
        }

def update_order(order_id: str, event_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    PUT /orders/{order_id} - Update order
    Expected body: {
        "status": "shipped",
        "total_amount": 175.99
    }
    """
    if not order_id:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'success': False,
                'error': 'order_id is required'
            })
        }
    
    # Build dynamic UPDATE query
    update_fields = []
    params = []
    
    if 'status' in event_body:
        update_fields.append('status = %s')
        params.append(event_body['status'])
    
    if 'total_amount' in event_body:
        update_fields.append('total_amount = %s')
        params.append(event_body['total_amount'])
    
    if not update_fields:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'success': False,
                'error': 'No fields to update'
            })
        }
    
    params.append(order_id)  # Add order_id for WHERE clause
    
    query = f"""
    UPDATE demo.orders
    SET {', '.join(update_fields)}
    WHERE order_id = %s
    RETURNING order_id, customer_id, order_date, status, total_amount
    """
    
    result = invoke_query_executor(query, params, fetch=True)
    
    if result.get('success'):
        if result.get('rowcount', 0) == 0:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'success': False,
                    'error': f'Order {order_id} not found'
                })
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Order updated successfully',
                'data': result.get('data', [])[0] if result.get('data') else None
            }, default=str)
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': result.get('error', 'Unknown error')
            })
        }

def delete_order(order_id: str) -> Dict[str, Any]:
    """
    DELETE /orders/{order_id} - Delete order
    """
    if not order_id:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'success': False,
                'error': 'order_id is required'
            })
        }
    
    # Delete order
    query = """
    DELETE FROM demo.orders
    WHERE order_id = %s
    """
    
    result = invoke_query_executor(query, [order_id], fetch=False)
    
    if result.get('success'):
        if result.get('rowcount', 0) == 0:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'success': False,
                    'error': f'Order {order_id} not found'
                })
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': f'Order {order_id} deleted successfully'
            })
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': result.get('error', 'Unknown error')
            })
        }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler - routes requests based on HTTP method.
    """
    try:
        # Extract HTTP method and path parameters
        http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method'))
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        # Parse body if present
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Invalid JSON in request body'
                    })
                }
        
        # Route based on HTTP method
        if http_method == 'POST':
            response = create_order(body)
        elif http_method == 'GET':
            response = get_orders(query_parameters)
        elif http_method == 'PUT':
            order_id = path_parameters.get('order_id') or path_parameters.get('id')
            response = update_order(order_id, body)
        elif http_method == 'DELETE':
            order_id = path_parameters.get('order_id') or path_parameters.get('id')
            response = delete_order(order_id)
        else:
            response = {
                'statusCode': 405,
                'body': json.dumps({
                    'success': False,
                    'error': f'Method {http_method} not allowed'
                })
            }
        
        # Add CORS headers
        if 'headers' not in response:
            response['headers'] = {}
        
        response['headers'].update({
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        })
        
        return response
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
