from typing import Any, Dict, List
import httpx
import json
from mcp.server.fastmcp import FastMCP

# 初始化FastMCP服务器
mcp = FastMCP("sap_mrp")

# SAP API基础URL和认证信息
SAP_API_BASE_URL = "https://my200816.s4hana.sapcloud.cn:443/sap/opu/odata/sap/API_MRP_MATERIALS_SRV_01"
SAP_USERNAME = "ORB_COM"
SAP_PASSWORD = "mzXkvXJeQaBgKEVNZn6ffaJnj~KcADrMgnGalwgH"

async def make_sap_request(url: str, params: Dict[str, str]) -> Dict[str, Any]:
    """向SAP API发送请求并处理响应。"""
    auth = (SAP_USERNAME, SAP_PASSWORD)
    headers = {
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient(verify=False, auth=auth) as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return {"status": "success", "data": response.json()}
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "message": f"HTTP错误: {e.response.status_code} - {e.response.text}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"请求失败: {str(e)}"
            }

@mcp.tool()
async def get_masterdata(material: str, plant: str) -> Dict[str, Any]:
    """获取MRP物料主数据。

    Args:
        material: 物料编号 (例如: FG126)
        plant: 工厂代码 (例如: 1310)
    """
    url = f"{SAP_API_BASE_URL}/A_MRPMaterial"
    params = {
        "$filter": f"Material eq '{material}' and MRPPlant eq '{plant}'",
        "$top": "50",
        "$inlinecount": "allpages",
        "$format": "json"
    }
    
    result = await make_sap_request(url, params)
    if result["status"] == "success":
        return result["data"]
    return result

@mcp.tool()
async def get_supplydemand(material: str, plant: str) -> Dict[str, Any]:
    """获取MRP供需数据。

    Args:
        material: 物料编号 (例如: FG126)
        plant: 工厂代码 (例如: 1310)
    """
    url = f"{SAP_API_BASE_URL}/SupplyDemandItems"
    params = {
        "$filter": f"Material eq '{material}' and MRPPlant eq '{plant}'",
        "$top": "50",
        "$inlinecount": "allpages",
        "$format": "json"
    }
    
    result = await make_sap_request(url, params)
    if result["status"] == "success":
        return result["data"]
    return result

@mcp.tool()
async def get_coverage(material: str, plant: str) -> Dict[str, Any]:
    """获取MRP物料覆盖数据。

    Args:
        material: 物料编号 (例如: FG126)
        plant: 工厂代码 (例如: 1310)
    """
    url = f"{SAP_API_BASE_URL}/MaterialCoverages"
    params = {
        "$filter": f"Material eq '{material}' and MRPPlant eq '{plant}'",
        "$top": "50",
        "$inlinecount": "allpages",
        "$format": "json"
    }
    
    result = await make_sap_request(url, params)
    if result["status"] == "success":
        return result["data"]
    return result

@mcp.tool()
async def get_bom(material: str, plant: str, levels: int = 1) -> Dict[str, Any]:
    """获取物料的BOM(物料清单)数据，并可以递归展开多层级。

    Args:
        material: 物料编号 (例如: FG126)
        plant: 工厂代码 (例如: 1310)
        levels: 需要展开的BOM层级数 (默认为1，只展开顶层)
    """
    result = await get_bom_recursive(material, plant, current_level=0, max_levels=levels)
    return result

