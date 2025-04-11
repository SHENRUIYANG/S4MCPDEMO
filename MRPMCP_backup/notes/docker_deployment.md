# MCP服务器Docker部署指南

## 环境准备

1. 确保安装了Docker和Docker Compose
   ```bash
   docker --version
   docker-compose --version
   ```

## 部署步骤

1. 构建并启动容器
   ```bash
   docker-compose up -d
   ```

2. 检查容器是否正常运行
   ```bash
   docker ps
   ```
   
3. 查看日志
   ```bash
   docker logs -f mrpmcp_mcp-server_1
   ```

## 访问服务器

- MCP服务器运行在 http://localhost:8080
- 如需从其他设备访问，将localhost替换为服务器IP地址

## 与Cursor连接

1. 配置Cursor连接
   - 将连接地址设置为 `http://[服务器IP]:8080`
   - 确保防火墙未阻止8080端口

2. 测试连接
   ```python
   import httpx
   
   response = httpx.get("http://localhost:8080/tools")
   print(response.json())
   ```

## 常见问题排查

1. 容器无法启动
   - 检查端口是否被占用：`lsof -i :8080`
   - 检查日志：`docker logs mrpmcp_mcp-server_1`

2. 连接超时
   - 确认容器正在运行：`docker ps`
   - 检查防火墙设置：`sudo ufw status`

3. 服务器运行但API调用失败
   - 检查环境变量是否正确
   - 查看容器日志：`docker logs mrpmcp_mcp-server_1`

## 维护与更新

1. 更新服务器
   ```bash
   git pull
   docker-compose down
   docker-compose up -d --build
   ```

2. 备份数据
   ```bash
   docker cp mrpmcp_mcp-server_1:/app/notes ./backup/notes_$(date +%Y%m%d)
   ```

## 经验与教训

1. 始终通过环境变量传递敏感信息，避免硬编码
2. 使用卷挂载保存重要数据，避免容器重启导致数据丢失
3. 端口映射配置错误是最常见的连接问题原因
4. 在生产环境中应考虑使用HTTPS加密连接 

## Docker部署总结

我们成功使用Docker容器化部署了MCP服务器，主要实现了以下内容：

1. 创建了基于Python 3.10的Docker镜像
2. 直接从GitHub安装了MCP SDK
3. 通过FastAPI创建了HTTP包装层，使MCP服务可以通过HTTP协议访问
4. 实现了以下API端点：
   - `GET /`: 服务器基本信息
   - `GET /tools`: 查询所有可用工具
   - `GET /prompts`: 查询所有可用提示词
   - `POST /tools/{tool_name}`: 执行指定工具
   - `POST /prompts/{prompt_name}`: 执行指定提示词

### 成功经验

1. 镜像基础设置：
   - 使用Python 3.10而非3.9，因为MCP SDK要求Python 3.10+
   - 安装git以支持从GitHub安装SDK
   - 确保安装所有必要依赖（httpx, fastapi, uvicorn等）

2. MCP集成：
   - 了解MCP服务的本质是没有内置HTTP服务器的
   - 创建FastAPI包装器解决了MCP不直接支持HTTP的问题
   - 使用inspect模块动态发现和暴露MCP工具和提示词

3. Docker配置：
   - 端口映射（8080:8080）确保容器外可以访问服务
   - 使用docker-compose简化部署过程
   - 使用环境变量传递敏感信息

### 注意事项

1. 安全考虑：
   - 生产环境应使用HTTPS
   - 考虑添加身份验证保护API
   - 敏感信息（如SAP凭据）应通过环境变量或安全存储传递

2. 性能和可靠性：
   - 考虑添加健康检查确保服务正常运行
   - 添加日志记录以便于故障排查
   - 考虑使用Docker Swarm或Kubernetes进行扩展和高可用

3. 常见问题：
   - MCP SDK版本兼容性问题
   - 环境变量配置错误
   - 网络连接问题

### Cursor连接配置

要在Cursor中连接Docker化的MCP服务器，需要：

1. 在Cursor设置中配置MCP连接URL为：`http://localhost:8080`
2. 确保8080端口在主机上可访问
3. 如果部署在远程服务器，使用服务器IP地址替换localhost

这种Docker化部署方式非常适合开发、测试和生产环境，提供了良好的隔离性和可移植性。 