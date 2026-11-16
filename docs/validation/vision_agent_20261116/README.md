# 2026-11-16 视觉与 Agent 验证

## 入口

- [最终 Agent 原图路径](qwen_yellow_final/trajectory.png)
- [最终 Agent 行动与逐轮反馈](qwen_yellow_final/agent_trace.md)
- [最终相机原图](qwen_yellow_final/last_camera_raw.png)
- [最终检测图](qwen_yellow_final/latest_detection.jpg)
- [视觉方法图像对比](vision_test/comparison.png)
- [72 帧检测评估](vision_test/metrics.csv)
- [RGB-D 黄箱对比](rgbd/yellow_box_rgbd_comparison.png)
- [100 项测试](tests.txt)

## 实际导航结果

全部使用真实 Qwen API（qwen-plus）、同一黄箱场景、固定深度与部件级水动力；headless 渲染相机。各配置一次，raw 初版另有最终版复测。

| 配置 | 仿真秒 | 航程m | 接触物体对数 | 离线审核 |
|---|---:|---:|---:|---|
| [qwen_yellow_baseline](qwen_yellow_baseline/agent_trace.md) | 64.4 | 1.983 | 0 | True |
| [qwen_yellow_raw](qwen_yellow_raw/agent_trace.md) | 65.5 | 2.103 | 0 | True |
| [qwen_yellow_clahe](qwen_yellow_clahe/agent_trace.md) | 67.1 | 2.123 | 0 | True |
| [qwen_yellow_final](qwen_yellow_final/agent_trace.md) | 66.0 | 2.096 | 0 | True |

基线未启用任务记忆和区域候选加权；因此本批不是单独隔离记忆效果的消融实验。Qwen 调用延迟与仿真调度也会影响结果。没有证据支持 Agent 更快或更短，只验证集成闭环和真实反馈传递。

初版 raw/CLAHE 使用的转圈监测阈值为各自冻结配置，最终版放宽为 20 s / 240°，避免误判普通转向；本批运行未触发该保护，触发行为通过状态机测试验证。

相机为末次已保存快照，不保证最后曝光帧。目标真值仅用于离线审核；范围提示来自明确的宽区域配置。
