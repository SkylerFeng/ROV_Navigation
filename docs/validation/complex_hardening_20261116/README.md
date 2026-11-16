# 复杂场景修正证据

- [检测指标对照](detection_comparison.png)：旧模型与候选模型，原测试集和留出布局。
- [难例示例](samples.png)、[遮挡方块](box_partial_views.png)：原布局离线视角，框来自实例分割。
- [诊断路径对照](diagnostic_path_comparison.png)：第二轮碰壁与第三轮无接触超时，均为实测路径。
- [池体碰撞先验与旧路径](static_prior.png)：只包含池体已知碰撞网格。
- `layout_preservation.json`：三份 USD 哈希与原测试一致。
- `static_clearance_checks.json`：旧东侧接触中心到新增占用格约 0.052m。
- [第一轮诊断](diagnostic_v1/README.md)：主动中止，不完整，不计为正式结果。
- [第二轮完整失败](diagnostic_v2/README.md)：420s 超时，北壁接触；类别冲突保护有效但整体未达标。
- `evaluation.json`、`runtime_detection_eval.json`：检测汇总与固定阈值逐图结果；中心目标子集两模型相同，不夸大提升。

完整说明与启动命令：`../../complex_hardening_20261116.md`。[第三轮结果](diagnostic_v3/README.md)：0.40m 安全配置避免接触，但目标拒绝和超时仍存在。[第四轮结果](diagnostic_v4/README.md)：方形膨胀、零接触，但仍超时。第五轮增加复用已知走廊的显式跨区转移。

## 最终结果

[最终三场景实测](latest/README.md)、[轨迹总图](latest/complex_scenes.png)。三场均超时；本版未通过端到端验收。错误先验场景零接触，西侧仅接近报告无冲量，东侧设备挡板一次小冲量。不得将检测指标提升等同于导航稳定性提升。
