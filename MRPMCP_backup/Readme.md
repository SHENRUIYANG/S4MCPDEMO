# MCP客户端和服务器示例

这个项目包含基于MCP(Model Context Protocol)的服务和使用DeepSeek API的客户端。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 服务器

项目包含两个服务器：

### 1. 天气服务

天气服务可以提供以下功能：

1. 获取美国各州的天气警报
2. 获取特定位置的天气预报

#### 运行天气服务器

```bash
python weather.py
```

### 2. MRP服务

MRP服务提供SAP系统数据查询功能：

1. 获取物料主数据
2. 获取供需数据
3. 获取库存覆盖数据
4. 获取物料清单(BOM)
5. 获取生产工单头信息
6. 获取生产工单组件信息

#### 运行MRP服务器

```bash
python MRP.py
```

## 客户端

客户端使用DeepSeek API与服务器通信，允许用户通过自然语言与服务器交互。

### 运行客户端

```bash
# 连接天气服务
python deepseek_client.py weather.py

# 连接MRP服务
python deepseek_client.py MRP.py
```

### 使用示例

一旦客户端启动，您可以输入自然语言查询，例如：

#### 天气服务查询示例：
- "纽约州有天气警报吗？"
- "旧金山的天气预报是什么？"
- "检查加利福尼亚的天气警报"
- "获取37.7749,-122.4194这个位置的天气预报"

#### MRP服务查询示例：
- "查询物料FG126在工厂1310的主数据"
- "获取物料RM778在工厂1410的供需情况"
- "显示工单1000567的头信息"
- "列出工单1000789的所有组件"

输入"quit"可以退出客户端。

## 项目结构

- `weather.py`: MCP天气服务器实现
- `MRP.py`: MCP MRP服务器实现，连接SAP系统
- `deepseek_client.py`: 使用DeepSeek API的MCP客户端
- `requirements.txt`: 项目依赖
- `README.md`: 项目说明
- `note.md`: 开发笔记和经验总结 