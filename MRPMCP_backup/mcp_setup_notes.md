# MCP服务器配置经验与教训

## 成功经验

1. **基本流程**
   - 创建使用美国国家气象服务API的天气服务器(weather.py)
   - 安装必要的依赖(mcp[cli], httpx等)
   - 配置Cursor的mcp.json文件
   - 连接测试确认工具可用

2. **解决问题的关键步骤**
   - 使用Inspector工具验证服务器功能
   - 确认正确的Python命令和路径
   - 确保所有依赖正确安装
   - 理解系统Path和命令可用性

## 遇到的问题与解决方案

1. **Python命令不可用**
   - 问题：系统找不到`python`命令
   - 错误信息：`zsh: command not found: python`
   - 解决方案：使用`python3`命令替代

2. **MCP模块缺失**
   - 问题：系统Python找不到mcp库
   - 错误信息：`ModuleNotFoundError: No module named 'mcp'`
   - 解决方案：安装依赖到系统Python：`pip3 install -r requirements.txt`

3. **路径配置错误**
   - 问题：误用虚拟环境路径，引起混淆
   - 教训：确认依赖安装位置，避免混用不同环境
   - 解决方案：确认系统Python3可访问所有所需依赖后，直接使用系统Python3

4. **Inspector连接问题**
   - 问题：Inspector显示服务器连接但工具为空
   - 原因：Python环境缺少必要的依赖
   - 解决方案：确保正确安装所有依赖

5. **Cursor配置错误**
   - 问题：Client closed错误
   - 原因：使用了错误的Python路径或命令
   - 解决方案：使用`python3`而非`python`，确保命令存在且能访问所需库

## 最佳实践

1. **环境依赖管理**
   - 明确区分系统Python和虚拟环境Python
   - 安装依赖时指定确切版本号
   - 使用`which python3`确认使用的Python解释器路径

2. **服务器测试**
   - 先使用Inspector验证服务器功能
   - 测试天气API访问是否正常
   - 确认工具参数格式是否正确

3. **配置文件策略**
   - Cursor MCP配置应尽量简单
   - 使用绝对路径避免路径解析问题
   - 配置修改后完全重启Cursor

4. **调试技巧**
   - 检查系统命令是否可用
   - 使用Inspector验证服务器功能
   - 确认API调用参数格式是否正确
   - 在简单配置工作后再尝试复杂配置

## 配置示例

### 成功的Cursor MCP配置
```json
{
  "mcpServers": {
    "weather": {
      "command": "python3",
      "args": [
        "/Users/shenruiyang/MRPMCP/weather.py"
      ]
    }
  }
}
```

## 注意事项

1. 美国国家气象服务API只支持美国境内的天气查询
2. 服务器提供的两个工具：`get_alerts`和`get_forecast`
3. MCP是正在发展的新协议，某些功能可能尚未完全支持
4. 同一台机器上的多个Python环境可能导致依赖冲突，需谨慎管理 