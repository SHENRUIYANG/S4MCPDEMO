import requests
import json
from datetime import datetime

# SAP系统配置
BASE_URL = "https://my200816.s4hana.sapcloud.cn:443"
USERNAME = "ORB_COM"
PASSWORD = "mzXkvXJeQaBgKEVNZn6ffaJnj~KcADrMgnGalwgH"

def test_material_coverages():
    """测试MaterialCoverages API"""
    url = f"{BASE_URL}/sap/opu/odata/sap/API_MRP_MATERIALS_SRV_01/MaterialCoverages"
    params = {
        "$filter": "Material eq 'SG124' and MRPPlant eq '1310' and MaterialShortageProfileCount eq '001' and MaterialShortageProfile eq 'SAP000000001'",
        "$top": "50",
        "$inlinecount": "allpages"
    }
    response = requests.get(url, params=params, auth=(USERNAME, PASSWORD), verify=False)
    print("MaterialCoverages API Response:", response.status_code)
    print("Headers:", response.headers)
    print("Content:", response.text)

def test_supply_demand_items():
    """测试SupplyDemandItems API"""
    url = f"{BASE_URL}/sap/opu/odata/sap/API_MRP_MATERIALS_SRV_01/SupplyDemandItems"
    params = {
        "$filter": "Material eq 'SG124' and MRPPlant eq '1310'",
        "$top": "50",
        "$inlinecount": "allpages"
    }
    response = requests.get(url, params=params, auth=(USERNAME, PASSWORD), verify=False)
    print("\nSupplyDemandItems API Response:", response.status_code)
    print("Headers:", response.headers)
    print("Content:", response.text)

def test_mrp_material():
    """测试MRPMaterial API"""
    url = f"{BASE_URL}/sap/opu/odata/sap/API_MRP_MATERIALS_SRV_01/A_MRPMaterial"
    params = {
        "$filter": "Material eq 'SG124' and MRPPlant eq '1310'",
        "$top": "50",
        "$inlinecount": "allpages"
    }
    response = requests.get(url, params=params, auth=(USERNAME, PASSWORD), verify=False)
    print("\nMRPMaterial API Response:", response.status_code)
    print("Headers:", response.headers)
    print("Content:", response.text)

if __name__ == "__main__":
    print(f"Testing APIs at {datetime.now()}")
    print("=" * 80)
    
    # 测试所有API
    test_material_coverages()
    test_supply_demand_items()
    test_mrp_material() 