"""
AWS Bedrock Prompt Management with Simple DynamoDB Name Mapping

IMPORTANT: This uses the bedrock-agent service, not bedrock service.
AWS Bedrock has two services:
    - bedrock: For model management
    - bedrock-agent: For agents, knowledge bases, and prompt management

This simplified version uses DynamoDB ONLY for name-to-ID mapping.
All other metadata stays in Bedrock where it belongs.

Why this approach is better:
    - Single source of truth (Bedrock)
    - No data duplication
    - No synchronization issues
    - Simpler to maintain
    - Lower DynamoDB costs

DynamoDB stores ONLY:
    - prompt_name: Your human-readable name
    - prompt_id: Bedrock's generated ID
    - description: Brief description (optional, for discovery)

Everything else (variables, model, temperature, versions, etc.) is
retrieved from Bedrock when needed.

Architecture:

    Application
        |
        | Request: "customer-email"
        v
    DynamoDB (simple lookup)
        |
        | Returns: prompt_id = "abc123xyz"
        v
    AWS Bedrock
        |
        | Returns: full prompt with all metadata
        v
    Use prompt

DynamoDB Table Schema:
    Table: bedrock-prompts
    Primary Key: prompt_name (String)
    Attributes:
        - prompt_name: "customer-welcome-email"
        - prompt_id: "abc123xyz789"
        - description: "Welcome email for new customers" (optional)

That's it! Everything else comes from Bedrock.

Prerequisites:
    pip install boto3 python-dotenv

AWS Setup:
    aws dynamodb create-table \
        --table-name bedrock-prompts \
        --attribute-definitions AttributeName=prompt_name,AttributeType=S \
        --key-schema AttributeName=prompt_name,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region us-east-1
"""

import os
import json
import boto3
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()


