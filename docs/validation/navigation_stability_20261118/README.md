# 导航根因定位与修复验证（2026-11-18）

最新正式结果为 [v13 三场景](v13/README.md)，真实 Qwen + Isaac Sim + 部件水动力，保持原场景布局、420 s 总任务预算、75 s 单动作预算和 0.4 m 硬膨胀。三场本轮均成功、零接触报告、严格离线审核通过。每场一次，不代表统计成功率。

- [完整原因与改动](../../navigation_stability_20261118.md)。
- [前后轨迹叠加](before_after_paths.png)与 [前后指标](before_after_metrics.json)。
- [采样执行稳定性对照](comparison.json)：动作超时、无进展、阻塞、对准阶段分别统计。
- 各场保留轨迹、末帧原始相机、检测图、动作反馈、审核、配置、manifest 和事件时间戳对应的 diagnostics。
- v11 是完整失败诊断轮；v12 主动中止，原始日志在 `logs/stability_20261118/v12/west_baffles`，不得作为正常完成任务。`partial_comparison.json` 为中间诊断对照，最终三场对照使用 `comparison.json`。
- [默认确认窗口等价检查](default_window_equivalence.json)说明仿真后可配置帧数边界修复的验证范围。

三场轨迹图的目标/布局真值只用于离线审核和解释，运行 Agent 依赖相机、距离、位姿与地图观测。仿真中的理想距离和真位姿仍是现实部署限制。用户已于 2026-11-18 确认将当前代码、配置及验证材料提交至 GitHub 留档。