async def get_bom_recursive(material: str, plant: str, current_level: int = 0, max_levels: int = 1, processed_components=None) -> Dict[str, Any]:
    """递归获取BOM数据。
    
    这是一个内部函数，通过get_bom工具调用。
    """
    # 初始化已处理组件记录
    if processed_components is None:
        processed_components = set()
    
    # 防止重复处理同一组件
    component_key = f"{material}_{plant}"
    if component_key in processed_components:
        return {
            "status": "warning",
            "message": f"检测到循环引用: 物料 {material} 在工厂 {plant} 已被处理过",
            "material": material,
            "plant": plant
        }
    
    processed_components.add(component_key)
    
    # 步骤1: 获取BOM头信息
    bom_header_url = "https://my200816.s4hana.sapcloud.cn:443/sap/opu/odata/sap/API_BILL_OF_MATERIAL_SRV;v=0002/MaterialBOM"
    bom_header_params = {
        "$filter": f"Material eq '{material}' and Plant eq '{plant}' and BillOfMaterialVariant eq '1'",
        "$top": "50",
        "$inlinecount": "allpages",
        "$format": "json"
    }
    
    headers_result = await make_sap_request(bom_header_url, bom_header_params)
    
    if headers_result["status"] != "success" or "d" not in headers_result["data"]:
        return {
            "status": "error",
            "message": f"无法获取物料 {material} 在工厂 {plant} 的BOM头信息",
            "raw_response": headers_result
        }
    
    if headers_result["data"]["d"]["__count"] == "0":
        return {
            "status": "success",
            "message": f"物料 {material} 在工厂 {plant} 没有BOM",
            "bom_headers": [],
            "bom_items": []
        }
    
    # 提取BOM头信息
    bom_headers = headers_result["data"]["d"]["results"]
    
    # 如果达到最大层级，则不继续展开
    if current_level >= max_levels:
        return {
            "status": "success",
            "bom_headers": bom_headers,
            "message": f"已达到最大展开层级 {max_levels}，不再展开子组件",
            "bom_items": []
        }
    
    # 步骤2: 获取BOM子项
    all_items = []
    component_boms = {}
    
    for header in bom_headers:
        bom_number = header.get("BillOfMaterial")
        if not bom_number:
            continue
            
        bom_items_url = f"https://my200816.s4hana.sapcloud.cn:443/sap/opu/odata/sap/API_BILL_OF_MATERIAL_SRV;v=0002/MaterialBOMItem"
        bom_items_params = {
            "$filter": f"BillOfMaterial eq '{bom_number}'",
            "$top": "50",
            "$inlinecount": "allpages",
            "$format": "json"
        }
        
        items_result = await make_sap_request(bom_items_url, bom_items_params)
        
        if items_result["status"] != "success" or "d" not in items_result["data"]:
            continue
            
        items = items_result["data"]["d"]["results"]
        all_items.extend(items)
        
        # 步骤3: 递归获取子组件的BOM (如果需要进一步展开)
        if current_level < max_levels - 1:
            for item in items:
                component = item.get("BillOfMaterialComponent")
                if component and item.get("IsAssembly") == "X":  # 子组件是组件且标记为组件
                    sub_bom = await get_bom_recursive(
                        component, 
                        plant, 
                        current_level=current_level+1, 
                        max_levels=max_levels,
                        processed_components=processed_components
                    )
                    component_boms[component] = sub_bom
    
    return {
        "status": "success",
        "material": material,
        "plant": plant,
        "level": current_level,
        "bom_headers": bom_headers,
        "bom_items": all_items,
        "component_boms": component_boms if current_level < max_levels - 1 else {}
    }

@mcp.tool()
async def get_production_order_header(order_number: str) -> Dict[str, Any]:
    """获取生产工单的头信息。

    Args:
        order_number: 生产工单号码 (例如: 1000145)
    """
    url = "https://my200816.s4hana.sapcloud.cn:443/sap/opu/odata/sap/API_PRODUCTION_ORDER_2_SRV/A_ProductionOrder_2"
    params = {
        "$filter": f"ManufacturingOrder eq '{order_number}'",
        "$top": "50",
        "$inlinecount": "allpages",
        "$format": "json"
    }
    
    result = await make_sap_request(url, params)
    if result["status"] == "success":
        return result["data"]
    return result

@mcp.tool()
async def get_production_order_component(order_number: str) -> Dict[str, Any]:
    """获取生产工单的组件信息。

    Args:
        order_number: 生产工单号码 (例如: 1000145)
    """
    url = "https://my200816.s4hana.sapcloud.cn:443/sap/opu/odata/sap/API_PRODUCTION_ORDER_2_SRV/A_ProductionOrderComponent_2"
    params = {
        "$filter": f"ManufacturingOrder eq '{order_number}'",
        "$top": "50",
        "$inlinecount": "allpages",
        "$format": "json"
    }
    
    result = await make_sap_request(url, params)
    if result["status"] == "success":
        return result["data"]
    return result

