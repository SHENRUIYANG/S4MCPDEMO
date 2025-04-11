# Material Master Data MCP Server Implementation Notes

## Overview
This document provides information about the implementation of the Material Master Data MCP server which connects to SAP systems to retrieve material data.

## Key Changes and Solutions

### Import and Configuration Issues
- Added robust error handling for MCP library imports
- Implemented a fallback to basic FastAPI if mcp-server package can't be loaded
- Added validation for .env file presence to avoid errors if configuration is missing
- Moved uvicorn import inside the run function with error handling to prevent crashes
- Changed default port from 5002 to 5003 to avoid conflicts

### Endpoint and Tool Changes
- Implemented the required MCP tools for material data:
  - `get_masterdata`: Get basic material information
  - `get_supplydemand`: Get supply and demand data (placeholder)
  - `get_coverage`: Get coverage data for a material (placeholder)
  - `get_bom`: Get bill of materials data (placeholder)
- Made all endpoints accept both material and plant parameters for consistency
- Added descriptive logging to track execution flow

### Error Prevention
- Detailed error messages with guidance for resolving issues
- Fallback mechanisms to ensure the server starts even with partial configuration
- Mock data mode automatically enabled when SAP connection details are missing

## Running the Server

### Prerequisites
1. Python 3.7 or higher
2. Required packages installed:
   ```
   pip install flask gunicorn werkzeug mcp-server PyYAML requests python-dotenv uvicorn starlette httpx mcp
   ```

### Configuration
1. Copy `.env.template` to `.env` and update with your SAP system details:
   ```
   # SAP System URL (including protocol)
   SAP_SYSTEM_URL=https://your-sap-system.example.com
   
   # SAP API Username 
   SAP_USERNAME=your_username
   
   # SAP API Password
   SAP_PASSWORD=your_password
   
   # MCP Server Port (default is 5003)
   PORT=5003
   ```

2. If SAP connection details are not provided, the server will run in mock data mode.

### Starting the Server
```bash
python3 MM03_MCP.py
```

The server will start on port 5003 (or the port specified in the .env file).

## Testing with the MCP Client

### Prerequisites
Make sure you have installed the Python MCP client library:
```
pip install mcp
```

### Running the Client
The project includes an MCP client implementation that connects to the server using the stdio transport:

```bash
python3 mm03_client.py MM03_MCP.py
```

This will:
1. Start the MM03_MCP.py server as a subprocess
2. Connect to it using the MCP stdio protocol
3. List available tools
4. Provide an interactive interface to call the different tools

### Available Commands in the Client
The interactive client provides several commands:
- `1` - Get material master data
- `2` - Get supply/demand data
- `3` - Get coverage data
- `4` - Get BOM data
- `5` - Get production order header
- `6` - Get production order component
- `q` - Quit the client

### Configuration in Cursor
To configure this MCP in Cursor:
1. Open Cursor settings
2. Navigate to the MCP Servers section
3. Add a new MCP server with:
   - Name: MM03
   - Command: python3
   - Arguments: /path/to/MM03_MCP.py

## Troubleshooting

### Common Issues

1. **Import errors with mcp-server**
   - Ensure you have installed the mcp-server package:
     ```
     pip install mcp-server
     ```
   - The server will fall back to a basic FastAPI implementation if the package is missing

2. **Port conflicts**
   - If port 5003 is already in use, change the PORT value in your .env file
   - The default port was changed from 5002 to 5003 to avoid common conflicts

3. **404 errors**
   - Verify you're using the correct endpoint paths (/mcp_MRP__get_masterdata rather than /mcp_MRP__BasicData)
   - Check that your tools are properly registered in the MCP manifest

4. **SAP Connection Issues**
   - Verify your SAP credentials and system URL in the .env file
   - Check network connectivity to the SAP system
   - Review logs for specific SAP error messages

5. **Client Connection Issues**
   - Ensure the server is running in the correct mode for client connection
   - Check server logs for any connection errors
   - Verify your mcp client library version (should be 0.1.2 or higher)

