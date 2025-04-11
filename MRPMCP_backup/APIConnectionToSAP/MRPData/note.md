# SAP MRP API 调用成功经验

## 成功的API列表

1. MaterialCoverages API
- URL: `/sap/opu/odata/sap/API_MRP_MATERIALS_SRV_01/MaterialCoverages`
- 参数示例: 
  ```
  $filter=Material eq 'FG126' and 
          MRPPlant eq '1310' and 
          MaterialShortageProfileCount eq '001' and 
          MaterialShortageProfile eq 'SAP000000001'
  ```
- 用途：查询物料覆盖率信息

2. SupplyDemandItems API
- URL: `/sap/opu/odata/sap/API_MRP_MATERIALS_SRV_01/SupplyDemandItems`
- 参数示例:
  ```
  $filter=Material eq 'FG126' and MRPPlant eq '1310'
  ```
- 用途：查询物料的供需明细数据

3. MRPMaterial API
- URL: `/sap/opu/odata/sap/API_MRP_MATERIALS_SRV_01/A_MRPMaterial`
- 参数示例:
  ```
  $filter=Material eq 'FG126' and MRPPlant eq '1310'
  ```
- 用途：查询物料的MRP主数据

## 成功经验

1. API调用前提
- 确保使用正确的认证信息
- 检查用户权限是否完整
- 确保网络连接稳定

2. 参数设置
- 必须使用正确的过滤条件
- 参数值需要用单引号包围
- 多个条件使用 and 连接

3. 返回数据处理
- 检查返回的 __count 字段确认数据量
- 通过 __metadata 可获取详细的数据类型信息
- 注意日期格式的处理（SAP使用/Date()格式）

## 避免错误的经验教训

1. 权限问题
- 如遇到403错误，首先检查认证信息
- 确认用户是否有对应的权限
- 检查token是否过期

2. 请求格式
- URL需要包含完整的服务路径
- 参数需要正确编码
- 注意大小写敏感性

3. 数据处理
- 注意处理空值情况
- 关注数据类型转换
- 处理好日期格式转换 

# SG124物料MRP数据分析

## 1. 物料主数据
- 物料号: SG124
- 物料描述: SEMI124,PD,Subassembly
- 工厂: 1310 (CN Plant)
- 物料组: L003 (Semi-Finished Goods)
- 基本单位: PC (Piece)
- 物料类型: HALB (半成品)
- MRP控制者: 001
- 采购组: 001 (Group 001)
- 采购类型: E (内部生产)

## 2. MRP参数设置
- MRP类型: PD (预测消耗，无计划时界)
- 批量策略: EX (批量等于需求量)
- 计划交货时间: 10天
- 计划生产时间: 1天
- 总补货提前期: 2天
- 安全库存: 0
- 再订货点: 0
- 计划策略组: 40

## 3. 供需情况
### 依赖需求
- 3月21日: -100 PC
- 3月24日: -99 PC
- 3月31日: -70 PC

### 计划订单
- 4月4日: 
  * 605 PC
  * 200 PC
  * 370 PC
- 4月7日: 100 PC
- 4月30日: 200 PC
- 6月30日: 90 PC
- 8月29日: 124 PC

## 4. 库存地点
- 生产库存地点: 131B (Std. Storage 2)
- 外部采购默认库存地点: 131C

## 5. 经验总结
1. 该物料为半成品，采用内部生产方式
2. MRP类型为PD，表示使用预测消耗且无计划时界
3. 批量策略为EX，表示按实际需求量下达订单
4. 近期（3-4月）有较多依赖需求和计划订单，需要重点关注生产能力是否满足需求
5. 中长期（6-8月）需求相对较少，可以进行更灵活的生产安排

## 6. 注意事项
1. 确保生产能力满足近期大量需求
2. 关注计划订单的及时转换和执行
3. 监控实际消耗是否符合预期
4. 定期检查MRP运行结果，确保供需平衡 