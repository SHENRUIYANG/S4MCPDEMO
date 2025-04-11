# Material Master Data MCP 实现经验记录

## API Key 实现方案

### 成功经验

1. JWT 作为 API Key 的选择原因：
   - 自包含：包含所有必要的 SAP 连接信息
   - 安全性：使用密钥签名，防止篡改
   - 过期机制：内置过期时间控制
   - 无状态：不需要服务器存储，减少复杂性

2. API Key 生成工具的设计：
   - 命令行工具方便集成
   - 清晰的使用说明输出
   - 灵活的参数配置
   - 安全的密钥处理

3. 认证流程设计：
   - 支持 Bearer Token 认证
   - 兼容 Basic Auth 作为备选
   - 优雅的错误处理
   - 清晰的错误消息

### 避免的错误

1. 安全性陷阱：
   - ❌ 不要在代码中硬编码 JWT 密钥
   - ❌ 不要使用弱加密算法
   - ❌ 不要忽略 Token 过期检查
   - ✅ 使用环境变量存储敏感信息
   - ✅ 使用强加密算法（HS256）
   - ✅ 实现完整的 Token 验证

2. 架构设计：
   - ❌ 不要将用户凭据存储在服务器
   - ❌ 不要使用复杂的数据库存储
   - ✅ 使用无状态的 JWT 设计
   - ✅ 将认证逻辑解耦

3. 用户体验：
   - ❌ 不要忽略错误处理
   - ❌ 不要使用晦涩的错误消息
   - ✅ 提供清晰的使用说明
   - ✅ 实现优雅的错误处理

## MCP.so 部署注意事项

1. 配置文件：
   - 确保 chatmcp.yaml 包含所有必要参数
   - 使用环境变量传递敏感信息
   - 提供合理的默认值

2. 依赖管理：
   - 指定具体的版本号
   - 使用兼容的依赖组合
   - 避免不必要的依赖

3. 文档完整性：
   - 提供详细的安装说明
   - 包含使用示例
   - 说明安全注意事项

## 最佳实践总结

1. 安全性：
   - 使用 JWT 进行认证
   - 实现 Token 过期机制
   - 安全传输敏感信息
   - 提供清晰的安全指南

2. 可维护性：
   - 模块化的代码结构
   - 完整的错误处理
   - 清晰的日志记录
   - 详细的文档说明

3. 用户友好：
   - 简单的配置过程
   - 清晰的使用说明
   - 直观的错误提示
   - 完整的示例代码

# MCP.so Hosting Experience

This document captures our experience with preparing the Material Master Data MCP service for hosting on MCP.so.

## Key Modifications for MCP.so Deployment

1. **Parameter Handling**
   - Added `get_param_value()` function to properly handle parameters from command line or environment variables
   - Updated all credential handling to use this function for flexibility

2. **Authentication Handling**
   - Added `get_auth_value()` function to extract authentication from request headers
   - Modified API endpoints to use these authentication values when available

3. **REST Transport Mode**
   - Added support for REST transport mode alongside existing HTTP and stdio modes
   - Implemented proper server connection for REST mode

4. **Configuration Files**
   - Created `Dockerfile` for containerization
   - Added `chatmcp.yaml` with proper configuration for MCP.so

## Best Practices

1. **No Hardcoded Credentials**
   - All credentials are now provided through parameters or environment variables
   - Added support for authentication through request headers

2. **Flexible Configuration**
   - Server can be run in multiple modes (stdio, http, rest)
   - All server settings are configurable via command line arguments

3. **Error Handling**
   - Improved error handling and logging
   - Proper error responses with clear messages

4. **Documentation**
   - Updated README.md with MCP.so hosting information
   - Added Docker deployment instructions

## Lessons Learned

1. **Parameter Handling is Critical**
   - For MCP.so compatibility, proper parameter handling is essential
   - Command line parameters should take precedence over environment variables

2. **Authentication Flexibility**
   - Support multiple authentication methods for greater flexibility
   - Headers-based authentication allows for more secure credential passing

3. **Transport Modes**
   - Supporting multiple transport modes increases service compatibility
   - REST transport is essential for MCP.so hosting

4. **Configuration Files**
   - `chatmcp.yaml` is the key configuration file for MCP.so hosting
   - Proper documentation of parameters helps users understand how to configure the service

## MCP.so Deployment Steps

1. Push code to GitHub repository: https://github.com/SHENRUIYANG/S4MCPDEMO.git
2. Visit MCP.so and submit the repository for review
3. Once approved, the service will be available on MCP.so
4. Users will need to provide SAP credentials when using the service

## Future Improvements

1. **Enhanced Authentication**
   - Implement OAuth or token-based authentication
   - Support credential storage in secure vaults

