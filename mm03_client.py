#!/usr/bin/env python3
import sys
import argparse
import logging
from pathlib import Path
import subprocess
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mm03_client")

def run_mcp_server(server_file: str):
    """使用subprocess运行MCP服务器"""
    logger.info(f"Starting MCP server from file: {server_file}")
    
    try:
        # 运行服务器脚本
        server_process = subprocess.Popen(
            [sys.executable, server_file],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # 行缓冲
        )
        
        # 保存server_process以便后续通信
        return server_process
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        sys.exit(1)

def call_mcp_function(server_process, function_name, **params):
    """调用MCP服务器中的函数"""
    logger.info(f"Calling MCP function: {function_name} with params: {params}")
    
    try:
        # 构建请求对象
        request = {
            "jsonrpc": "2.0",
            "method": function_name,
            "params": params,
            "id": 1
        }
        
        # 发送请求到服务器
        request_str = json.dumps(request) + "\n"
        server_process.stdin.write(request_str)
        server_process.stdin.flush()
        
        # 读取响应
        response_str = server_process.stdout.readline()
        
        # 如果响应为空，检查是否有错误
        if not response_str:
            error = server_process.stderr.read()
            logger.error(f"Empty response from server. Error: {error}")
            return {"error": "Empty response from server"}
        
        # 解析响应
        response = json.loads(response_str)
        
        # 检查响应中是否有错误
        if "error" in response:
            logger.error(f"Error in MCP response: {response['error']}")
            return response["error"]
        
        # 返回结果
        return response["result"]
    except Exception as e:
        logger.error(f"Error calling MCP function: {e}")
        return {"error": str(e)}

def test_mrp_functions(server_process):
    """测试MRP MCP的各项功能"""
    
    # 测试物料主数据
    logger.info("\n----- Testing Material Master Data -----")
    result = call_mcp_function(server_process, "get_masterdata", material="FG126", plant="1310")
    print(json.dumps(result, indent=2))
    
    # 测试供需数据
    logger.info("\n----- Testing Supply/Demand Data -----")
    result = call_mcp_function(server_process, "get_supplydemand", material="FG126", plant="1310")
    print(json.dumps(result, indent=2))
    
    # 测试覆盖数据
    logger.info("\n----- Testing Coverage Data -----")
    result = call_mcp_function(server_process, "get_coverage", material="FG126", plant="1310")
    print(json.dumps(result, indent=2))
    
    # 测试BOM数据
    logger.info("\n----- Testing BOM Data -----")
    result = call_mcp_function(server_process, "get_bom", material="FG126", plant="1310", levels=2)
    print(json.dumps(result, indent=2))
    
    # 测试生产订单数据
    logger.info("\n----- Testing Production Order Data -----")
    result = call_mcp_function(server_process, "get_production_order_header", order_number="1000145")
    print(json.dumps(result, indent=2))
    
    # 测试生产订单组件数据
    logger.info("\n----- Testing Production Order Component Data -----")
    result = call_mcp_function(server_process, "get_production_order_component", order_number="1000145")
    print(json.dumps(result, indent=2))
    
    # 测试采购订单数据
    logger.info("\n----- Testing Purchase Order Data -----")
    result = call_mcp_function(server_process, "Get_PObyPO", po_number="4500000245")
    print(json.dumps(result, indent=2))
    
    # 测试采购订单行项数据
    logger.info("\n----- Testing Purchase Order Line Items Data -----")
    result = call_mcp_function(server_process, "Get_POITEMbyPO", po_number="4500000245")
    print(json.dumps(result, indent=2))

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="MM03 MCP Client")
    parser.add_argument("server_file", help="MCP server implementation file path")
    args = parser.parse_args()
    
    # 检查服务器文件是否存在
    server_file = Path(args.server_file)
    if not server_file.exists():
        logger.error(f"Server file not found: {server_file}")
        sys.exit(1)
    
    # 启动MCP服务器
    server_process = run_mcp_server(server_file)
    
    try:
        # 测试各项功能
        test_mrp_functions(server_process)
    except KeyboardInterrupt:
        logger.info("Client interrupted by user")
    finally:
        # 关闭服务器进程
        if server_process:
            logger.info("Shutting down MCP server")
            server_process.terminate()

if __name__ == "__main__":
    main() 