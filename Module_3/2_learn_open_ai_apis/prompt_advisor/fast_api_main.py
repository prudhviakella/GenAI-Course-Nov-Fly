"""
FastAPI REST API for Prompt Advisor
====================================

This module provides a complete REST API for the Prompt Advisor system.
It allows users to analyze business problems and receive AI-powered recommendations
for prompt templates and techniques through HTTP endpoints.

Features:
    - Fast mode: Quick single recommendation
    - Deep mode: Multiple options with LLM judge evaluation
    - Reference endpoints for browsing templates and techniques
    - Automatic Unicode handling and text cleaning
    - CORS enabled for frontend integration
    - OpenAPI documentation at /docs

Author: Prompt Advisor Team
Version: 1.0.0
"""

# ============================================================================
# IMPORTS
# ============================================================================

# FastAPI core components for building the REST API
from fastapi import FastAPI, HTTPException, Header
# CORS middleware to enable cross-origin requests from web browsers
from fastapi.middleware.cors import CORSMiddleware
# Pydantic for data validation and serialization
from pydantic import BaseModel, Field
# Type hints for better code quality and IDE support
from typing import Optional, Dict, Any
# OS utilities for environment variable access
import os
# Import the core prompt advisor functionality
from prompt_advisor import PromptAdvisor, TEMPLATES, TECHNIQUES


# ============================================================================
# FASTAPI APPLICATION INITIALIZATION
# ============================================================================

# Create the FastAPI application instance with metadata
# This metadata appears in the auto-generated documentation
app = FastAPI(
    title="Prompt Advisor API",  # API name shown in documentation
    description="Analyze business problems and get AI-powered prompt template and technique recommendations",
    version="1.0.0"  # API version for tracking changes
)

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# Add CORS (Cross-Origin Resource Sharing) middleware
# This allows the API to be called from web browsers on different domains
# Essential for frontend applications that need to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin (use specific domains in production)
    allow_credentials=True,  # Allow cookies and authentication headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers in requests
)


# ============================================================================
# PYDANTIC MODELS (REQUEST/RESPONSE SCHEMAS)
# ============================================================================

class AnalyzeRequest(BaseModel):
    """
    Request model for the analyze endpoint.
    
    This Pydantic model defines the structure and validation rules for
    incoming analysis requests. FastAPI automatically validates requests
    against this schema and returns 422 errors for invalid data.
    
    Attributes:
        problem (str): The business problem to analyze (minimum 10 characters).
                      This ensures users provide meaningful problem descriptions.
        mode (str): Analysis mode - either 'fast' or 'deep'.
                   Fast mode gives quick single recommendation.
                   Deep mode generates multiple options with LLM judge.
                   Defaults to 'fast' for backwards compatibility.
        model (str): OpenAI model to use for analysis.
                    Options: gpt-4o, gpt-4o-mini, gpt-3.5-turbo, etc.
                    Defaults to 'gpt-4o' for best quality.
    
    Example:
        {
            "problem": "Build a recommendation system for products",
            "mode": "fast",
            "model": "gpt-4o"
        }
    """
    # Problem description field with validation
    # Field(...) means this is required (no default value)
    # min_length ensures meaningful input
    problem: str = Field(
        ...,  # Required field indicator
        description="Business problem to analyze",
        min_length=10  # Minimum 10 characters to ensure quality input
    )
    
    # Analysis mode field with default value
    mode: str = Field(
        default="fast",  # Default to fast mode if not specified
        description="Analysis mode: 'fast' or 'deep'"
    )
    
    # OpenAI model selection with default
    model: str = Field(
        default="gpt-4o",  # Default to best model
        description="OpenAI model to use"
    )
    
    # Configuration class for Pydantic model
    class Config:
        # Example data shown in API documentation
        json_schema_extra = {
            "example": {
                "problem": "Build a recommendation system for e-commerce products based on user behavior",
                "mode": "fast",
                "model": "gpt-4o"
            }
        }


class HealthResponse(BaseModel):
    """
    Response model for the health check endpoint.
    
    Provides information about API status and available resources.
    Useful for monitoring, load balancers, and orchestration systems.
    
    Attributes:
        status (str): Current API status (e.g., "healthy", "degraded")
        version (str): API version number
        templates_count (int): Number of available prompt templates
        techniques_count (int): Number of available prompt techniques
    """
    status: str  # API operational status
    version: str  # API version for compatibility checking
    templates_count: int  # Total templates available
    techniques_count: int  # Total techniques available