2. **More SAP APIs**
   - Expand support for additional SAP APIs
   - Implement batch operations for better performance

3. **Caching**
   - Add caching for frequently accessed data
   - Implement proper cache invalidation mechanisms

4. **Metrics and Monitoring**
   - Add prometheus metrics for monitoring
   - Implement health checks with detailed status information

## SAP API 连接问题修复 (2024-04-11)

### 问题描述

在测试 `/mcp_MM03_DescToMaterial` 和 `/mcp_MM03_Description_Search` API 时，发现出现 JSON 解析错误：`Expecting value: line 1 column 1 (char 0)`。这表明 SAP API 返回了 HTTP 200 状态码，但响应主体为空或不是有效的 JSON 格式。

### 解决方案

1. **增强错误处理和日志记录**：
   - 添加详细的日志记录，包括请求参数、响应状态码、响应头和响应长度
   - 添加特定的错误类型处理（HTTP 错误、连接错误、JSON 解析错误）
   - 增加超时设置（30秒），防止请求无限期挂起

2. **改进 HTTP 客户端配置**：
   - 增加请求超时配置
   - 更加详细的请求/响应日志
   - 适当的错误信息输出

3. **全面的状态检查**：
   - 检查 HTTP 状态码，确保是 200 成功
   - 检查响应内容是否为空
   - 检查解析后的 JSON 是否包含预期字段

### 如何使用

1. **查找带"序列"的物料**：
   ```
   curl -X POST "http://127.0.0.1:5010/mcp_MM03_DescToMaterial" \
   -H "Content-Type: application/json" \
   -H "Authorization: Bearer YOUR_API_KEY" \
   -d '{"description": "序列", "language": "ZH", "max_results": 10}'
   ```

2. **获取物料的英文描述**：
   ```
   curl -X POST "http://127.0.0.1:5010/mcp_MM03_Description_Search" \
   -H "Content-Type: application/json" \
   -H "Authorization: Bearer YOUR_API_KEY" \
   -d '{"material": "MATERIAL_NUMBER", "language": "EN"}'
   ```

### 后续计划

1. 添加自动重试机制，处理临时性网络问题
2. 实现连接池，提高性能和连接复用
3. 添加监控和告警功能，及时发现 API 问题
4. 实现更适合生产环境的日志级别控制

### 经验教训

1. SAP API 集成需要全面的错误处理策略
2. 详细的日志记录对于排查 API 问题至关重要
3. 应该直接解决根本问题，而不是依赖临时解决方案
4. API 测试应该包括各种边缘情况和错误场景

## SAP API 认证问题修复 (2024-04-11)

### 问题描述

在与SAP系统集成时，仅使用基本认证（用户名和密码）不足以正确访问API。SAP OData API需要一个多步骤的认证过程，包括CSRF令牌和会话cookie。

### 解决方案

1. **实现两步认证流程**：
   - 第一步：使用基本认证发送初始请求，同时请求CSRF令牌（`x-csrf-token: fetch`）
   - 第二步：使用获取到的CSRF令牌和会话cookie发送实际API请求

2. **CSRF令牌处理**：
   - 在第一个请求中添加`x-csrf-token: fetch`头
   - 从响应头中提取`x-csrf-token`值
   - 在后续请求中使用这个令牌

3. **会话管理**：
   - 保留第一个请求建立的会话cookie
   - 在后续请求中使用这些cookie维持会话

### 实现细节

```python
# 第一步：建立会话并获取CSRF token
session_response = await client.get(url, auth=auth, headers={"x-csrf-token": "fetch"})
            
# 提取CSRF token和cookies
csrf_token = session_response.headers.get("x-csrf-token")
cookies = session_response.cookies

# 第二步：使用token和cookies发送实际请求
response = await client.get(
    url, 
    auth=auth, 
    params=params, 
    headers={"x-csrf-token": csrf_token},
    cookies=cookies
)
```

### 深入解析

1. **为什么需要CSRF令牌**：
   - SAP使用CSRF令牌防止跨站请求伪造攻击
   - 任何修改数据的请求（POST/PUT/DELETE）都需要有效的CSRF令牌
   - 即使是GET请求，在某些SAP配置下也需要这个令牌

2. **会话处理的重要性**：
   - SAP OData API使用会话来维护状态
   - 会话cookies包含重要的认证信息
   - 不正确地处理会话可能导致"Unauthorized"错误

### 经验教训

1. SAP API集成需要理解其特有的认证机制
2. 即使是标准的OData接口，SAP也有其特殊的安全要求
3. 详细的日志记录对于排查认证问题至关重要
4. API密钥应包含所有必要的SAP连接信息（主机、端口、用户名、密码） 