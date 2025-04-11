#!/usr/bin/env python3
"""
Example of using the SAP Material Data MCP server with Claude or other AI assistants.

This shows how to set up an MCP integration with the MCP server
to allow AI assistants to retrieve SAP material data.
"""
import os
import argparse
import requests
import json
from typing import Dict, Any

# Default server URL
DEFAULT_SERVER_URL = "http://localhost:5002"

def check_server_status(server_url: str = DEFAULT_SERVER_URL) -> bool:
    """Check if the MCP server is running."""
    try:
        # Try to connect to the MCP SSE endpoint which should always be available
        response = requests.get(f"{server_url}/mcp/sse")
        return response.status_code == 200
    except:
        return False

def get_material_data(material: str, server_url: str = DEFAULT_SERVER_URL) -> Dict[str, Any]:
    """Get basic material data using the BasicData tool."""
    # MCP request format
    mcp_request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "callTool",
        "params": {
            "name": "BasicData",
            "parameters": {
                "material": material
            }
        }
    }
    
    try:
        # Send the request to the MCP server
        response = requests.post(
            f"{server_url}/mcp/jsonrpc",
            headers={"Content-Type": "application/json"},
            json=mcp_request
        )
        
        # Return the result
        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                return result["result"]
            elif "error" in result:
                return {"error": result["error"]["message"]}
            return result
        else:
            return {
                "error": f"Request failed with status code {response.status_code}",
                "details": response.text
            }
    except Exception as e:
        return {"error": str(e)}

def search_materials_by_description(description: str, max_results: int = 50, server_url: str = DEFAULT_SERVER_URL) -> Dict[str, Any]:
    """Search for materials by description using the Description tool."""
    # MCP request format
    mcp_request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "callTool",
        "params": {
            "name": "Description",
            "parameters": {
                "description": description,
                "max_results": max_results
            }
        }
    }
    
    try:
        # Send the request to the MCP server
        response = requests.post(
            f"{server_url}/mcp/jsonrpc",
            headers={"Content-Type": "application/json"},
            json=mcp_request
        )
        
        # Return the result
        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                return result["result"]
            elif "error" in result:
                return {"error": result["error"]["message"]}
            return result
        else:
            return {
                "error": f"Request failed with status code {response.status_code}",
                "details": response.text
            }
    except Exception as e:
        return {"error": str(e)}

def format_json(data: Dict[str, Any]) -> str:
    """Format JSON data with indentation."""
    return json.dumps(data, indent=2)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test the SAP Material Data MCP server")
    parser.add_argument("--server", default=DEFAULT_SERVER_URL, help="Server URL")
    parser.add_argument("--material", help="Material number to look up (e.g., FG126)")
    parser.add_argument("--description", help="Description text to search for (e.g., '序列号')")
    parser.add_argument("--max-results", type=int, default=50, help="Maximum number of results for description search")
    args = parser.parse_args()
    
    # Check if server is running
    print(f"Checking if SAP Material Data MCP server is running at {args.server}...")
    if check_server_status(args.server):
        print("Server is running.")
        
        # Process based on arguments
        if args.material:
            # Look up material data
            print(f"\nLooking up material {args.material}...")
            result = get_material_data(args.material, args.server)
            print(format_json(result))
        elif args.description:
            # Search by description
            print(f"\nSearching for materials with description containing '{args.description}'...")
            result = search_materials_by_description(args.description, args.max_results, args.server)
            print(format_json(result))
            
            # If we got results, show a count
            if "value" in result and isinstance(result["value"], list):
                print(f"\nFound {len(result['value'])} materials matching '{args.description}'")
        else:
            print("\nPlease specify either --material or --description")
            return
        
        # Show example of what to tell an AI assistant
        print("\n=== Example instruction for AI assistant (e.g., Claude) ===")
        print(f"You can use the SAP Material Data MCP server at {args.server} to interact with SAP.")
        print("For example, you can ask:")
        print("- 'What is the product type for material FG126?'")
        print("- 'Find materials with 序列号 in their description'")
    else:
        print(f"Error: SAP Material Data MCP server is not running at {args.server}")
        print("Please start the server first with: python MM03_MCP.py")

if __name__ == "__main__":
    main() 