# MCP(Model Calling Protocol)开发笔记

## 成功经验

1. **正确的服务器实现**
   - 使用`FastMCP`库创建MCP服务器，简化了工具注册和服务启动流程
   - 所有工具函数必须是异步的(async)，以支持并发处理请求
   - 服务器需要使用`stdio`传输方式启动，使客户端能够通过标准输入输出与其通信

2. **标准工具定义**
   - 每个工具都需要清晰的描述和参数定义
   - 参数定义应当包含类型、是否必须、默认值等信息
   - 工具函数应当有异常处理，确保即使出错也能返回有意义的错误信息

3. **客户端实现**
   - 使用`subprocess`模块启动服务器进程
   - 使用标准的JSON-RPC 2.0格式进行通信
   - 使用行缓冲模式来确保每次请求和响应的完整性

4. **数据结构设计**
   - 为每种数据类型创建明确的结构，提高代码可读性
   - 使用mock数据进行测试，避免开发过程中对真实系统的依赖
   - 确保数据结构与前端展示需求一致

## 避免错误的经验教训

1. **通信协议错误**
   - JSON-RPC请求必须包含`jsonrpc`、`method`、`params`和`id`字段
   - 每条消息后必须有换行符`\n`，否则服务器无法正确解析
   - 客户端和服务器必须使用相同的编码(通常是UTF-8)

2. **异步处理问题**
   - 服务器工具函数必须是异步的，使用`async/await`
   - 客户端需要正确处理服务器响应，包括超时和错误情况
   - 避免在主线程中进行长时间操作，防止UI阻塞

3. **环境配置陷阱**
   - 确保安装了所有必要的依赖，包括最新版本的`mcp-server`
   - 使用`.env`文件管理环境变量，但不要将敏感信息提交到代码库
   - 测试环境和生产环境的配置应该分开管理

4. **调试困难**
   - 实现详细的日志记录，记录每次请求和响应
   - 在开发阶段使用模拟数据，简化测试流程
   - 使用`stderr`输出调试信息，不影响正常的`stdout`通信

## MCP工具设计最佳实践

1. **工具命名规范**
   - 使用动词开头，清晰表达功能，如`get_masterdata`、`update_order`
   - 保持一致的命名风格，便于使用和维护

2. **参数设计**
   - 必要参数应标记为required
   - 对每个参数提供清晰的描述
   - 为可选参数提供合理的默认值

3. **返回值设计**
   - 统一返回结构，包含状态码和数据字段
   - 错误信息应当明确且有帮助性
   - 大型数据集考虑分页或过滤机制

4. **安全考虑**
   - 验证所有输入参数，防止注入攻击
   - 限制服务器资源使用，防止DoS攻击
   - 敏感数据应当加密存储和传输

## 下一步改进计划

1. 添加身份验证机制，确保只有授权用户可以访问API
2. 实现更多数据过滤和查询选项，提高灵活性
3. 添加缓存机制，提高频繁请求的响应速度
4. 完善错误处理和日志记录，便于问题排查

# SAP MCP服务器配置经验与教训

## 成功实现SAP MCP服务器

### FastMCP服务器实现步骤
1. **正确导入FastMCP**
   ```python
   from mcp.server.fastmcp import FastMCP
   ```

2. **初始化FastMCP服务器**
   ```python
   mcp = FastMCP("MM03")  # 服务器名称
   ```

3. **注册工具函数**
   ```python
   @mcp.tool()
   async def get_masterdata(material: str, plant: str) -> Dict[str, Any]:
       """获取MRP物料主数据。
       
       Args:
           material: 物料编号 (例如: FG126)
           plant: 工厂代码 (例如: 1310)
       """
       # 实现代码...
   ```

4. **启动服务器（HTTP模式）**
   ```python
   mcp.run(transport='http', host='0.0.0.0', port=5003)
   ```