class BedrockPromptManager:
    """
    Simplified Bedrock Prompt Manager with name-to-ID mapping.

    Uses DynamoDB only for storing the mapping between human-readable
    names and Bedrock prompt IDs. All other data stays in Bedrock.

    Benefits:
        - Single source of truth
        - No data duplication
        - Always in sync with Bedrock
        - Simpler code
        - Lower costs
    """

    def __init__(
        self,
        region_name: str = "us-east-1",
        table_name: str = "bedrock-prompts"
    ):
        """
        Initialize Bedrock Agent and DynamoDB clients.

        Args:
            region_name (str): AWS region
            table_name (str): DynamoDB table name for name mapping

        Note:
            Prompt Management is part of bedrock-agent service, not bedrock.

        DynamoDB Table Creation:
            aws dynamodb create-table \
                --table-name bedrock-prompts \
                --attribute-definitions AttributeName=prompt_name,AttributeType=S \
                --key-schema AttributeName=prompt_name,KeyType=HASH \
                --billing-mode PAY_PER_REQUEST
        """
        self.region = region_name
        self.table_name = table_name

        # Bedrock Agent client for prompt management
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=region_name)

        # Bedrock Runtime client for model invocations
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)

        # DynamoDB for name mapping only
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.mapping_table = self.dynamodb.Table(table_name)

    def create_prompt(
        self,
        name: str,
        description: str,
        prompt_text: str,
        variables: List[str],
        model_id: str = "us.amazon.nova-lite-v1:0",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Create a prompt in Bedrock and store name mapping in DynamoDB.

        This creates the prompt in Bedrock (which stores all the metadata)
        and only stores the name-to-ID mapping in DynamoDB.

        Args:
            name (str):
                Your human-readable name for this prompt
                Example: "customer-welcome-email"

            description (str):
                Brief description (stored in both Bedrock and DynamoDB)

            prompt_text (str):
                The template with {{variables}}

            variables (List[str]):
                List of variable names

            model_id (str):
                Bedrock model identifier
                Default: us.amazon.nova-lite-v1:0 (Amazon Nova Lite)

                RECOMMENDED - Amazon Nova Models (No payment/subscription needed):
                    - us.amazon.nova-lite-v1:0 (Best for starting - Fast, cheap)
                    - us.amazon.nova-micro-v1:0 (Smallest, fastest)
                    - us.amazon.nova-pro-v1:0 (Higher quality)

                Claude Models (Require marketplace subscription + payment validation):
                    - us.anthropic.claude-3-5-sonnet-20241022-v2:0 (Highest quality)
                    - anthropic.claude-3-5-haiku-20241022-v1:0 (Fast Claude)

            temperature (float):
                Randomness control (0.0 to 1.0)

            max_tokens (int):
                Response length limit

        Returns:
            Dict with success status, prompt name and ID

        Example:
            manager = BedrockPromptManager()

            result = manager.create_prompt(
                name="order-confirmation",
                description="Order confirmation email",
                prompt_text="Dear {{name}}, order {{id}} confirmed.",
                variables=["name", "id"]
            )

            # Now you can use it by name
            response = manager.invoke_prompt_by_name(
                "order-confirmation",
                {"name": "John", "id": "12345"}
            )
        """
        try:
            # Create prompt in Bedrock (single source of truth)
            variable_definitions = [{"name": var} for var in variables]

            bedrock_response = self.bedrock_agent.create_prompt(
                name=name,  # Bedrock also stores the name
                description=description,
                variants=[{
                    "name": "default",
                    "templateType": "TEXT",
                    "templateConfiguration": {
                        "text": {
                            "text": prompt_text,
                            "inputVariables": variable_definitions
                        }
                    },
                    "modelId": model_id,
                    "inferenceConfiguration": {
                        "text": {
                            "temperature": temperature,
                            "maxTokens": max_tokens
                        }
                    }
                }]
            )

            prompt_id = bedrock_response['id']

            # Store ONLY the name-to-ID mapping in DynamoDB
            self.mapping_table.put_item(
                Item={
                    'prompt_name': name,
                    'prompt_id': prompt_id,
                    'description': description  # Optional, for discovery
                }
            )

            return {
                "success": True,
                "prompt_name": name,
                "prompt_id": prompt_id,
                "message": f"Prompt '{name}' created successfully"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_prompt_id(self, name: str) -> Optional[str]:
        """
        Get Bedrock prompt ID from human-readable name.

        This is the core function - simple name-to-ID lookup.

        Args:
            name (str): Prompt name

        Returns:
            str: Bedrock prompt ID or None if not found

        Example:
            prompt_id = manager.get_prompt_id("customer-email")
            # Returns: "abc123xyz789"
        """
        try:
            response = self.mapping_table.get_item(Key={'prompt_name': name})

            if 'Item' in response:
                return response['Item']['prompt_id']
            return None

        except Exception as e:
            print(f"Error getting prompt ID: {e}")
            return None

    def get_prompt_by_name(
        self,
        name: str,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get full prompt details by name.

        This looks up the ID in DynamoDB, then fetches all details
        from Bedrock (the single source of truth).

        Args:
            name (str): Prompt name
            version (str, optional): Specific version

        Returns:
            Dict with all prompt details from Bedrock

        Example:
            prompt = manager.get_prompt_by_name("customer-email")
            print(f"Variables: {prompt['variables']}")
            print(f"Model: {prompt['model_id']}")
            print(f"Template: {prompt['prompt_text']}")
        """
        try:
            # Get ID from DynamoDB
            prompt_id = self.get_prompt_id(name)

            if not prompt_id:
                return {"success": False, "error": f"Prompt '{name}' not found"}

            # Get full details from Bedrock
            params = {"promptIdentifier": prompt_id}
            if version:
                params["promptVersion"] = version

            response = self.bedrock_agent.get_prompt(**params)

            # Extract details
            variant = response['variants'][0]
            template = variant['templateConfiguration']['text']
            inference = variant['inferenceConfiguration']['text']

            return {
                "success": True,
                "prompt_name": name,
                "prompt_id": prompt_id,
                "bedrock_name": response['name'],
                "description": response.get('description', ''),
                "prompt_text": template['text'],
                "variables": [v['name'] for v in template.get('inputVariables', [])],
                "model_id": variant['modelId'],
                "temperature": inference.get('temperature', 0.7),
                "max_tokens": inference.get('maxTokens', 1000),
                "version": response['version'],
                "arn": response['arn']
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def invoke_prompt_by_name(
        self,
        name: str,
        variables: Dict[str, str],
        version: Optional[str] = None
    ) -> str:
        """
        Invoke a prompt using its name instead of ID.

        This is the main function you'll use in production:
        1. Looks up ID in DynamoDB
        2. Gets prompt from Bedrock
        3. Fills in variables
        4. Invokes model

        Args:
            name (str): Prompt name
            variables (Dict[str, str]): Variable values
            version (str, optional): Specific version to use

        Returns:
            str: Model response

        Example:
            response = manager.invoke_prompt_by_name(
                name="welcome-email",
                variables={
                    "customer_name": "Alice",
                    "product": "Premium Plan"
                }
            )
            print(response)  # Generated email
        """
        try:
            # Get ID from DynamoDB
            prompt_id = self.get_prompt_id(name)

            if not prompt_id:
                return f"Error: Prompt '{name}' not found"

            # Get prompt from Bedrock
            params = {"promptIdentifier": prompt_id}
            if version:
                params["promptVersion"] = version

            prompt_response = self.bedrock_agent.get_prompt(**params)
            print("get_prompt response", prompt_response)

            # Extract configuration
            variant = prompt_response['variants'][0]
            template = variant['templateConfiguration']['text']
            inference = variant['inferenceConfiguration']['text']

            # Fill in variables
            prompt_text = template['text']
            for var_name, var_value in variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                prompt_text = prompt_text.replace(placeholder, str(var_value))

            # Prepare request body based on model type
            model_id = variant['modelId']

            if 'anthropic' in model_id.lower():
                # Claude models use Anthropic format
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": [{"role": "user", "content": prompt_text}],
                    "temperature": inference.get('temperature', 0.7),
                    "max_tokens": inference.get('maxTokens', 1000)
                }
            elif 'amazon.nova' in model_id.lower():
                # Amazon Nova models use different format
                request_body = {
                    "messages": [{"role": "user", "content": [{"text": prompt_text}]}],
                    "inferenceConfig": {
                        "temperature": inference.get('temperature', 0.7),
                        "max_new_tokens": inference.get('maxTokens', 1000)
                    }
                }
            else:
                # Default to Claude format for unknown models
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": [{"role": "user", "content": prompt_text}],
                    "temperature": inference.get('temperature', 0.7),
                    "max_tokens": inference.get('maxTokens', 1000)
                }

            # Invoke model
            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )

            response_body = json.loads(response['body'].read())
            print("invoke_model response", response_body)
            # Extract text based on model type
            if 'anthropic' in model_id.lower():
                # Claude response format
                return response_body['content'][0]['text']
            elif 'amazon.nova' in model_id.lower():
                # Amazon Nova response format
                return response_body['output']['message']['content'][0]['text']
            else:
                # Try Claude format first, fallback to Nova
                try:
                    return response_body['content'][0]['text']
                except (KeyError, IndexError):
                    return response_body['output']['message']['content'][0]['text']

        except Exception as e:
            error_str = str(e)

            # Provide helpful error messages for common issues
            if "AccessDeniedException" in error_str and "INVALID_PAYMENT_INSTRUMENT" in error_str:
                return (
                    "\n" + "="*80 + "\n"
                    "❌ AWS PAYMENT ISSUE DETECTED\n"
                    "="*80 + "\n\n"
                    "Your AWS account needs a valid payment method to use Bedrock models.\n\n"
                    "TO FIX THIS:\n"
                    "1. Go to: https://console.aws.amazon.com/billing/home#/paymentmethods\n"
                    "2. Add or update your credit/debit card\n"
                    "3. Wait 5-10 minutes for changes to propagate\n"
                    "4. Run this script again\n\n"
                    "NOTE: Bedrock requires a valid payment method even for free tier usage.\n\n"
                    f"Technical error: {error_str}\n"
                )
            elif "AccessDeniedException" in error_str:
                return (
                    "\n" + "="*80 + "\n"
                    "❌ MODEL ACCESS DENIED\n"
                    "="*80 + "\n\n"
                    "You need to request access to Bedrock models.\n\n"
                    "TO FIX THIS:\n"
                    "1. Go to: https://console.aws.amazon.com/bedrock/home#/modelaccess\n"
                    "2. Click 'Manage model access' or 'Enable specific models'\n"
                    "3. Select 'Anthropic' and check Claude models\n"
                    "4. Click 'Save changes'\n"
                    "5. Wait for approval (usually instant for Claude)\n"
                    "6. Run this script again\n\n"
                    f"Technical error: {error_str}\n"
                )
            elif "ResourceNotFoundException" in error_str:
                return (
                    "\n" + "="*80 + "\n"
                    "❌ MODEL NOT AVAILABLE IN YOUR REGION\n"
                    "="*80 + "\n\n"
                    "The model is not available in your AWS region.\n\n"
                    "TO FIX THIS:\n"
                    "1. Check available regions at: https://docs.aws.amazon.com/bedrock/\n"
                    "2. Try changing region_name in BedrockPromptManager() to:\n"
                    "   - 'us-east-1' (US East - N. Virginia)\n"
                    "   - 'us-west-2' (US West - Oregon)\n"
                    "   - 'eu-west-1' (Europe - Ireland)\n\n"
                    f"Technical error: {error_str}\n"
                )
            else:
                return f"\n❌ Error invoking prompt: {error_str}\n"

    def list_prompts(self) -> List[Dict[str, str]]:
        """
        List all available prompts.

        Returns basic info from DynamoDB. For full details,
        call get_prompt_by_name() on specific prompts.

        Returns:
            List of dicts with name, id, and description

        Example:
            prompts = manager.list_prompts()
            for prompt in prompts:
                print(f"{prompt['prompt_name']}: {prompt['description']}")
        """
        try:
            response = self.mapping_table.scan()
            return response.get('Items', [])

        except Exception as e:
            return [{"error": str(e)}]

    def delete_prompt(self, name: str) -> Dict[str, Any]:
        """
        Delete a prompt from both Bedrock and DynamoDB.

        Args:
            name (str): Prompt name to delete

        Returns:
            Dict with deletion status

        Example:
            result = manager.delete_prompt("old-template")
            if result['success']:
                print("Deleted successfully")
        """
        try:
            # Get ID
            prompt_id = self.get_prompt_id(name)

            if not prompt_id:
                return {"success": False, "error": f"Prompt '{name}' not found"}

            # Delete from Bedrock
            self.bedrock_agent.delete_prompt(promptIdentifier=prompt_id)

            # Delete from DynamoDB
            self.mapping_table.delete_item(Key={'prompt_name': name})

            return {
                "success": True,
                "message": f"Prompt '{name}' deleted successfully"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_prompt(
        self,
        name: str,
        prompt_text: Optional[str] = None,
        description: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update a prompt in Bedrock (updates DRAFT version).

        DynamoDB mapping stays the same (name → ID doesn't change).

        Args:
            name (str): Prompt name
            prompt_text (str, optional): New prompt template
            description (str, optional): New description
            temperature (float, optional): New temperature
            max_tokens (int, optional): New token limit

        Returns:
            Dict with update status

        Example:
            manager.update_prompt(
                name="customer-email",
                prompt_text="Updated template with {{new_variable}}"
            )
        """
        try:
            # Get ID from DynamoDB
            prompt_id = self.get_prompt_id(name)

            if not prompt_id:
                return {"success": False, "error": f"Prompt '{name}' not found"}

            # Get current prompt from Bedrock
            current = self.get_prompt_by_name(name)

            if not current['success']:
                return current

            # Build update (only changed fields)
            update_config = {
                "name": current['bedrock_name'],
                "description": description or current['description']
            }

            # Update variant
            variant = {
                "name": "default",
                "templateType": "TEXT",
                "modelId": current['model_id']
            }

            if prompt_text:
                variant["templateConfiguration"] = {
                    "text": {
                        "text": prompt_text,
                        "inputVariables": [
                            {"name": v} for v in current['variables']
                        ]
                    }
                }

            inference = {}
            if temperature is not None:
                inference["temperature"] = temperature
            if max_tokens is not None:
                inference["maxTokens"] = max_tokens

            if inference:
                variant["inferenceConfiguration"] = {"text": inference}

            update_config["variants"] = [variant]

            # Update in Bedrock
            self.bedrock_agent.update_prompt(
                promptIdentifier=prompt_id,
                **update_config
            )

            # Update description in DynamoDB if changed
            if description:
                self.mapping_table.update_item(
                    Key={'prompt_name': name},
                    UpdateExpression='SET description = :desc',
                    ExpressionAttributeValues={':desc': description}
                )

            return {
                "success": True,
                "message": f"Prompt '{name}' updated successfully"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_prompt_version(
        self,
        name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an immutable version of a prompt.

        Args:
            name (str): Prompt name
            description (str, optional): Version description

        Returns:
            Dict with version number

        Example:
            result = manager.create_prompt_version(
                name="customer-email",
                description="Tested and approved for production"
            )
            print(f"Created version {result['version']}")
        """
        try:
            # Get ID from DynamoDB
            prompt_id = self.get_prompt_id(name)

            if not prompt_id:
                return {"success": False, "error": f"Prompt '{name}' not found"}

            # Create version in Bedrock
            params = {"promptIdentifier": prompt_id}
            if description:
                params["description"] = description

            response = self.bedrock_agent.create_prompt_version(**params)

            return {
                "success": True,
                "prompt_name": name,
                "version": response['version'],
                "arn": response['arn']
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


# Example usage demonstrations

def example_1_create_and_use():
    """
    Example 1: Create prompt and use it by name.

    Shows the basic workflow with simplified DynamoDB storage.
    """
    print("\n" + "-"*80)
    print("Example 1: Create and Use Prompt by Name")
    print("-"*80)

    manager = BedrockPromptManager()

    # Create prompt
    print("\nCreating prompt...")
    result = manager.create_prompt(
        name="greeting-email",
        description="Friendly greeting email",
        prompt_text="""
        Write a warm greeting email to {{customer_name}}.
        They purchased {{product_name}}.
        Keep it under 100 words.
        """,
        variables=["customer_name", "product_name"],
        model_id="us.amazon.nova-lite-v1:0"  # Amazon Nova - No subscription needed
    )
    print("create_prompt response",result)
    if result['success']:
        print(f"✓ Created: {result['prompt_name']}")
        print(f"  Bedrock ID: {result['prompt_id']}")

        # Use by name
        print("\nInvoking by name...")
        response = manager.invoke_prompt_by_name(
            name="greeting-email",
            variables={
                "customer_name": "Alice Johnson",
                "product_name": "Premium Coffee Maker"
            }
        )

        print("\nGenerated Email:")
        print("-"*80)
        print(response)
    else:
        print(f"✗ Error: {result['error']}")


def example_2_list_and_details():
    """
    Example 2: List prompts and get details.

    Shows how to discover available prompts.
    """
    import sys

    print("\n" + "-"*80, flush=True)
    print("Example 2: List Prompts and Get Details", flush=True)
    print("-"*80, flush=True)

    manager = BedrockPromptManager()

    # List all prompts
    print("\nListing prompts from DynamoDB...", flush=True)

    try:
        prompts = manager.list_prompts()

        if not prompts:
            print("  No prompts found. Create one first with Example 1.", flush=True)
            return

        print(f"\nFound {len(prompts)} prompt(s):", flush=True)

        for prompt in prompts:
            print(f"\n  Name: {prompt['prompt_name']}", flush=True)
            print(f"  ID: {prompt['prompt_id']}", flush=True)
            print(f"  Description: {prompt.get('description', 'N/A')}", flush=True)

        # Get full details for first prompt
        if prompts:
            name = prompts[0]['prompt_name']
            print(f"\nGetting full details for '{name}' from Bedrock...", flush=True)
            details = manager.get_prompt_by_name(name)

            if details['success']:
                print(f"  Variables: {details['variables']}", flush=True)
                print(f"  Model: {details['model_id']}", flush=True)
                print(f"  Temperature: {details['temperature']}", flush=True)
                print(f"  Max tokens: {details['max_tokens']}", flush=True)
            else:
                print(f"  Error: {details['error']}", flush=True)

    except Exception as e:
        print(f"\nError in Example 2: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()


def example_3_versioning():
    """
    Example 3: Create and use versions.

    Shows version management workflow.
    """
    import sys

    print("\n" + "-"*80, flush=True)
    print("Example 3: Version Management", flush=True)
    print("-"*80, flush=True)

    manager = BedrockPromptManager()

    print("\nChecking for available prompts...", flush=True)

    try:
        prompts = manager.list_prompts()

        if not prompts:
            print("  No prompts available. Create one first with Example 1.", flush=True)
            return

        name = prompts[0]['prompt_name']
        print(f"\nFound prompt: {name}", flush=True)

        print(f"\nCreating immutable version...", flush=True)
        result = manager.create_prompt_version(
            name=name,
            description="Tested and approved"
        )

        if result['success']:
            print(f"✓ Version created: {result['version']}", flush=True)
            print(f"  ARN: {result['arn']}", flush=True)

            print(f"\nThis version is now immutable and can be used in production.", flush=True)
            print(f"To use it: invoke_prompt_by_name('{name}', variables, version='{result['version']}')", flush=True)
        else:
            print(f"✗ Error: {result['error']}", flush=True)

    except Exception as e:
        print(f"\nError in Example 3: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()


def main():
    """
    Run all examples.
    """
    print("\n" + "="*80)
    print("Simplified AWS Bedrock Prompt Management with DynamoDB")
    print("="*80)
    print("\nDynamoDB stores ONLY name-to-ID mapping.")
    print("All other data stays in Bedrock (single source of truth).\n")

    try:
        print("="*80)
        print("Interactive Mode:")
        print("  - Press Enter to run each example")
        print("  - Press Ctrl+C to skip remaining examples")
        print("  - Or run with --auto flag to skip pauses")
        print("="*80)

        print("\n[Waiting for Enter key...]", flush=True)
        input("Press Enter to start Example 1 (Create and Use) >>> ")
        print("[Starting Example 1...]", flush=True)
        example_1_create_and_use()

        print("\n[Example 1 complete]", flush=True)
        print("\n[Waiting for Enter key...]", flush=True)
        input("\n" + "-"*80 + "\nPress Enter for Example 2 (List and Details) >>> ")
        print("[Starting Example 2...]", flush=True)
        example_2_list_and_details()

        print("\n[Example 2 complete]", flush=True)
        print("\n[Waiting for Enter key...]", flush=True)
        input("\n" + "-"*80 + "\nPress Enter for Example 3 (Versioning) >>> ")
        print("[Starting Example 3...]", flush=True)
        example_3_versioning()

        print("\n" + "="*80)
        print("All examples completed")
        print("="*80)

    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("Examples interrupted by user (Ctrl+C)")
        print("="*80)
    except Exception as e:
        print(f"\n\n" + "="*80)
        print(f"Error: {str(e)}")
        print("="*80)


if __name__ == "__main__":
    import sys

    # Check for --auto flag to run without pausing
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        print("\n" + "="*80)
        print("Running in AUTO mode (no pauses)")
        print("="*80)

        try:
            example_1_create_and_use()
            print("\n" + "-"*80)
            example_2_list_and_details()
            print("\n" + "-"*80)
            example_3_versioning()
            #
            print("\n" + "="*80)
            print("All examples completed")
            print("="*80)
        except Exception as e:
            print(f"\n\nError: {str(e)}")
    else:
        # Interactive mode (default)
        main()