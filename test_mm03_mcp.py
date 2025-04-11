#!/usr/bin/env python3

import requests
import json
import sys

"""
测试脚本，用于验证MM03 MCP服务器是否正常工作
使用方法: python3 test_mm03_mcp.py
"""

# 服务器地址
SERVER_URL = "http://localhost:5003"

def test_manifest():
    """测试获取manifest"""
    print("测试获取MCP manifest...")
    try:
        response = requests.get(f"{SERVER_URL}/.well-known/mcp-manifest.json")
        response.raise_for_status()
        manifest = response.json()
        print(f"成功获取manifest! name_for_model: {manifest.get('name_for_model')}")
        print(f"可用工具: {[tool['name'] for tool in manifest.get('tools', [])]}")
        return True
    except Exception as e:
        print(f"获取manifest失败: {e}")
        return False

def test_sse_endpoint():
    """测试SSE端点"""
    print("\n测试SSE端点...")
    try:
        # 使用stream=True获取SSE事件流
        response = requests.get(f"{SERVER_URL}/mcp/sse", stream=True)
        response.raise_for_status()
        print("SSE端点响应成功!")
        # 只读取第一个事件然后关闭
        for line in response.iter_lines():
            if line:
                print(f"SSE事件: {line.decode('utf-8')}")
                break
        return True
    except Exception as e:
        print(f"SSE端点测试失败: {e}")
        return False

def test_tool_call(tool_name="get_masterdata"):
    """测试工具调用"""
    print(f"\n测试工具调用: {tool_name}...")
    try:
        # 准备请求数据
        if tool_name == "get_masterdata":
            data = {"material": "FG126", "plant": "1310"}
        elif tool_name == "get_supplydemand":
            data = {"material": "FG126", "plant": "1310"}
        else:
            print(f"未知工具: {tool_name}")
            return False
            
        # 发送JSON-RPC请求
        payload = {
            "jsonrpc": "2.0",
            "method": f"mcp_MM03__{tool_name}",
            "params": data,
            "id": 1
        }
        
        response = requests.post(
            f"{SERVER_URL}/mcp/jsonrpc",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text[:200]}...")
        
        response.raise_for_status()
        result = response.json()
        
        if "error" in result:
            print(f"工具调用返回错误: {result['error']}")
            return False
            
        print(f"工具调用成功!")
        return True
    except Exception as e:
        print(f"工具调用失败: {e}")
        return False

def main():
    """运行所有测试"""
    if not test_manifest():
        print("Manifest测试失败，退出测试")
        return
        
    if not test_sse_endpoint():
        print("SSE端点测试失败，继续尝试其他测试")
    
    # 测试工具调用
    test_tool_call("get_masterdata")
    
    print("\n测试完成!")

if __name__ == "__main__":
    main() 