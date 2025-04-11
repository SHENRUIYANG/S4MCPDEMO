#!/usr/bin/env python3
import json
import logging
import os
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# SAP connection parameters
SAP_HOST = os.getenv("SAP_HOST")
SAP_PORT = os.getenv("SAP_PORT")
SAP_CLIENT = os.getenv("SAP_CLIENT")
SAP_USER = os.getenv("SAP_USER")
SAP_PASSWORD = os.getenv("SAP_PASSWORD")
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "False").lower() == "true"

app = FastAPI(
    title="Material Master Data MCP",
    description="MCP server for SAP Material Master Data",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class MaterialBasicDataRequest(BaseModel):
    material: str


class MaterialSearchRequest(BaseModel):
    description: str
    max_results: int = 50


class MaterialBasicData(BaseModel):
    material: str
    description: str
    material_type: str
    base_unit: str
    material_group: str
    created_on: str
    created_by: str
    last_change: str


class MaterialSearchResult(BaseModel):
    material: str
    description: str
    material_type: str


# Mock data generator functions
def generate_mock_material_data(material_number: str) -> MaterialBasicData:
    """Generate mock material data for testing without SAP connection"""
    today = datetime.now()
    created_date = (today - timedelta(days=random.randint(100, 1000))).strftime("%Y-%m-%d")
    
    material_types = ["FERT", "HALB", "ROH", "HAWA", "DIEN"]
    base_units = ["EA", "KG", "L", "M", "PC"]
    material_groups = ["1000", "2000", "3000", "4000", "5000"]
    
    return MaterialBasicData(
        material=material_number,
        description=f"Mock material {material_number} for testing",
        material_type=random.choice(material_types),
        base_unit=random.choice(base_units),
        material_group=random.choice(material_groups),
        created_on=created_date,
        created_by="MOCKUSER",
        last_change=today.strftime("%Y-%m-%d"),
    )


def generate_mock_search_results(description: str, max_results: int) -> List[MaterialSearchResult]:
    """Generate mock search results for testing without SAP connection"""
    results = []
    for i in range(random.randint(1, max_results)):
        material_number = ''.join(random.choices(string.ascii_uppercase, k=2)) + ''.join(random.choices(string.digits, k=4))
        material_types = ["FERT", "HALB", "ROH", "HAWA", "DIEN"]
        
        results.append(
            MaterialSearchResult(
                material=material_number,
                description=f"{description} {i+1} - Mock material for testing",
                material_type=random.choice(material_types),
            )
        )
    
    return results


# SAP connection and data retrieval functions
def get_sap_connection():
    """Establish connection to SAP system"""
    if USE_MOCK_DATA:
        logger.info("Using mock data instead of connecting to SAP")
        return None
        
    try:
        # Here you would implement actual SAP connection logic
        # For example using PyRFC or another SAP connector
        logger.info(f"Connecting to SAP system {SAP_HOST}:{SAP_PORT} client {SAP_CLIENT}")
        # connection = pyrfc.Connection(
        #     ashost=SAP_HOST,
        #     sysnr=SAP_SYSNR,
        #     client=SAP_CLIENT,
        #     user=SAP_USER,
        #     passwd=SAP_PASSWORD
        # )
        # return connection
        
        # For now just return None as a placeholder
        return None
    except Exception as e:
        logger.error(f"Error connecting to SAP: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to connect to SAP: {str(e)}")


def get_material_data_from_sap(material: str) -> MaterialBasicData:
    """Retrieve material data from SAP system"""
    if USE_MOCK_DATA:
        return generate_mock_material_data(material)
        
    try:
        conn = get_sap_connection()
        
        # Here you would call the appropriate RFC function
        # For example:
        # result = conn.call('BAPI_MATERIAL_GET_DETAIL',
        #                    MATERIAL=material)
        # 
        # Then map the result to MaterialBasicData
        
        # For now just return mock data
        return generate_mock_material_data(material)
    except Exception as e:
        logger.error(f"Error retrieving material data from SAP: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve material data: {str(e)}")


def search_materials_in_sap(description: str, max_results: int) -> List[MaterialSearchResult]:
    """Search for materials in SAP system by description"""
    if USE_MOCK_DATA:
        return generate_mock_search_results(description, max_results)
        
    try:
        conn = get_sap_connection()
        
        # Here you would call the appropriate RFC function
        # For example:
        # result = conn.call('BAPI_MATERIAL_GETLIST',
        #                   MATERIAL_DESC=description,
        #                   MAX_ROWS=max_results)
        # 
        # Then map the results to a list of MaterialSearchResult
        
        # For now just return mock data
        return generate_mock_search_results(description, max_results)
    except Exception as e:
        logger.error(f"Error searching materials in SAP: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search materials: {str(e)}")


# MCP Manifest
@app.get("/.well-known/mcp-manifest.json")
async def get_manifest():
    """Return the MCP manifest defining available tools"""
    manifest = {
        "schema_version": "v1",
        "name_for_human": "Material Master Data",
        "name_for_model": "mcp_MRP_",
        "description_for_human": "Access SAP Material Master Data information",
        "description_for_model": "Retrieve material master data from SAP systems, including basic material information and search by description.",
        "logo_url": "https://example.com/logo.png",  # Replace with actual logo URL
        "contact_email": "contact@example.com",  # Replace with actual contact email
        "legal_info_url": "https://example.com/legal",  # Replace with actual legal info URL
        "tools": [
            {
                "name": "BasicData",
                "description": "Get basic information for a material by material number",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "material": {
                            "type": "string",
                            "description": "Material number (e.g. FG126)"
                        }
                    },
                    "required": ["material"]
                }
            },
            {
                "name": "Description",
                "description": "Search for materials by description text",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Description text to search for (e.g. 'valve')"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 50
                        }
                    },
                    "required": ["description"]
                }
            }
        ]
    }
    
    return manifest


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# MCP Tool implementations
@app.post("/mcp_MRP__BasicData")
async def basic_data(request: MaterialBasicDataRequest):
    """Get basic information for a material"""
    logger.info(f"Retrieving basic data for material: {request.material}")
    
    material_data = get_material_data_from_sap(request.material)
    
    return material_data


@app.post("/mcp_MRP__Description")
async def description_search(request: MaterialSearchRequest):
    """Search for materials by description"""
    logger.info(f"Searching materials with description: {request.description}, max results: {request.max_results}")
    
    search_results = search_materials_in_sap(request.description, request.max_results)
    
    return search_results


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Material Master Data MCP Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=5002, help="Port to bind the server to")
    args = parser.parse_args()
    
    logger.info(f"Starting Material Master Data MCP Server on {args.host}:{args.port}")
    uvicorn.run("server:app", host=args.host, port=args.port, reload=True) 