### 关键配置注意事项
1. **传输模式选择**
   - `stdio`：用于Cursor或命令行交互
   - `http`：用于网络服务，包括Web应用、API客户端访问

2. **文档字符串格式**
   - 工具函数必须有详细的文档字符串
   - 参数描述格式必须符合规范（Args: 部分）
   - 返回值类型提示必须正确

## 常见问题与解决方案

### manifest 404错误
- **问题**: 访问`/.well-known/mcp-manifest.json`返回404错误
- **原因**: 使用FastMCP时，transport参数设置不正确
- **解决方案**: 使用`transport='http'`并提供`host`和`port`参数

### SAP连接问题
- **问题**: SAP连接失败或超时
- **原因**: 
  1. SAP系统URL、用户名或密码错误
  2. 网络连接问题或防火墙限制
- **解决方案**:
  1. 验证SAP连接参数
  2. 实现数据模拟模式用于开发和测试

### 依赖安装问题
- **问题**: 找不到MCP模块
- **原因**: mcp-server包未正确安装
- **解决方案**: `pip install mcp-server==0.1.3`

## 最佳实践

1. **使用环境变量管理配置**
   ```python
   # 加载环境变量
   env_path = Path('.') / '.env'
   if env_path.exists():
       dotenv.load_dotenv(dotenv_path=env_path)
   ```

2. **实现模拟数据模式**
   ```python
   if sap_config.mock_mode:
       return get_mock_material_data(material, plant)
   ```

3. **日志记录**
   ```python
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   logger = logging.getLogger("MM03_MCP")
   ```

4. **错误处理与异常捕获**
   ```python
   try:
       # API调用代码
   except Exception as e:
       logger.error(f"Error in SAP API call: {str(e)}")
       return {"status": "error", "message": str(e)}
   ```

5. **命令行参数支持**
   ```python
   parser = argparse.ArgumentParser(description="MM03 MCP Server")
   parser.add_argument("--host", type=str, default="0.0.0.0", help="Host")
   parser.add_argument("--port", type=int, default=5003, help="Port")
   args = parser.parse_args()
   ```

## 测试与验证

1. **使用curl测试manifest**
   ```bash
   curl http://localhost:5003/.well-known/mcp-manifest.json
   ```

2. **使用API工具（如Postman）测试工具**
   - 测试获取物料主数据API
   - 验证JSON响应格式

3. **Python客户端测试**
   ```python
   import httpx
   response = httpx.post("http://localhost:5003/mcp_MM03_get_masterdata", 
                         json={"material": "FG126", "plant": "1310"})
   print(response.json())
   ```

## 注意事项与教训

1. MCP是一个新兴协议，具体实现可能随版本变化
2. SAP API调用需要考虑性能与超时设置
3. 通过参数化配置增强代码可维护性
4. 为每个工具函数提供全面的文档字符串
5. HTTP模式下必须确保manifest端点可访问

# FastMCP服务器配置经验与教训

## 成功实现HTTP模式的MCP服务器

### 关键发现
1. **FastMCP版本限制**
   - mcp-server 0.1.3版本**不支持**直接通过transport='http'启动HTTP服务
   - 正确方法是手动实现基于FastAPI的HTTP服务，并提供MCP清单和工具端点

2. **正确的HTTP模式实现方式**
   ```python
   # 导入必要模块
   import uvicorn
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware
   from pydantic import BaseModel
   
   # 创建FastAPI应用
   app = FastAPI(title="Material Master Data MCP")
   
   # 添加CORS中间件
   app.add_middleware(CORSMiddleware, allow_origins=["*"])
   
   # 定义模型
   class MaterialPlantRequest(BaseModel):
       material: str
       plant: str
   
   # 实现MCP清单端点 - 最关键的部分
   @app.get("/.well-known/mcp-manifest.json")
   async def get_manifest():
       manifest = {
           "schema_version": "v1",
           "name_for_model": "mcp_MRP_",
           "tools": [
               {
                   "name": "get_masterdata",
                   "description": "获取MRP物料主数据",
                   "input_schema": {
                       "type": "object",
                       "properties": {
                           "material": {"type": "string"},
                           "plant": {"type": "string"}
                       },
                       "required": ["material", "plant"]
                   }
               }
           ]
       }
       return manifest
   
   # 实现工具端点
   @app.post("/mcp_MRP__get_masterdata")
   async def api_get_masterdata(request: MaterialPlantRequest):
       # 调用实际的工具函数
       result = await get_masterdata(request.material, request.plant)
       return result
   
   # 启动服务器
   uvicorn.run(app, host="0.0.0.0", port=5003)
   ```

