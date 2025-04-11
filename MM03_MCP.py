#!/usr/bin/env python3
import os
import json
import logging
from typing import Dict, List, Any
import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# 配置logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MM03_MCP")

# 加载环境变量
load_dotenv()

# SAP连接配置
SAP_HOST = os.getenv("SAP_HOST", "my200816.s4hana.sapcloud.cn")
SAP_PORT = os.getenv("SAP_PORT", "443")
SAP_USER = os.getenv("SAP_USER", "")
SAP_PASSWORD = os.getenv("SAP_PASSWORD", "")

# 初始化FastMCP服务器
mcp = FastMCP("MM03")

@mcp.tool()
async def BasicData(material: str) -> Dict[str, Any]:
    """获取物料的基本信息。

    Args:
        material: 物料编号 (例如: FG126)
    """
    logger.info(f"Getting basic data for material: {material}")
    
    try:
        # 使用正确的SAP OData API端点 - 从API sample文件中获取
        url = f"https://{SAP_HOST}:{SAP_PORT}/sap/opu/odata4/sap/api_product/srvd_a2x/sap/product/0002/Product/{material}"
        auth = (SAP_USER, SAP_PASSWORD)
        headers = {"Accept": "application/json"}
        
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(url, auth=auth, headers=headers)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error getting material data: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def DescToMaterial(description: str, max_results: int = 50, language: str = "ZH") -> List[Dict[str, Any]]:
    """通过描述搜索物料。

    Args:
        description: 描述文本 (例如: 'valve')
        max_results: 最大返回结果数 (默认: 50)
        language: 语言代码 (例如: EN为英语, ZH为中文, ALL为所有语言, 默认为ZH)
    """
    logger.info(f"Searching materials with description: {description} in language: {language}")
    
    try:
        # 使用正确的SAP OData API端点 - 从API sample2文件中获取
        url = f"https://{SAP_HOST}:{SAP_PORT}/sap/opu/odata4/sap/api_product/srvd_a2x/sap/product/0002/ProductDescription"
        auth = (SAP_USER, SAP_PASSWORD)
        
        # 构建过滤条件，如果language为ALL则不限制语言
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
            
            # 转换SAP响应格式为标准格式 - 根据sample2文件中的响应格式
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
async def Description_Search(material: str, language: str = "EN") -> Dict[str, Any]:
    """获取特定物料在指定语言下的描述信息。

    Args:
        material: 物料编号 (例如: FG126)
        language: 语言代码 (例如: EN为英语, ZH为中文, 默认为EN)
    """
    logger.info(f"Searching description for material {material} in language {language}")
    
    try:
        # 使用SAP ProductDescription API获取特定物料的指定语言描述
        url = f"https://{SAP_HOST}:{SAP_PORT}/sap/opu/odata4/sap/api_product/srvd_a2x/sap/product/0002/ProductDescription"
        auth = (SAP_USER, SAP_PASSWORD)
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
            
            # 转换SAP响应格式为标准格式
            if "value" in data and len(data["value"]) > 0:
                result = {
                    "material": data["value"][0]["Product"],
                    "description": data["value"][0]["ProductDescription"],
                    "language": data["value"][0]["Language"]
                }
                return result
            else:
                # 如果没有找到指定语言的描述，返回提示信息
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
    parser.add_argument("--mode", type=str, default="stdio", choices=["stdio", "http"], 
                        help="Communication mode: stdio or http")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind for HTTP mode")
    parser.add_argument("--port", type=int, default=5003, help="Port to bind for HTTP mode")
    args = parser.parse_args()
    
    # 启动MCP服务
    logger.info(f"Starting Material Master Data MCP server in {args.mode} mode")
    
    if args.mode == "http":
        # HTTP模式 - 使用FastAPI
        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel
        
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
            
        class SearchRequest(BaseModel):
            description: str
            max_results: int = 50
            language: str = "ZH"
        
        class DescriptionSearchRequest(BaseModel):
            material: str
            language: str = "EN"
        
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
                                }
                            },
                            "required": ["material"]
                        }
                    }
                ]
            }
            return manifest
            
        # 工具端点
        @app.post("/mcp_MM03_BasicData")
        async def api_basic_data(request: MaterialRequest):
            """获取物料基本信息的API端点"""
            result = await BasicData(request.material)
            return result
            
        @app.post("/mcp_MM03_DescToMaterial")
        async def api_description(request: SearchRequest):
            """搜索物料的API端点"""
            # 调用DescToMaterial函数进行API请求
            result = await DescToMaterial(request.description, request.max_results, request.language)
            return result
            
        @app.post("/mcp_MM03_Description_Search")
        async def api_description_search(request: DescriptionSearchRequest):
            """搜索物料描述的API端点"""
            result = await Description_Search(request.material, request.language)
            return result
            
        # 健康检查端点
        @app.get("/health")
        async def health_check():
            """健康检查端点"""
            from datetime import datetime
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        # 启动HTTP服务器
        logger.info(f"Starting HTTP server on {args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        # stdio模式
        logger.info("Starting stdio server")
        mcp.run(transport="stdio") 