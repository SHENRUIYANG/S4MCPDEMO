import inspect
import sys
import json

# 动态导入MRP模块
print("尝试导入MRP模块...")
try:
    from MRP import mcp
    print("MRP模块导入成功")
except Exception as e:
    print(f"导入MRP模块失败: {str(e)}")
    sys.exit(1)

# 查看模块属性
print("\n模块属性:")
module_attrs = dir(mcp)
print(module_attrs)

# 寻找工具函数
print("\n寻找工具函数:")
tool_funcs = []
prompt_funcs = []

# 列出所有工具函数
for name in module_attrs:
    if name.startswith("__"):
        continue
        
    func = getattr(mcp, name)
    
    # 检查是否为工具函数
    is_tool = False
    is_prompt = False
    
    if callable(func):
        print(f"\n检查函数: {name}")
        # 通过多种方式检测
        if hasattr(func, "__mcp_tool__"):
            is_tool = func.__mcp_tool__
            print(f"函数 {name} 的 __mcp_tool__ 属性: {is_tool}")
        
        # 检查提示词
        if hasattr(func, "__mcp_prompt__"):
            is_prompt = func.__mcp_prompt__
            print(f"函数 {name} 的 __mcp_prompt__ 属性: {is_prompt}")
            
        # 检查函数签名
        try:
            sig = inspect.signature(func)
            print(f"函数签名: {sig}")
        except Exception as e:
            print(f"获取函数签名失败: {str(e)}")
        
        # 如果是指定的函数名，直接加入工具列表
        if name in ["get_masterdata", "get_supplydemand", "get_coverage", "get_bom", 
                   "get_production_order_header", "get_production_order_component", 
                   "Get_PObyPO", "Get_POITEMbyPO"]:
            print(f"函数 {name} 是已知工具函数")
            tool_funcs.append({"name": name, "doc": func.__doc__ or ""})
        
        # 如果是指定的提示词名，直接加入提示词列表
        if name in ["mrp_analysis", "production_order_analysis"]:
            print(f"函数 {name} 是已知提示词函数")
            prompt_funcs.append({"name": name, "doc": func.__doc__ or ""})

# 输出结果
print("\n找到工具函数:")
print(json.dumps(tool_funcs, indent=2))

print("\n找到提示词函数:")
print(json.dumps(prompt_funcs, indent=2))

# 测试调用一个工具函数
print("\n尝试调用 get_masterdata 函数:")
if hasattr(mcp, "get_masterdata"):
    print("get_masterdata 函数存在")
    func = getattr(mcp, "get_masterdata")
    print(f"函数类型: {type(func)}")
    print(f"是否可调用: {callable(func)}")
    print("函数签名:", inspect.signature(func))
else:
    print("get_masterdata 函数不存在") 