### 使用stdio模式
- 对于CLI或Cursor插件，使用stdio模式，直接使用FastMCP的run方法：
  ```python
  mcp.run(transport='stdio')
  ```

## 常见错误与解决方案

### 1. Manifest 404错误
- **现象**: 访问`/.well-known/mcp-manifest.json`返回404
- **原因**: FastMCP不支持直接HTTP模式，缺少清单端点
- **解决方案**: 手动实现FastAPI应用并添加清单端点

### 2. "unexpected keyword 'host'" 错误
- **现象**: `FastMCP.run() got an unexpected keyword argument 'host'`
- **原因**: 尝试向FastMCP.run传递HTTP参数
- **解决方案**: 使用FastAPI和uvicorn替代HTTP服务

### 3. "module not found" 错误
- **现象**: `ModuleNotFoundError: No module named 'mcp.transport'`
- **原因**: mcp-server版本限制，不支持某些功能
- **解决方案**: 检查mcp-server版本，使用兼容方法

## 关键经验教训

1. **理解FastMCP的局限性**
   - FastMCP在当前版本(0.1.3)不提供完整的HTTP服务支持
   - HTTP模式需要手动实现FastAPI应用

2. **MCP清单格式的重要性**
   - MCP清单格式必须严格遵循规范
   - 工具输入schema必须正确定义
   - 所有属性名称需遵循约定

3. **端点命名规则**
   - 工具端点必须按照`/mcp_[服务名]_[工具名]`格式命名
   - 在本例中：`/mcp_MRP__get_masterdata`

4. **模拟数据模式的价值**
   - 实现mock模式可快速开发和测试，无需SAP连接
   - 提供合理的模拟数据结构，便于前端开发

## 测试方法

1. **验证清单端点**
   ```bash
   curl http://localhost:5003/.well-known/mcp-manifest.json
   ```

2. **测试工具端点**
   ```bash
   curl -X POST http://localhost:5003/mcp_MRP__get_masterdata \
     -H "Content-Type: application/json" \
     -d '{"material":"FG126","plant":"1310"}'
   ```

3. **验证健康检查**
   ```bash
   curl http://localhost:5003/health
   ```

## 实现MCP服务器的最佳实践

1. **使用`argparse`支持不同的运行模式**
   ```python
   parser.add_argument("--mode", choices=["stdio", "http"], default="stdio")
   ```

2. **提供全面的日志记录**
   ```python
   logger.info(f"Starting server in {mode} mode on {host}:{port}")
   ```

3. **结构化错误处理**
   ```python
   try:
       # 代码
   except Exception as e:
       return {"status": "error", "message": str(e)}
   ```

4. **遵循MCP命名规范**
   - 服务名：简短有意义
   - 工具名：动词+名词结构
   - 端点：统一前缀`mcp_[服务名]_` 

## Successful Implementation Points
- ✅ Dual mode operation (HTTP and stdio) providing flexibility in deployment
- ✅ Comprehensive error handling and logging
- ✅ Clear API documentation with OpenAPI/Swagger support
- ✅ Health check endpoint for monitoring
- ✅ CORS middleware for web client support
- ✅ Type validation using Pydantic models

## Areas for Improvement
1. Security Considerations:
   - Move credentials to `.env` file
   - Implement proper SSL/TLS certificate verification
   - Add API key authentication for HTTP mode
   - Consider implementing rate limiting