class TemplateInfo(BaseModel):
    """
    Schema for template information.
    
    Defines the structure of template data returned by the API.
    Used for type validation and documentation.
    
    Attributes:
        name (str): Full name of the template
        acronym (str): Short acronym (e.g., R-T-F, DREAM)
        components (list): List of template components/sections
        best_for (str): Description of ideal use cases
    """
    name: str  # Full descriptive name
    acronym: str  # Short memorable identifier
    components: list  # List of template parts
    best_for: str  # When to use this template


class TechniqueInfo(BaseModel):
    """
    Schema for technique information.
    
    Defines the structure of technique data returned by the API.
    
    Attributes:
        name (str): Full name of the technique
        best_for (str): Description of ideal use cases
    """
    name: str  # Technique name
    best_for: str  # When to use this technique


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_advisor(api_key: str, model: str = "gpt-4o") -> PromptAdvisor:
    """
    Create and return a PromptAdvisor instance with the given API key.
    
    This factory function initializes the advisor with proper error handling.
    It ensures the API key is valid and the advisor can be created before
    processing any analysis requests.
    
    Args:
        api_key (str): OpenAI API key for making API calls.
                      Must be a valid API key starting with 'sk-'.
        model (str): OpenAI model to use for analysis.
                    Defaults to 'gpt-4o' for best results.
    
    Returns:
        PromptAdvisor: Initialized advisor instance ready for analysis.
    
    Raises:
        HTTPException: 401 if API key is missing
                      500 if advisor initialization fails
    
    Example:
        advisor = get_advisor("sk-proj-xxx", "gpt-4o")
        result = advisor.analyze_problem("My problem", mode="fast")
    """
    # Validate that API key is provided
    if not api_key:
        # Raise 401 Unauthorized if no key provided
        raise HTTPException(
            status_code=401,
            detail="API key is required"
        )
    
    # Attempt to create the advisor instance
    try:
        # Initialize PromptAdvisor with the provided credentials
        return PromptAdvisor(api_key=api_key, model=model)
    except Exception as e:
        # If initialization fails, return 500 Internal Server Error
        # This could happen if the API key is invalid or OpenAI is unreachable
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize advisor: {str(e)}"
        )


# ============================================================================
# API ENDPOINTS - INFORMATION
# ============================================================================

