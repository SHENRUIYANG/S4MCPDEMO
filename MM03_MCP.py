#!/usr/bin/env python3
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
        payload = jwt.decode(api_key, secret_key, algorithms=["HS256"])
        
        # 验证API Key是否过期
        if "exp" in payload and datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
            return None
            
        # 返回SAP连接信息
        return {
            "sap_host": payload.get("sap_host"),
            "sap_port": payload.get("sap_port", "443"),
            "sap_user": payload.get("sap_user"),
            "sap_password": payload.get("sap_password")
        }
    except jwt.InvalidTokenError:
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
        
        url = f"https://{host}:{port}/sap/opu/odata4/sap/api_product/srvd_a2x/sap/product/0002/Product/{material}"
        auth = (user, password)
        headers = {"Accept": "application/json"}
        
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(url, auth=auth, headers=headers)
            response.raise_for_status()
            return response.json()
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
        
        url = f"https://{host}:{port}/sap/opu/odata4/sap/api_product/srvd_a2x/sap/product/0002/ProductDescription"
        auth = (user, password)
        
        # 构建过滤条件
        filter_condition = f"contains(ProductDescription, '{description}')"
        if language != "ALL":
            filter_condition += f" and Language eq '{language}'"
            
        params = {
            "$filter": filter_condition,
            "$top": str(max_results)
        }
        headers = {
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(url, auth=auth, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "value" in data:
                results = []
                for item in data["value"]:
                    results.append({
                        "material": item["Product"],
                        "description": item["ProductDescription"],
                        "language": item["Language"]
                    })
                return results
            return []
    except Exception as e:
        logger.error(f"Error searching materials: {str(e)}")
        error_message = str(e)
        return {"error": error_message}

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
        
        url = f"https://{host}:{port}/sap/opu/odata4/sap/api_product/srvd_a2x/sap/product/0002/ProductDescription"
        auth = (user, password)
        params = {
            "$filter": f"Product eq '{material}' and Language eq '{language}'",
            "$format": "json"
        }
        headers = {
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(url, auth=auth, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "value" in data and len(data["value"]) > 0:
                result = {
                    "material": data["value"][0]["Product"],
                    "description": data["value"][0]["ProductDescription"],
                    "language": data["value"][0]["Language"]
                }
                return result
            else:
                return {
                    "material": material,
                    "description": f"No description found in language {language}",
                    "language": language
                }
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
        async def api_basic_data(request: Request, data: MaterialRequest, sap_info: Optional[Dict] = Depends(verify_api_key_header)):
            """物料基础信息API"""
            result = await BasicData(data.material, data.api_key)
            return result
        
        @app.post("/mcp_MM03_DescToMaterial")
        async def api_description(request: Request, data: SearchRequest, sap_info: Optional[Dict] = Depends(verify_api_key_header)):
            """物料描述搜索API"""
            result = await DescToMaterial(data.description, data.max_results, data.language, data.api_key)
            return result
        
        @app.post("/mcp_MM03_Description_Search")
        async def api_description_search(request: Request, data: DescriptionSearchRequest, sap_info: Optional[Dict] = Depends(verify_api_key_header)):
            """物料指定语言描述API"""
            result = await Description_Search(data.material, data.language, data.api_key)
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