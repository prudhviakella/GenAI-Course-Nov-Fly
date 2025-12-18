"""
Customers API Lambda Function
Handles CRUD operations for customers table by invoking generic query executor.
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

def create_customer(event_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /customers - Create new customer
    Expected body: {
        "customer_id": "CUST001",
        "customer_name": "John Doe",
        "email": "john@example.com",
        "city": "New York",
        "state": "NY"
    }
    """
    # Validate required fields
    required_fields = ['customer_id', 'customer_name', 'email']
    for field in required_fields:
        if field not in event_body:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': f'Missing required field: {field}'
                })
            }
    
    # Prepare INSERT query
    query = """
    INSERT INTO demo.customers 
    (customer_id, customer_name, email, city, state, created_at)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING customer_id, customer_name, email, city, state, created_at
    """
    
    params = [
        event_body['customer_id'],
        event_body['customer_name'],
        event_body['email'],
        event_body.get('city'),
        event_body.get('state'),
        datetime.utcnow()
    ]
    
    # Execute query
    result = invoke_query_executor(query, params, fetch=True)
    
    if result.get('success'):
        return {
            'statusCode': 201,
            'body': json.dumps({
                'success': True,
                'message': 'Customer created successfully',
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

def get_customers(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    GET /customers - Get all customers or filter by customer_id
    Query params: ?customer_id=CUST001
    """
    customer_id = query_params.get('customer_id')
    
    if customer_id:
        # Get specific customer
        query = """
        SELECT customer_id, customer_name, email, city, state, created_at
        FROM demo.customers
        WHERE customer_id = %s
        """
        params = [customer_id]
    else:
        # Get all customers
        query = """
        SELECT customer_id, customer_name, email, city, state, created_at
        FROM demo.customers
        ORDER BY created_at DESC
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

def update_customer(customer_id: str, event_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    PUT /customers/{customer_id} - Update customer
    Expected body: {
        "customer_name": "John Doe Updated",
        "email": "john.updated@example.com",
        "city": "Boston",
        "state": "MA"
    }
    """
    if not customer_id:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'success': False,
                'error': 'customer_id is required'
            })
        }
    
    # Build dynamic UPDATE query
    update_fields = []
    params = []
    
    if 'customer_name' in event_body:
        update_fields.append('customer_name = %s')
        params.append(event_body['customer_name'])
    
    if 'email' in event_body:
        update_fields.append('email = %s')
        params.append(event_body['email'])
    
    if 'city' in event_body:
        update_fields.append('city = %s')
        params.append(event_body['city'])
    
    if 'state' in event_body:
        update_fields.append('state = %s')
        params.append(event_body['state'])
    
    if not update_fields:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'success': False,
                'error': 'No fields to update'
            })
        }
    
    params.append(customer_id)  # Add customer_id for WHERE clause
    
    query = f"""
    UPDATE demo.customers
    SET {', '.join(update_fields)}
    WHERE customer_id = %s
    RETURNING customer_id, customer_name, email, city, state, created_at
    """
    
    result = invoke_query_executor(query, params, fetch=True)
    
    if result.get('success'):
        if result.get('rowcount', 0) == 0:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'success': False,
                    'error': f'Customer {customer_id} not found'
                })
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Customer updated successfully',
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

def delete_customer(customer_id: str) -> Dict[str, Any]:
    """
    DELETE /customers/{customer_id} - Delete customer
    """
    if not customer_id:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'success': False,
                'error': 'customer_id is required'
            })
        }
    
    # Check if customer has orders
    check_query = """
    SELECT COUNT(*) as order_count
    FROM demo.orders
    WHERE customer_id = %s
    """
    
    check_result = invoke_query_executor(check_query, [customer_id], fetch=True)
    
    if check_result.get('success') and check_result.get('data'):
        order_count = check_result['data'][0].get('order_count', 0)
        
        if order_count > 0:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': f'Cannot delete customer. {order_count} orders exist for this customer.'
                })
            }
    
    # Delete customer
    query = """
    DELETE FROM demo.customers
    WHERE customer_id = %s
    """
    
    result = invoke_query_executor(query, [customer_id], fetch=False)
    
    if result.get('success'):
        if result.get('rowcount', 0) == 0:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'success': False,
                    'error': f'Customer {customer_id} not found'
                })
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': f'Customer {customer_id} deleted successfully'
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
            response = create_customer(body)
        elif http_method == 'GET':
            response = get_customers(query_parameters)
        elif http_method == 'PUT':
            customer_id = path_parameters.get('customer_id') or path_parameters.get('id')
            response = update_customer(customer_id, body)
        elif http_method == 'DELETE':
            customer_id = path_parameters.get('customer_id') or path_parameters.get('id')
            response = delete_customer(customer_id)
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
