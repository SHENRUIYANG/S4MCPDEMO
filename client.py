#!/usr/bin/env python3
import argparse
import json
import sys
from typing import Dict, Any, List, Optional

import requests

BASE_URL = "http://localhost:5002"  # Default server URL


def get_manifest() -> Dict[str, Any]:
    """Get the MCP manifest from the server"""
    response = requests.get(f"{BASE_URL}/.well-known/mcp-manifest.json")
    response.raise_for_status()
    return response.json()


def get_health() -> Dict[str, Any]:
    """Get server health status"""
    response = requests.get(f"{BASE_URL}/health")
    response.raise_for_status()
    return response.json()


def get_basic_data(material: str) -> Dict[str, Any]:
    """Get basic material data"""
    response = requests.post(
        f"{BASE_URL}/mcp_MRP__BasicData",
        json={"material": material}
    )
    response.raise_for_status()
    return response.json()


def search_by_description(description: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """Search materials by description"""
    response = requests.post(
        f"{BASE_URL}/mcp_MRP__Description",
        json={"description": description, "max_results": max_results}
    )
    response.raise_for_status()
    return response.json()


def pretty_print_json(data: Any) -> None:
    """Print JSON data in a readable format"""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Material Master Data MCP Client")
    parser.add_argument("--server", default=BASE_URL, help="MCP server URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Manifest command
    manifest_parser = subparsers.add_parser("manifest", help="Get MCP manifest")
    
    # Health command
    health_parser = subparsers.add_parser("health", help="Check server health")
    
    # Basic data command
    basic_data_parser = subparsers.add_parser("basic-data", help="Get material basic data")
    basic_data_parser.add_argument("material", help="Material number")
    
    # Description search command
    description_parser = subparsers.add_parser("search", help="Search materials by description")
    description_parser.add_argument("description", help="Description text to search for")
    description_parser.add_argument("--max", type=int, default=50, help="Maximum number of results")
    
    args = parser.parse_args()
    
    # Set server URL if provided
    global BASE_URL
    if args.server:
        BASE_URL = args.server
    
    # Execute the requested command
    try:
        if args.command == "manifest":
            pretty_print_json(get_manifest())
        
        elif args.command == "health":
            pretty_print_json(get_health())
        
        elif args.command == "basic-data":
            pretty_print_json(get_basic_data(args.material))
        
        elif args.command == "search":
            pretty_print_json(search_by_description(args.description, args.max))
        
        else:
            parser.print_help()
            sys.exit(1)
    
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        if hasattr(e, "response") and e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 