# 复杂场景真实导航结果

使用真实 Qwen API + Isaac Sim。表中时间为仿真秒，路径为实际测量；失败也保留。

| 场景 | 状态 | 时间s | 航程m | 接触对 | 离线审核 | 初始不可见且通过 |
|---|---|---:|---:|---:|---|---|
| wrong_hint_box | FAILED | 420.0 | 18.03 | 0 | False | False |

[布局与实测轨迹](complex_scenes.png)。每个场景子目录保留 `trajectory.png`、`last_camera_raw.png`、`latest_detection.jpg`、`agent_trace.md`、`audit.json` 和事件日志。

`summary.json` 另外记录首次目标检测时间、区域扩展、API 决策拒绝、原地转圈保护及局部位置更新次数。

每组仅一次，不能估算成功率或证明区域提示提高效率；三种布局不构成同场景有无先验的消融实验。相机定位依赖理想距离和真实位姿。

`layout_checks.json` 仅为离线平面连通性预检查，不替代物理碰撞审核。实跑为 headless 相机渲染，未做 GUI 录像验收。
