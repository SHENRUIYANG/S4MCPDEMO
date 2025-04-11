#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Material Master Data MCP

A service for interacting with SAP systems to provide material master data query functionality.

Version: 1.0.1
Author: ORBIS Consulting Shanghai Co.,Ltd
License: MIT
Copyright (c) 2025 ORBIS Consulting Shanghai Co.,Ltd
Last Updated: April 11, 2025
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import jwt
from datetime import datetime, timedelta

# 配置logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MM03_MCP")

# 加载环境变量
load_dotenv()

# 初始化FastMCP服务器
mcp = FastMCP("MM03")

def get_param_value(key, default=None):
    """获取参数值，优先从命令行参数获取，其次从环境变量"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(f"--{key}", dest=key)
    
    # 解析已知参数
    args, _ = parser.parse_known_args()
    value = getattr(args, key, None)
    
    # 如果命令行未提供，则从环境变量获取
    if value is None:
        value = os.getenv(key.upper(), default)
    
    return value

def verify_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """验证API Key并返回SAP连接信息"""
    try:
        # 使用JWT解码API Key
        # 注意：在生产环境中，应该使用安全的密钥存储服务
        secret_key = get_param_value("jwt_secret", "your-secret-key")
        logger.info(f"Using JWT secret key: {secret_key}")
        
        logger.info(f"Decoding API key...")
        payload = jwt.decode(api_key, secret_key, algorithms=["HS256"])
        logger.info(f"Decoded payload: {payload}")
        
        # 验证API Key是否过期
        if "exp" in payload and datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
            logger.warning("API Key has expired")
            return None
            
        # 验证必要字段
        required_fields = ["email", "sap_host", "sap_user", "sap_password"]
        if not all(field in payload for field in required_fields):
            logger.warning(f"Missing required fields in payload. Required: {required_fields}, Got: {list(payload.keys())}")
            return None
            
        # 返回SAP连接信息
        result = {
            "email": payload.get("email"),
            "sap_host": payload.get("sap_host"),
            "sap_port": payload.get("sap_port", "443"),
            "sap_user": payload.get("sap_user"),
            "sap_password": payload.get("sap_password")
        }
        logger.info(f"Successfully verified API key for email: {result['email']}")
        return result
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while verifying API key: {str(e)}")
        return None

def get_auth_value(request, key):
    """从请求中获取认证信息"""
    if hasattr(request, 'headers'):
        # 首先尝试从Authorization头部获取API Key
        api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
        if api_key:
            sap_info = verify_api_key(api_key)
            if sap_info:
                if key == 'SAP_HOST':
                    return sap_info['sap_host']
                elif key == 'SAP_PORT':
                    return sap_info['sap_port']
                elif key == 'SAP_USER':
                    return sap_info['sap_user']
                elif key == 'SAP_PASSWORD':
                    return sap_info['sap_password']
        
        # 如果没有API Key或验证失败，尝试从Basic认证获取
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Basic '):
            import base64
            decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
            if ':' in decoded:
                username, password = decoded.split(':', 1)
                if key == 'SAP_USER':
                    return username
                elif key == 'SAP_PASSWORD':
                    return password
    return None

# SAP连接配置
SAP_HOST = get_param_value("sap_host")
SAP_PORT = get_param_value("sap_port", "443")
SAP_USER = get_param_value("sap_user")
SAP_PASSWORD = get_param_value("sap_password")

@mcp.tool()
async def BasicData(material: str, api_key: str = None) -> Dict[str, Any]:
    """获取物料的基本信息。

    Args:
        material: 物料编号 (例如: FG126)
        api_key: API Key (可选)
    """
    logger.info(f"Getting basic data for material: {material}")
    
    try:
        # 验证API Key并获取SAP连接信息
        sap_info = None
        if api_key:
            logger.info("Verifying API key...")
            sap_info = verify_api_key(api_key)
            if not sap_info:
                logger.warning("Invalid or expired API key")
                return {"error": "Invalid or expired API key"}
        else:
            logger.info("No API key provided, using default configuration")
        
        # 使用SAP连接信息或默认配置
        host = sap_info['sap_host'] if sap_info else SAP_HOST
        port = sap_info['sap_port'] if sap_info else SAP_PORT
        user = sap_info['sap_user'] if sap_info else SAP_USER
        password = sap_info['sap_password'] if sap_info else SAP_PASSWORD
        
        logger.info(f"Using SAP connection: host={host}, port={port}, user={user}")
        
        if not all([host, user, password]):
            logger.error("Missing SAP connection information")
            return {"error": "Missing SAP connection information"}
        
        # 用户必须使用的SAP API端点
        url = f"https://{host}:{port}/sap/opu/odata4/sap/api_product/srvd_a2x/sap/product/0002/Product/{material}"
        
        # SAP连接认证信息
        auth = (user, password)
        
        # 必要的头部信息
        headers = {
            "Accept": "application/json",
            "x-csrf-token": "fetch"  # 首先获取CSRF token
        }
        
        logger.info(f"Making request to SAP API: {url}")
        logger.info(f"Using authentication: {user}:***")
        
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            # 第一步：建立会话并获取CSRF token
            logger.info("Step 1: Establishing SAP session and fetching CSRF token")
            session_response = await client.get(url, auth=auth, headers=headers)
            
            # 如果SAP返回了CSRF token，提取它用于后续请求
            csrf_token = session_response.headers.get("x-csrf-token")
            cookies = session_response.cookies
            
            if csrf_token:
                logger.info(f"Received CSRF token: {csrf_token}")
                headers["x-csrf-token"] = csrf_token
            else:
                logger.warning("No CSRF token received")
            
            # 记录初始认证响应
            logger.info(f"Initial auth response status: {session_response.status_code}")
            logger.info(f"Initial auth response headers: {session_response.headers}")
            
            # 第二步：执行实际的API查询
            logger.info("Step 2: Executing actual API query")
            response = await client.get(
                url, 
                auth=auth, 
                headers=headers,
                cookies=cookies  # 使用第一次请求建立的会话cookies
            )
            
            # 记录响应状态和头部
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {response.headers}")
            
            # 检查状态码
            if response.status_code != 200:
                logger.error(f"Error response from SAP API: {response.status_code} - {response.text}")
                return {"error": f"SAP API returned status {response.status_code}: {response.text[:200]}"}
            
            # 解析响应内容
            content = response.text
            content_length = len(content)
            logger.info(f"Response content length: {content_length}")
            
            # 检查内容是否为空
            if not content.strip():
                logger.warning("Empty response content from SAP API")
                return {"error": "Empty response from SAP API"}
            
            # 检查内容类型是否为HTML（可能是登录页面或错误页面）
            if content.strip().startswith("<html") or content.strip().startswith("<!DOCTYPE html") or "text/html" in response.headers.get("content-type", ""):
                logger.error("Received HTML response instead of JSON. Authentication may have failed.")
                logger.error(f"HTML response (first 300 chars): {content[:300]}")
                
                # 返回更有用的错误信息
                return {
                    "error": "Authentication failed or incorrect API endpoint. The SAP system returned an HTML page instead of JSON data.",
                    "details": "Please verify your SAP credentials, host, and endpoint. You may need to request API access from your SAP administrator."
                }
            
            try:
                return response.json()
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}, Content: {content[:200]}")
                return {
                    "error": "Invalid JSON response from SAP API",
                    "details": "The response could not be parsed as JSON. This typically indicates an authentication issue or incorrect API endpoint.",
                    "technical_details": f"JSON error: {str(e)}"
                }
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        return {"error": f"Failed to connect to SAP API: {str(e)}"}
    except Exception as e:
        logger.error(f"Error getting material data: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def DescToMaterial(description: str, max_results: int = 50, language: str = "ZH", api_key: str = None) -> List[Dict[str, Any]]:
    """通过描述搜索物料。

    Args:
        description: 描述文本 (例如: 'valve')
        max_results: 最大返回结果数 (默认: 50)
        language: 语言代码 (例如: EN为英语, ZH为中文, ALL为所有语言, 默认为ZH)
        api_key: API Key (可选)
    """
    logger.info(f"Searching materials with description: {description} in language: {language}")
    
    try:
        # 验证API Key并获取SAP连接信息
        sap_info = None
        if api_key:
            sap_info = verify_api_key(api_key)
            if not sap_info:
                return {"error": "Invalid or expired API key"}
        
        # 使用SAP连接信息或默认配置
        host = sap_info['sap_host'] if sap_info else SAP_HOST
        port = sap_info['sap_port'] if sap_info else SAP_PORT
        user = sap_info['sap_user'] if sap_info else SAP_USER
        password = sap_info['sap_password'] if sap_info else SAP_PASSWORD
        
        if not all([host, user, password]):
            return {"error": "Missing SAP connection information"}
        
        # 构建全路径URL - 检查是否包含端口号
        base_url = f"https://{host}"
        if port and port != "443":
            base_url += f":{port}"
        
        # 尝试改用标准的SAP OData V2格式端点
        service_path = "/sap/opu/odata/SAP/API_PRODUCT_SRV"
        
        # 用于检查服务可用性的URL
        service_url = f"{base_url}{service_path}"
        
        # 构建过滤条件 - 使用OData V2格式
        filter_condition = f"substringof('{description}',Description)"
        if language != "ALL":
            filter_condition += f" and Language eq '{language}'"
            
        # 查询参数 - 使用OData V2格式
        params = {
            "$filter": filter_condition,
            "$top": str(max_results),
            "$format": "json"
        }
        
        # 认证信息
        auth = (user, password)
        
        # SAP OData 推荐头部
        headers = {
            "Accept": "application/json",
            "x-csrf-token": "fetch",  # 获取CSRF令牌
            "sap-client": "100",      # SAP客户端ID，通常是100
            "sap-language": language   # 语言代码
        }
        
        logger.info(f"Trying to access SAP OData service: {service_url}")
        logger.info(f"Using authentication: {user}:***")
        
        async with httpx.AsyncClient(verify=False, timeout=60.0, follow_redirects=True) as client:
            # 第一步：尝试连接服务根目录，获取CSRF令牌
            logger.info("Step 1: Connecting to service root to fetch CSRF token")
            metadata_url = f"{service_url}/$metadata"
            logger.info(f"Requesting metadata from: {metadata_url}")
            
            session_response = await client.get(
                metadata_url, 
                auth=auth, 
                headers=headers,
                timeout=30.0
            )
            
            logger.info(f"Metadata response status: {session_response.status_code}")
            logger.info(f"Metadata response headers: {session_response.headers}")
            
            # 获取CSRF令牌和cookies
            csrf_token = session_response.headers.get("x-csrf-token")
            cookies = session_response.cookies
            
            if csrf_token:
                logger.info(f"Received CSRF token: {csrf_token}")
                headers["x-csrf-token"] = csrf_token
            else:
                logger.warning("No CSRF token received from metadata request")
            
            # 第二步：构建实际的查询URL
            entity_url = f"{service_url}/MaterialDescriptions"
            logger.info(f"Step 2: Querying entity set at: {entity_url} with params: {params}")
            
            # 执行实际查询
            response = await client.get(
                entity_url, 
                auth=auth, 
                params=params, 
                headers=headers,
                cookies=cookies,
                timeout=30.0
            )
            
            # 记录响应
            logger.info(f"Query response status: {response.status_code}")
            logger.info(f"Query response headers: {response.headers}")
            
            # 检查状态码
            if response.status_code != 200:
                logger.error(f"Error response from SAP API: {response.status_code} - {response.text}")
                return {"error": f"SAP API returned status {response.status_code}: {response.text[:200]}"}
            
            # 解析响应内容
            content = response.text
            content_length = len(content)
            logger.info(f"Response content length: {content_length}")
            
            # 检查内容是否为空
            if not content.strip():
                logger.warning("Empty response content from SAP API")
                return {"error": "Empty response from SAP API"}
            
            # 检查是否是HTML响应
            if content.strip().startswith("<html") or content.strip().startswith("<!DOCTYPE html") or "text/html" in response.headers.get("content-type", ""):
                logger.error("Received HTML response instead of JSON. Authentication may have failed.")
                logger.error(f"HTML response (first 300 chars): {content[:300]}")
                
                # 尝试提取错误消息
                error_msg = "无法连接到SAP API，请验证您的凭据和API访问权限"
                
                # 返回更友好的错误信息
                return {
                    "error": "SAP系统认证失败或API端点配置不正确",
                    "details": "系统返回了HTML页面而不是JSON数据。请检查API密钥中的SAP连接信息和用户权限。",
                    "message": error_msg,
                    "solution": "请联系SAP管理员确认您的账号有API_PRODUCT_SRV服务的访问权限。"
                }
            
            try:
                data = response.json()
                
                # 解析OData V2响应格式
                if "d" in data and "results" in data["d"]:
                    results = []
                    for item in data["d"]["results"]:
                        results.append({
                            "material": item.get("Material", ""),
                            "description": item.get("Description", ""),
                            "language": item.get("Language", "")
                        })
                    logger.info(f"Found {len(results)} materials matching '{description}'")
                    return results
                else:
                    logger.warning(f"Unexpected response format: {data}")
                    return []
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}, Content: {content[:200]}")
                return {
                    "error": "Invalid JSON response from SAP API",
                    "details": "The response could not be parsed as JSON. This typically indicates an authentication issue or incorrect API endpoint.",
                    "technical_details": f"JSON error: {str(e)}"
                }
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        return {"error": f"Failed to connect to SAP API: {str(e)}"}
    except Exception as e:
        logger.error(f"Error searching materials: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def Description_Search(material: str, language: str = "EN", api_key: str = None) -> Dict[str, Any]:
    """获取特定物料在指定语言下的描述信息。

    Args:
        material: 物料编号 (例如: FG126)
        language: 语言代码 (例如: EN为英语, ZH为中文, 默认为EN)
        api_key: API Key (可选)
    """
    logger.info(f"Searching description for material {material} in language {language}")
    
    try:
        # 验证API Key并获取SAP连接信息
        sap_info = None
        if api_key:
            sap_info = verify_api_key(api_key)
            if not sap_info:
                return {"error": "Invalid or expired API key"}
        
        # 使用SAP连接信息或默认配置
        host = sap_info['sap_host'] if sap_info else SAP_HOST
        port = sap_info['sap_port'] if sap_info else SAP_PORT
        user = sap_info['sap_user'] if sap_info else SAP_USER
        password = sap_info['sap_password'] if sap_info else SAP_PASSWORD
        
        if not all([host, user, password]):
            return {"error": "Missing SAP connection information"}
        
        # 用户必须使用的SAP API端点
        url = f"https://{host}:{port}/sap/opu/odata4/sap/api_product/srvd_a2x/sap/product/0002/ProductDescription"
        
        params = {
            "$filter": f"Product eq '{material}' and Language eq '{language}'",
            "$format": "json"
        }
        
        # SAP连接认证信息
        auth = (user, password)
        
        # 必要的头部信息
        headers = {
            "Accept": "application/json",
            "x-csrf-token": "fetch"  # 首先获取CSRF token
        }
        
        logger.info(f"Making request to SAP API: {url} with params: {params}")
        logger.info(f"Using authentication: {user}:***")
        
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            # 第一步：建立会话并获取CSRF token
            logger.info("Step 1: Establishing SAP session and fetching CSRF token")
            session_response = await client.get(url, auth=auth, headers=headers)
            
            # 如果SAP返回了CSRF token，提取它用于后续请求
            csrf_token = session_response.headers.get("x-csrf-token")
            cookies = session_response.cookies
            
            if csrf_token:
                logger.info(f"Received CSRF token: {csrf_token}")
                headers["x-csrf-token"] = csrf_token
            else:
                logger.warning("No CSRF token received")
            
            # 记录初始认证响应
            logger.info(f"Initial auth response status: {session_response.status_code}")
            logger.info(f"Initial auth response headers: {session_response.headers}")
            
            # 第二步：执行实际的API查询
            logger.info("Step 2: Executing actual API query")
            response = await client.get(
                url, 
                auth=auth, 
                params=params, 
                headers=headers,
                cookies=cookies  # 使用第一次请求建立的会话cookies
            )
            
            # 记录响应状态和头部
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {response.headers}")
            
            # 检查状态码
            if response.status_code != 200:
                logger.error(f"Error response from SAP API: {response.status_code} - {response.text}")
                return {"error": f"SAP API returned status {response.status_code}: {response.text[:200]}"}
            
            # 解析响应内容
            content = response.text
            content_length = len(content)
            logger.info(f"Response content length: {content_length}")
            
            # 检查内容是否为空
            if not content.strip():
                logger.warning("Empty response content from SAP API")
                return {"error": "Empty response from SAP API"}
            
            # 检查内容类型是否为HTML（可能是登录页面或错误页面）
            if content.strip().startswith("<html") or content.strip().startswith("<!DOCTYPE html") or "text/html" in response.headers.get("content-type", ""):
                logger.error("Received HTML response instead of JSON. Authentication may have failed.")
                logger.error(f"HTML response (first 300 chars): {content[:300]}")
                
                # 返回更有用的错误信息
                return {
                    "error": "Authentication failed or incorrect API endpoint. The SAP system returned an HTML page instead of JSON data.",
                    "details": "Please verify your SAP credentials, host, and endpoint. You may need to request API access from your SAP administrator."
                }
            
            try:
                data = response.json()
                
                if "value" in data and len(data["value"]) > 0:
                    result = {
                        "material": data["value"][0]["Product"],
                        "description": data["value"][0]["ProductDescription"],
                        "language": data["value"][0]["Language"]
                    }
                    logger.info(f"Found description for material {material} in language {language}")
                    return result
                else:
                    logger.warning(f"No description found for material {material} in language {language}")
                    return {
                        "material": material,
                        "description": f"No description found in language {language}",
                        "language": language
                    }
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}, Content: {content[:200]}")
                return {
                    "error": "Invalid JSON response from SAP API",
                    "details": "The response could not be parsed as JSON. This typically indicates an authentication issue or incorrect API endpoint.",
                    "technical_details": f"JSON error: {str(e)}"
                }
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        return {"error": f"Failed to connect to SAP API: {str(e)}"}
    except Exception as e:
        logger.error(f"Error searching material description: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MM03 MCP Server")
    parser.add_argument("--mode", type=str, default="stdio", choices=["stdio", "http", "rest"], 
                        help="Communication mode: stdio, http or rest")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind for HTTP/REST mode")
    parser.add_argument("--port", type=int, default=5003, help="Port to bind for HTTP/REST mode")
    parser.add_argument("--endpoint", type=str, default="/rest", help="Endpoint for REST mode")
    args = parser.parse_args()
    
    # 启动MCP服务
    logger.info(f"Starting Material Master Data MCP server in {args.mode} mode")
    
    if args.mode == "rest":
        # REST模式 - 使用FastMCP REST传输
        from mcp.server.transport.rest import RestServerTransport
        
        transport = RestServerTransport(port=args.port, host=args.host, endpoint=args.endpoint)
        mcp.connect(transport)
        transport.start_server()
        
    elif args.mode == "http":
        # HTTP模式 - 使用FastAPI
        import uvicorn
        from fastapi import FastAPI, Request, HTTPException, Depends, Header
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel
        from typing import Optional
        
        app = FastAPI(
            title="Material Master Data MCP",
            description="MCP server for SAP Material Master Data",
            version="1.0.0",
        )
        
        # 添加CORS中间件
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 请求模型
        class MaterialRequest(BaseModel):
            material: str
            api_key: Optional[str] = None
            
        class SearchRequest(BaseModel):
            description: str
            max_results: int = 50
            language: str = "ZH"
            api_key: Optional[str] = None
        
        class DescriptionSearchRequest(BaseModel):
            material: str
            language: str = "EN"
            api_key: Optional[str] = None
        
        async def verify_api_key_header(authorization: str = Header(None)):
            if not authorization:
                return None
            
            api_key = authorization.replace('Bearer ', '')
            if not api_key:
                return None
                
            sap_info = verify_api_key(api_key)
            if not sap_info:
                raise HTTPException(status_code=401, detail="Invalid or expired API key")
                
            return sap_info
        
        # MCP清单
        @app.get("/.well-known/mcp-manifest.json")
        async def get_manifest():
            """返回MCP清单定义可用工具"""
            manifest = {
                "schema_version": "v1",
                "name_for_human": "Material Master Data",
                "name_for_model": "mcp_MM03_",
                "description_for_human": "Access SAP Material Master Data information",
                "description_for_model": "通过SAP系统获取物料主数据，包括基础信息和描述搜索。",
                "auth": {
                    "type": "bearer"
                },
                "tools": [
                    {
                        "name": "BasicData",
                        "description": "获取物料的基本信息",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "material": {
                                    "type": "string",
                                    "description": "物料编号 (例如: FG126)"
                                },
                                "api_key": {
                                    "type": "string",
                                    "description": "API Key (可选)"
                                }
                            },
                            "required": ["material"]
                        }
                    },
                    {
                        "name": "DescToMaterial",
                        "description": "通过描述搜索物料",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "description": {
                                    "type": "string",
                                    "description": "描述文本 (例如: 'valve')"
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "最大返回结果数",
                                    "default": 50
                                },
                                "language": {
                                    "type": "string",
                                    "description": "语言代码 (例如: EN为英语, ZH为中文, ALL为所有语言, 默认为ZH)",
                                    "default": "ZH"
                                },
                                "api_key": {
                                    "type": "string",
                                    "description": "API Key (可选)"
                                }
                            },
                            "required": ["description"]
                        }
                    },
                    {
                        "name": "Description_Search",
                        "description": "获取特定物料在指定语言下的描述信息",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "material": {
                                    "type": "string",
                                    "description": "物料编号 (例如: FG126)"
                                },
                                "language": {
                                    "type": "string",
                                    "description": "语言代码 (例如: EN为英语, ZH为中文, 默认为EN)",
                                    "default": "EN"
                                },
                                "api_key": {
                                    "type": "string",
                                    "description": "API Key (可选)"
                                }
                            },
                            "required": ["material"]
                        }
                    }
                ]
            }
            return manifest
        
        @app.post("/mcp_MM03_BasicData")
        async def api_basic_data(request: Request, data: MaterialRequest):
            """物料基础信息API"""
            logger.info("Received request for BasicData")
            api_key = None
            
            # 从请求头或请求体中获取 API Key
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                api_key = auth_header.replace('Bearer ', '')
                logger.info("Found API key in Authorization header")
            elif data.api_key:
                api_key = data.api_key
                logger.info("Found API key in request body")
                
            if not api_key:
                logger.warning("No API key provided")
                return {"error": "API key is required"}
                
            result = await BasicData(data.material, api_key)
            return result
        
        @app.post("/mcp_MM03_DescToMaterial")
        async def api_description(request: Request, data: SearchRequest):
            """物料描述搜索API"""
            logger.info("Received request for DescToMaterial")
            api_key = None
            
            # 从请求头或请求体中获取 API Key
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                api_key = auth_header.replace('Bearer ', '')
                logger.info("Found API key in Authorization header")
            elif data.api_key:
                api_key = data.api_key
                logger.info("Found API key in request body")
                
            if not api_key:
                logger.warning("No API key provided")
                return {"error": "API key is required"}
                
            result = await DescToMaterial(data.description, data.max_results, data.language, api_key)
            return result
        
        @app.post("/mcp_MM03_Description_Search")
        async def api_description_search(request: Request, data: DescriptionSearchRequest):
            """物料指定语言描述API"""
            logger.info("Received request for Description_Search")
            api_key = None
            
            # 从请求头或请求体中获取 API Key
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                api_key = auth_header.replace('Bearer ', '')
                logger.info("Found API key in Authorization header")
            elif data.api_key:
                api_key = data.api_key
                logger.info("Found API key in request body")
                
            if not api_key:
                logger.warning("No API key provided")
                return {"error": "API key is required"}
                
            result = await Description_Search(data.material, data.language, api_key)
            return result
        
        @app.get("/health")
        async def health_check():
            """健康检查"""
            return {"status": "ok"}
        
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        # STDIO模式 - 使用FastMCP标准传输
        from mcp.server.transport.stdio import StdioServerTransport
        
        transport = StdioServerTransport()
        mcp.connect(transport)
        logger.info("MM03 MCP Server running in stdio mode, waiting for input...") 