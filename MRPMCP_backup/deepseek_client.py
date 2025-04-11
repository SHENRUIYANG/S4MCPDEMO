import asyncio
import json
import sys
from typing import Optional, List, Dict, Any
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 使用OpenAI客户端库
from openai import OpenAI

class MCPClient:
    def __init__(self, api_key: str):
        # 初始化会话和客户端对象
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # 初始化OpenAI客户端，使用DeepSeek API
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
        
    async def connect_to_server(self, server_script_path: str):
        """连接到MCP服务器

        Args:
            server_script_path: 服务器脚本路径 (.py或.js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("服务器脚本必须是.py或.js文件")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        # 初始化连接
        await self.session.initialize()

        # 列出可用工具
        response = await self.session.list_tools()
        self.tools = response.tools
        print("\n已连接到服务器，可用工具:", [tool.name for tool in self.tools])
        
        # 打印工具详情
        for tool in self.tools:
            print(f"\n工具: {tool.name}")
            print(f"描述: {tool.description}")
            print(f"输入模式: {tool.inputSchema}")

    def format_tools_for_api(self, tools_list):
        """将MCP工具格式转换为DeepSeek API可接受的格式"""
        formatted_tools = []
        
        for tool in tools_list:
            try:
                # 检查是否需要解析JSON，或者已经是字典
                if isinstance(tool.inputSchema, dict):
                    schema = tool.inputSchema
                else:
                    schema = json.loads(tool.inputSchema)
                
                formatted_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": schema
                    }
                }
                formatted_tools.append(formatted_tool)
            except Exception as e:
                print(f"处理工具 {tool.name} 时出错: {str(e)}")
                
        return formatted_tools

    async def process_query(self, query: str) -> str:
        """使用DeepSeek处理查询并使用可用工具"""
        # 初始消息
        messages = [
            {"role": "user", "content": query}
        ]
        
        # 格式化工具
        formatted_tools = self.format_tools_for_api(self.tools)
        
        if not formatted_tools:
            return "无法获取可用工具或格式化工具失败"
            
        # 创建完整对话跟踪
        conversation_log = []
        conversation_log.append(f"用户: {query}")
        
        # 首次API调用
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                tools=formatted_tools,
                tool_choice="auto",
                max_tokens=1000
            )
            
            # 获取模型回复
            assistant_message = response.choices[0].message
            
            # 处理可能的工具调用
            if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    function_call = tool_call.function
                    tool_name = function_call.name
                    
                    # 解析参数
                    try:
                        # 参数可能是字符串或已经解析的对象
                        if isinstance(function_call.arguments, str):
                            tool_args = json.loads(function_call.arguments)
                        else:
                            tool_args = function_call.arguments
                    except Exception as e:
                        print(f"参数解析错误: {str(e)}")
                        tool_args = {}
                    
                    # 记录工具调用
                    print(f"\n调用工具: {tool_name}")
                    print(f"参数: {tool_args}")
                    conversation_log.append(f"模型决定调用: {tool_name}({tool_args})")
                    
                    # 执行工具调用
                    try:
                        result = await self.session.call_tool(tool_name, tool_args)
                        tool_result = result.content
                        conversation_log.append(f"工具结果: {tool_result}")
                        
                        # 将工具调用结果添加到消息历史
                        messages.append({
                            "role": "assistant", 
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {
                                        "name": tool_name,
                                        "arguments": json.dumps(tool_args)
                                    }
                                }
                            ]
                        })
                        
                        # 添加工具结果
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_result
                        })
                        
                        # 获取最终回复
                        final_response = self.client.chat.completions.create(
                            model="deepseek-chat",
                            messages=messages,
                            max_tokens=1000
                        )
                        
                        final_content = final_response.choices[0].message.content
                        conversation_log.append(f"模型: {final_content}")
                        
                    except Exception as e:
                        error_msg = f"执行工具 {tool_name} 时出错: {str(e)}"
                        print(error_msg)
                        conversation_log.append(error_msg)
            
            # 如果没有工具调用，返回直接回复
            elif assistant_message.content:
                conversation_log.append(f"模型: {assistant_message.content}")
                
        except Exception as e:
            return f"API处理错误: {str(e)}"
            
        # 返回完整对话记录
        return "\n".join(conversation_log)

    async def chat_loop(self):
        """运行交互式聊天循环"""
        print("\nMCP客户端已启动!")
        print("输入您的问题或输入'quit'退出。")

        while True:
            try:
                query = input("\n问题: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\n错误: {str(e)}")
                import traceback
                traceback.print_exc()

    async def cleanup(self):
        """清理资源"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("用法: python deepseek_client.py <服务器脚本路径>")
        sys.exit(1)

    # DeepSeek API密钥
    api_key = "sk-5dea70724d7b4bc090b059ae4b6ca718"
    
    client = MCPClient(api_key)
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 