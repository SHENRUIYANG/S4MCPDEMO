#!/usr/bin/env python3
import jwt
import argparse
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

def generate_api_key(sap_host: str, sap_port: str, sap_user: str, sap_password: str, expiry_days: int = 365) -> str:
    """生成包含SAP连接信息的API Key。

    Args:
        sap_host: SAP服务器地址
        sap_port: SAP服务器端口
        sap_user: SAP用户名
        sap_password: SAP密码
        expiry_days: API Key有效期（天数）

    Returns:
        str: JWT格式的API Key
    """
    # 加载环境变量
    load_dotenv()
    
    # 获取JWT密钥
    secret_key = os.getenv("JWT_SECRET", "your-secret-key")
    
    # 创建payload
    payload = {
        "sap_host": sap_host,
        "sap_port": sap_port,
        "sap_user": sap_user,
        "sap_password": sap_password,
        "exp": datetime.utcnow() + timedelta(days=expiry_days)
    }
    
    # 生成JWT
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token

def main():
    parser = argparse.ArgumentParser(description="生成MCP API Key")
    parser.add_argument("--sap-host", required=True, help="SAP服务器地址")
    parser.add_argument("--sap-port", default="443", help="SAP服务器端口")
    parser.add_argument("--sap-user", required=True, help="SAP用户名")
    parser.add_argument("--sap-password", required=True, help="SAP密码")
    parser.add_argument("--expiry-days", type=int, default=365, help="API Key有效期（天数）")
    
    args = parser.parse_args()
    
    try:
        api_key = generate_api_key(
            args.sap_host,
            args.sap_port,
            args.sap_user,
            args.sap_password,
            args.expiry_days
        )
        print(f"\nAPI Key 生成成功！\n")
        print(f"API Key: {api_key}\n")
        print("使用说明：")
        print("1. 在HTTP请求中，将此API Key添加到Authorization头部：")
        print(f'   Authorization: Bearer {api_key}')
        print("\n2. 在MCP工具调用中，将此API Key作为api_key参数传递：")
        print('   await BasicData("FG126", api_key="' + api_key + '")')
        print("\n注意：请妥善保管您的API Key，不要分享给不信任的人。")
        
    except Exception as e:
        print(f"生成API Key时出错：{str(e)}")

if __name__ == "__main__":
    main() 