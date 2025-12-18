"""
Generic Query Executor Lambda Function
This Lambda function executes SQL queries on RDS PostgreSQL database.
It's called by other Lambda functions to perform database operations.
"""
import json
import os
import psycopg2
from psycopg2 import pool
from typing import Dict, Any, List, Optional

# Database connection pool
connection_pool = None

def get_db_connection():
    """
    Get database connection from pool or create new one.
    Uses environment variables for database configuration.
    """
    global connection_pool
    
    if connection_pool is None:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 10,  # min and max connections
            host=os.environ['DB_HOST'],
            database=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            port=os.environ.get('DB_PORT', '5432')
        )
    
    return connection_pool.getconn()

def return_db_connection(conn):
    """Return connection to pool"""
    global connection_pool
    if connection_pool:
        connection_pool.putconn(conn)

def execute_query(query: str, params: Optional[tuple] = None, fetch: bool = True) -> Dict[str, Any]:
    """
    Execute SQL query and return results.
    
    Args:
        query: SQL query to execute
        params: Query parameters (for parameterized queries)
        fetch: Whether to fetch results (True for SELECT, False for INSERT/UPDATE/DELETE)
    
    Returns:
        Dict with success status, data, and row count
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Execute query with parameters
        cursor.execute(query, params)
        
        result = {
            'success': True,
            'rowcount': cursor.rowcount
        }
        
        if fetch and cursor.description:
            # Fetch results for SELECT queries
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            result['data'] = [dict(zip(columns, row)) for row in rows]
        else:
            # For INSERT/UPDATE/DELETE, commit the transaction
            conn.commit()
            result['data'] = None
        
        return result
        
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        
        return {
            'success': False,
            'error': str(e),
            'error_code': e.pgcode if hasattr(e, 'pgcode') else None
        }
        
    except Exception as e:
        if conn:
            conn.rollback()
        
        return {
            'success': False,
            'error': str(e)
        }
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            return_db_connection(conn)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler function.
    
    Expected event structure:
    {
        "query": "SELECT * FROM demo.customers WHERE customer_id = %s",
        "params": ["CUST001"],  # Optional
        "fetch": true  # Optional, default true
    }
    """
    try:
        # Parse event (might be from API Gateway or direct invocation)
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        # Extract query parameters
        query = body.get('query')
        params = body.get('params')
        fetch = body.get('fetch', True)
        
        # Validate input
        if not query:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Query is required'
                })
            }
        
        # Convert params list to tuple if provided
        if params and isinstance(params, list):
            params = tuple(params)
        
        # Execute query
        result = execute_query(query, params, fetch)
        
        # Return response
        return {
            'statusCode': 200 if result['success'] else 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result, default=str)  # default=str handles datetime serialization
        }
        
    except json.JSONDecodeError as e:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': f'Invalid JSON: {str(e)}'
            })
        }
        
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