@app.get("/", tags=["Info"])
async def root():
    """
    Root endpoint providing API information and available endpoints.
    
    This is the landing page of the API. It provides an overview of
    available endpoints and links to documentation. Useful for API discovery.
    
    Returns:
        dict: JSON object with API metadata and endpoint list
    
    Status Codes:
        200: Success - returns API information
    
    Example Response:
        {
            "message": "Prompt Advisor API",
            "version": "1.0.0",
            "docs": "/docs",
            "endpoints": {...}
        }
    """
    # Return a dictionary that FastAPI automatically converts to JSON
    return {
        "message": "Prompt Advisor API",  # API name
        "version": "1.0.0",  # Current version
        "docs": "/docs",  # Link to interactive documentation
        "endpoints": {
            # Map of endpoint names to their URLs
            "analyze": "/api/v1/analyze",
            "templates": "/api/v1/templates",
            "techniques": "/api/v1/techniques",
            "health": "/health"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Info"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    This endpoint is used by:
    - Monitoring systems to check if the API is running
    - Load balancers to determine if traffic can be routed to this instance
    - Orchestration platforms (Kubernetes, ECS) for health checks
    - DevOps teams for troubleshooting
    
    Returns:
        HealthResponse: Object with status and resource counts
    
    Status Codes:
        200: API is healthy and operational
    
    Example Response:
        {
            "status": "healthy",
            "version": "1.0.0",
            "templates_count": 10,
            "techniques_count": 7
        }
    """
    # Return health status with current counts of available resources
    return {
        "status": "healthy",  # Operational status
        "version": "1.0.0",  # API version
        "templates_count": len(TEMPLATES),  # Number of templates loaded
        "techniques_count": len(TECHNIQUES)  # Number of techniques loaded
    }


# ============================================================================
# API ENDPOINTS - REFERENCE DATA
# ============================================================================

@app.get("/api/v1/templates", tags=["Reference"])
async def get_templates():
    """
    Get list of all available prompt templates.
    
    This endpoint returns complete information about all prompt templates
    in the system. Users can browse templates to understand what's available
    before making analysis requests.
    
    Returns:
        dict: Object containing count and list of all templates
    
    Status Codes:
        200: Success - returns template list
    
    Example Response:
        {
            "count": 10,
            "templates": [
                {
                    "name": "Role-Task-Format",
                    "acronym": "R-T-F",
                    "components": ["Role", "Task", "Format"],
                    "use_cases": ["Creative content", "Marketing"],
                    "best_for": "Creative tasks"
                },
                ...
            ]
        }
    """
    # Return count and list of all templates
    return {
        "count": len(TEMPLATES),  # Total number of templates
        "templates": [
            # List comprehension to convert each template to a dictionary
            {
                "name": t.name,  # Full template name
                "acronym": t.acronym,  # Short identifier
                "components": t.components,  # Template sections
                "use_cases": t.use_cases,  # Example use cases
                "best_for": t.best_for  # Ideal scenarios
            }
            for t in TEMPLATES  # Iterate over all template objects
        ]
    }


@app.get("/api/v1/techniques", tags=["Reference"])
async def get_techniques():
    """
    Get list of all available prompt techniques.
    
    This endpoint returns complete information about all prompt techniques
    in the system. Techniques are different approaches to structuring prompts
    (e.g., Chain of Thought, Tree of Thought, Self-Consistency).
    
    Returns:
        dict: Object containing count and list of all techniques
    
    Status Codes:
        200: Success - returns technique list
    
    Example Response:
        {
            "count": 7,
            "techniques": [
                {
                    "name": "Chain of Thought Prompting",
                    "description": "Breaks down complex problems...",
                    "use_cases": ["Math", "Logic"],
                    "best_for": "Multi-step reasoning"
                },
                ...
            ]
        }
    """
    # Return count and list of all techniques
    return {
        "count": len(TECHNIQUES),  # Total number of techniques
        "techniques": [
            # List comprehension to convert each technique to a dictionary
            {
                "name": t.name,  # Technique name
                "description": t.description,  # What it does
                "use_cases": t.use_cases,  # Example scenarios
                "best_for": t.best_for  # Ideal use cases
            }
            for t in TECHNIQUES  # Iterate over all technique objects
        ]
    }


# ============================================================================
# API ENDPOINTS - ANALYSIS (MAIN FUNCTIONALITY)
# ============================================================================

@app.post("/api/v1/analyze", tags=["Analysis"])
async def analyze_problem(
    request: AnalyzeRequest,  # Request body validated by Pydantic
    x_api_key: Optional[str] = Header(None, description="OpenAI API Key")  # API key from header
):
    """
    Analyze a business problem and get prompt template/technique recommendations.
    
    This is the main analysis endpoint. It accepts a business problem description
    and returns AI-powered recommendations for the best prompt template and technique
    to use. Supports both fast and deep analysis modes.
    
    Args:
        request (AnalyzeRequest): Request body containing:
            - problem: Business problem to analyze (required, min 10 chars)
            - mode: 'fast' or 'deep' (optional, default 'fast')
            - model: OpenAI model to use (optional, default 'gpt-4o')
        x_api_key (str, optional): OpenAI API key from X-API-Key header
    
    Returns:
        dict: Analysis results including:
            - problem_analysis: Characteristics of the problem
            - recommended_template: Best template with reasoning
            - recommended_technique: Best technique with reasoning
            - example_prompt: Example of how to use them together
            - metadata: Information about the analysis request
            - (deep mode only) all_options: All options evaluated
            - (deep mode only) evaluations: Scores for each option
    
    Raises:
        HTTPException: 
            - 400: Invalid mode (must be 'fast' or 'deep')
            - 401: Missing API key
            - 422: Invalid request format
            - 500: Analysis failed or OpenAI API error
    
    Status Codes:
        200: Success - analysis completed
        400: Bad Request - invalid parameters
        401: Unauthorized - missing API key
        422: Unprocessable Entity - validation error
        500: Internal Server Error - analysis failed
    
    Example Request (Fast Mode):
        POST /api/v1/analyze
        Headers: X-API-Key: sk-xxx
        Body: {
            "problem": "Build a recommendation system",
            "mode": "fast"
        }
    
    Example Request (Deep Mode):
        POST /api/v1/analyze
        Headers: X-API-Key: sk-xxx
        Body: {
            "problem": "Design complex AI system",
            "mode": "deep"
        }
    
    Example Response (Fast Mode):
        {
            "mode": "fast",
            "recommended_template": {
                "acronym": "D-R-E-A-M",
                "name": "Define-Research-Execute-Analyse-Measure"
            },
            "recommended_technique": {
                "name": "Chain of Thought Prompting"
            },
            "example_prompt": "...",
            "metadata": {
                "mode": "fast",
                "model": "gpt-4o",
                "input_length": 30
            }
        }
    
    Example Response (Deep Mode):
        {
            "mode": "deep",
            "all_options": [...],
            "evaluations": [...],
            "winner_reasoning": "...",
            ...
        }
    """
    # ========================================================================
    # STEP 1: VALIDATE REQUEST MODE
    # ========================================================================
    # Ensure the mode is either 'fast' or 'deep'
    # This prevents invalid modes that would cause errors later
    if request.mode not in ["fast", "deep"]:
        # Raise 400 Bad Request with clear error message
        raise HTTPException(
            status_code=400,
            detail="Mode must be 'fast' or 'deep'"
        )
    
    # ========================================================================
    # STEP 2: GET AND VALIDATE API KEY
    # ========================================================================
    # Try to get API key from header first, then fall back to environment variable
    # This provides flexibility in how users authenticate
    api_key = x_api_key or os.getenv("OPENAI_API_KEY")
    
    # If no API key found, return 401 Unauthorized
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="OpenAI API key required. Provide via X-API-Key header or OPENAI_API_KEY environment variable"
        )
    
    # ========================================================================
    # STEP 3: PERFORM ANALYSIS
    # ========================================================================
    try:
        # Create an advisor instance with the provided API key and model
        advisor = get_advisor(api_key, request.model)
        
        # Call the core analysis function
        # This is where the AI magic happens
        # The advisor will:
        # - Clean the problem text (handle Unicode)
        # - Call OpenAI API (1 call for fast, 2 calls for deep)
        # - Generate recommendations
        result = advisor.analyze_problem(request.problem, mode=request.mode)
        
        # Check if the analysis returned an error
        # The advisor returns errors as {"error": "message"} instead of raising exceptions
        if "error" in result:
            # Convert error to HTTP 500 response
            raise HTTPException(status_code=500, detail=result["error"])
        
        # ====================================================================
        # STEP 4: ADD METADATA TO RESPONSE
        # ====================================================================
        # Enhance the response with information about the request
        # This helps users track and debug their requests
        result["metadata"] = {
            "mode": request.mode,  # Which mode was used
            "model": request.model,  # Which OpenAI model was used
            "input_length": len(request.problem)  # Length of input (for debugging)
        }
        
        # Return the complete result
        # FastAPI automatically converts this to JSON
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        # These are already properly formatted errors
        raise
    except Exception as e:
        # Catch any unexpected errors and convert to HTTP 500
        # This prevents the API from crashing and provides useful error messages
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


# ============================================================================
# API ENDPOINTS - CONVENIENCE ENDPOINTS
# ============================================================================

@app.post("/api/v1/analyze/fast", tags=["Analysis"])
async def analyze_fast(
    request: AnalyzeRequest,  # Request body
    x_api_key: Optional[str] = Header(None)  # API key from header
):
    """
    Convenience endpoint for fast analysis mode.
    
    This endpoint is a shortcut that automatically sets mode="fast".
    It's identical to calling /api/v1/analyze with mode="fast" in the body.
    Provided for API convenience and clearer endpoint names.
    
    Args:
        request (AnalyzeRequest): Request body (mode will be overridden)
        x_api_key (str, optional): OpenAI API key from header
    
    Returns:
        dict: Same as /api/v1/analyze with mode="fast"
    
    Status Codes:
        Same as /api/v1/analyze
    
    Example:
        POST /api/v1/analyze/fast
        Headers: X-API-Key: sk-xxx
        Body: {"problem": "Build a chatbot"}
    """
    # Override the mode to ensure fast analysis
    # This is done regardless of what the user sends
    request.mode = "fast"
    
    # Call the main analyze_problem function
    # await is used because this is an async function
    return await analyze_problem(request, x_api_key)


@app.post("/api/v1/analyze/deep", tags=["Analysis"])
async def analyze_deep(
    request: AnalyzeRequest,  # Request body
    x_api_key: Optional[str] = Header(None)  # API key from header
):
    """
    Convenience endpoint for deep analysis mode.
    
    This endpoint is a shortcut that automatically sets mode="deep".
    It's identical to calling /api/v1/analyze with mode="deep" in the body.
    Deep mode generates multiple options and uses LLM as judge.
    
    Args:
        request (AnalyzeRequest): Request body (mode will be overridden)
        x_api_key (str, optional): OpenAI API key from header
    
    Returns:
        dict: Same as /api/v1/analyze with mode="deep"
              Includes all_options, evaluations, and winner_reasoning
    
    Status Codes:
        Same as /api/v1/analyze
    
    Example:
        POST /api/v1/analyze/deep
        Headers: X-API-Key: sk-xxx
        Body: {"problem": "Complex AI system"}
    """
    # Override the mode to ensure deep analysis
    request.mode = "deep"
    
    # Call the main analyze_problem function
    return await analyze_problem(request, x_api_key)


# ============================================================================
# API ENDPOINTS - SPECIFIC RESOURCE LOOKUP
# ============================================================================

@app.get("/api/v1/templates/{acronym}", tags=["Reference"])
async def get_template_by_acronym(acronym: str):
    """
    Get detailed information for a specific template by its acronym.
    
    This endpoint allows users to look up a template by its short acronym
    (e.g., "R-T-F", "DREAM", "P-A-C-T"). Case-insensitive matching is used.
    
    Args:
        acronym (str): Template acronym (path parameter)
                      Examples: R-T-F, DREAM, SOIVE, TAG, etc.
    
    Returns:
        dict: Complete template information including:
            - name: Full template name
            - acronym: Short identifier
            - components: List of template parts
            - use_cases: Example scenarios
            - description: Detailed explanation
            - best_for: Ideal use cases
    
    Raises:
        HTTPException: 404 if template with given acronym not found
    
    Status Codes:
        200: Success - template found
        404: Not Found - no template with that acronym
    
    Example:
        GET /api/v1/templates/D-R-E-A-M
        
        Response:
        {
            "name": "Define-Research-Execute-Analyse-Measure",
            "acronym": "D-R-E-A-M",
            "components": ["Define", "Research", ...],
            ...
        }
    """
    # Search for template with matching acronym
    # next() returns first match or None if not found
    # Case-insensitive comparison using .upper()
    template = next(
        (t for t in TEMPLATES if t.acronym.upper() == acronym.upper()),
        None  # Default value if no match found
    )
    
    # If no template found, return 404 Not Found
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template '{acronym}' not found"
        )
    
    # Return complete template information
    return {
        "name": template.name,  # Full name
        "acronym": template.acronym,  # Acronym
        "components": template.components,  # Template parts
        "use_cases": template.use_cases,  # Example uses
        "description": template.description,  # What it does
        "best_for": template.best_for  # When to use it
    }


@app.get("/api/v1/techniques/{name}", tags=["Reference"])
async def get_technique_by_name(name: str):
    """
    Get detailed information for a specific technique by name.
    
    This endpoint allows users to look up a technique by its name.
    Supports partial matching, so searching for "chain" will find
    "Chain of Thought Prompting". Case-insensitive.
    
    Args:
        name (str): Full or partial technique name (path parameter)
                   Examples: "chain", "tree", "self-consistency"
    
    Returns:
        dict: Complete technique information including:
            - name: Full technique name
            - description: What the technique does
            - use_cases: Example scenarios
            - best_for: Ideal use cases
    
    Raises:
        HTTPException: 404 if no technique matches the name
    
    Status Codes:
        200: Success - technique found
        404: Not Found - no matching technique
    
    Example:
        GET /api/v1/techniques/chain
        
        Response:
        {
            "name": "Chain of Thought Prompting",
            "description": "Breaks down complex problems...",
            "use_cases": ["Math", "Logic"],
            "best_for": "Multi-step reasoning"
        }
    """
    # Search for technique with name containing the search term
    # Uses partial matching with case-insensitive comparison
    # This allows flexible searching (e.g., "chain" matches "Chain of Thought")
    technique = next(
        (t for t in TECHNIQUES if name.lower() in t.name.lower()),
        None  # Default value if no match found
    )
    
    # If no technique found, return 404 Not Found
    if not technique:
        raise HTTPException(
            status_code=404,
            detail=f"Technique containing '{name}' not found"
        )
    
    # Return complete technique information
    return {
        "name": technique.name,  # Full name
        "description": technique.description,  # What it does
        "use_cases": technique.use_cases,  # Example uses
        "best_for": technique.best_for  # When to use it
    }


# ============================================================================
# MAIN ENTRY POINT (FOR DIRECT EXECUTION)
# ============================================================================

# This block only runs when the file is executed directly (not imported)
# Allows running the API with: python fast_api_main.py
if __name__ == "__main__":
    # Import uvicorn server
    import uvicorn
    
    # Run the FastAPI application
    # host="0.0.0.0" makes it accessible from other machines
    # port=8000 is the default HTTP port for the API
    uvicorn.run(
        app,  # FastAPI application instance
        host="0.0.0.0",  # Listen on all network interfaces
        port=8000  # Port number
    )
