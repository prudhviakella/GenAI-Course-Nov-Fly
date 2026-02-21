import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

"""
{
    name:"<name of product>",
    description:"<description of product>",
    price:"<price of product>",
    quantity:"<quantity of product>",
    inventories:[
        {
           "name":"<name of inventory>",
           "location":"<price of location>",>", 
        },
         {
           "name":"<name of inventory>",
           "location":"<price of location>",>", 
        },
        {
           "name":"<name of inventory>",
           "location":"<price of location>",>", 
        }
    ]
}
"""

#Input schema
class Inventory(BaseModel):
    name: str = Field(...)
    location: str= Field(...)

class Product(BaseModel):
    name: str = Field(min_length=5, max_length=20)
    description: str = Field(...)
    price: float = Field(...)
    quantity: int = Field(...)
    inventories: list[Inventory]

#Output Schema
class ProductOutpuSchema(BaseModel):
    name: str = Field(...)
    status: str = Field(...)


app = FastAPI(
    title="Prompt Advisor API",  # API name shown in documentation
    description="Analyze business problems and get AI-powered prompt template and technique recommendations",
    version="1.0.0"  # API version for tracking changes
)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/product",)
def test(input:Product) -> ProductOutpuSchema:
    """
    Create a Product
    :return:
    """
    """
    Business Logic
    """
    return {"name":dict(input).get("name"),"status":"updated"}

uvicorn.run(
        app,  # FastAPI application instance
        host="0.0.0.0",  # Listen on all network interfaces
        port=8000  # Port number
    )