2. Performance Optimizations:
   - Add caching layer for frequently accessed material data
   - Implement connection pooling for SAP API calls
   - Add request timeout configurations

3. Monitoring and Maintenance:
   - Add more detailed logging for debugging
   - Implement metrics collection
   - Add request tracing

## Best Practices to Follow
1. Environment Configuration:
   ```python
   # Use .env file for all sensitive data
   SAP_HOST=my200816.s4hana.sapcloud.cn
   SAP_PORT=443
   SAP_USER=your_user
   SAP_PASSWORD=your_password
   ```

2. Certificate Verification:
   - Always use proper certificate verification in production
   - If needed, specify custom certificate authority:
   ```python
   client = httpx.AsyncClient(verify="/path/to/certificate.pem")
   ```

3. Error Handling:
   - Implement specific error types for different failure scenarios
   - Add proper error messages for client debugging
   - Include request ID in responses for tracing

## Common Pitfalls to Avoid
- Don't disable SSL verification in production
- Don't hardcode credentials in source code
- Don't leave default values for critical configurations
- Don't skip input validation
- Don't ignore error logging

## Testing Guidelines
- Unit tests for each function
- Integration tests for SAP API communication
- Load testing for HTTP mode
- Security testing for authentication and authorization 

# Material Master Data MCP 项目笔记

## 成功实现要点

1. API路径配置
   - ✅ 正确的SAP OData API端点:
     - 基本信息: `/sap/opu/odata4/sap/api_product/srvd_a2x/sap/product/0002/Product/{material}`
     - 物料描述: `/sap/opu/odata4/sap/api_product/srvd_a2x/sap/product/0002/ProductDescription`
   - ✅ 合适的查询参数格式 (使用适当的过滤器表达式)

2. 多语言支持
   - ✅ 灵活的语言查询支持
   - ✅ 可以查询单一语言或所有语言
   - ✅ 适当的返回字段映射

3. 错误处理
   - ✅ 良好的异常捕获
   - ✅ 清晰的错误消息

4. 双模式支持
   - ✅ HTTP API 模式
   - ✅ 标准输入/输出模式

## 避免错误的经验与教训

1. API测试的重要性
   - ❗ 在开发前查看API示例文件，理解正确的端点和参数
   - ❗ 测试不同的API路径，找到正确的端点
   - ❗ 使用curl等工具进行手动测试，确认API工作正常

2. API路径问题
   - ❗ 避免使用错误的API路径(`API_MATERIAL_DOCUMENT_SRV`)
   - ❗ 使用正确的路径(`api_product/srvd_a2x/sap/product/0002/`)
   - ❗ 确保过滤条件格式正确，例如`contains(ProductDescription, 'text')`

3. 模拟数据使用
   - ❗ 当API连接有问题时，可以临时使用模拟数据进行开发
   - ❗ 但确保最终版本使用正确的API实现

4. 权限和认证
   - ❗ 确保具有适当的SAP系统访问权限
   - ❗ 根据需要处理CSRF令牌
   - ❗ 考虑安全性，避免在代码中硬编码凭据

5. 端口使用
   - ❗ 检查端口是否被占用，如有问题可以更改端口
   - ❗ 使用pkill等命令清理占用端口的进程

## 进一步改进建议

1. 安全性
   - 添加身份验证
   - 使用HTTPS
   - 将凭据移至更安全的存储

2. 性能优化
   - 添加缓存
   - 实现连接池
   - 优化查询方式

3. 可用性
   - 添加更多搜索参数
   - 提供更多返回字段选项
   - 改进错误处理和指导性提示

4. 可维护性
   - 单元测试
   - 集成测试
   - 监控和日志功能

## 技术栈总结

- FastAPI: 提供HTTP API功能
- FastMCP: 实现MCP协议
- httpx: 异步HTTP客户端
- Pydantic: 数据验证和类型安全
- Uvicorn: ASGI服务器
- Python-dotenv: 环境变量管理 