@mcp.tool()
async def Get_PObyPO(po_number: str) -> Dict[str, Any]:
    """获取采购订单详细信息。

    Args:
        po_number: 采购订单号码 (例如: 4500000245)
    """
    url = f"https://my200816.s4hana.sapcloud.cn:443/sap/opu/odata4/sap/api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001/PurchaseOrder/{po_number}"
    params = {
        "$format": "json"
    }
    
    result = await make_sap_request(url, params)
    if result["status"] == "success":
        return result["data"]
    return result

@mcp.tool()
async def Get_POITEMbyPO(po_number: str) -> Dict[str, Any]:
    """获取采购订单行项目详细信息。

    Args:
        po_number: 采购订单号码 (例如: 4500000245)
    """
    url = f"https://my200816.s4hana.sapcloud.cn:443/sap/opu/odata4/sap/api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001/PurchaseOrder/{po_number}/_PurchaseOrderItem"
    params = {
        "$top": "50",
        "$format": "json"
    }
    
    result = await make_sap_request(url, params)
    if result["status"] == "success":
        return result["data"]
    return result

# MRP提示词功能 - 使用@mcp.prompt()装饰器
@mcp.prompt()
def mrp_analysis(material: str, plant: str, analysis_type: str = "comprehensive") -> str:
    """分析MRP数据并提供洞察

    Args:
        material: 物料编号
        plant: 工厂代码
        analysis_type: 分析类型 (shortage/coverage/demand_supply/production)
    """
    return f"""Analyze the MRP situation for material {material} at plant {plant}.

MRP is a complex, interconnected system rather than a linear process. The core data consists of:

1. Master Data:
   - Material master data (properties, planning parameters, inventory parameters)
   - BOM (Bill of Materials) defining product structure

2. MRP Demand/Supply Data:
   - Based on inventory and various documents
   - Calculates available inventory quantities by date
   - Documents include purchase orders (purchased parts), production orders (self-manufactured parts), 
     planned orders (self-manufactured parts), purchase requisitions (purchased parts), 
     and various requirements (such as independent requirements plans or sales orders)

3. Material Coverage:
   - Analytical result showing supply/demand balance over time

For this {analysis_type} analysis, focus on how the different documents interact to create the overall 
MRP situation. All data relationships should be analyzed through the central MRP data, serving as the 
interconnection point to achieve comprehensive analysis.

Please provide insights on current inventory status, upcoming requirements, planned production/procurement,
and recommendations for potential actions if any issues are identified."""

@mcp.prompt()
def production_order_analysis(order_number: str) -> str:
    """分析生产工单在MRP环境中的角色

    Args:
        order_number: 生产工单号码
    """
    return f"""Analyze production order {order_number} in the context of MRP.

Production orders are key documents in the MRP system that represent self-manufactured items. 
When analyzing a production order, consider:

1. Order Header Information:
   - Basic order data (status, dates, quantities)
   - Connection to material master and planning data
   - Current production status and schedule

2. Component Information:
   - Required components and their availability
   - Component withdrawal status
   - Potential bottlenecks in supply chain

3. MRP Context:
   - How this order impacts overall material availability
   - Relationship to dependent demand
   - Effects on downstream production or customer orders

Please analyze this production order focusing on its role within the broader MRP landscape,
examining how it connects to master data and impacts the overall supply/demand situation."""

# MRP提示词功能 - 作为DocString注释提供
"""
MRP是一个复杂的、网状关联的系统:
- 数据核心来自于MRP数据和主数据
- 主数据包括物料主数据与BOM
- 核心数据来自于MRP需求供给
- Material Coverage是需求供给的分析结果
- 数据联系应以MRP为中心进行关联
"""

# 设置服务器能力，启动服务
if __name__ == "__main__":
    # 启动MCP服务
    mcp.run(transport='stdio') 