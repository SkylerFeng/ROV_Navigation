# 2026-10-14：ROV 五场景重新实验与绘图

> 正式入口更新（2026-10-15）：修正后的门洞已替换 `gates`，不再提供 `gates_clearance` 场景入口；slalom 使用当前默认修正配置。本页历史命名、旧命令和对照数据仅供追溯，当前运行与汇报见[组会汇报](group_meeting_ROV_navigation.md)。

> 后续已完成进一步定位和修复对照，见[ROV卡住与异常运动报告](navigation_freeze_diagnosis.md)。本文件保留原五场景复测条件与结果；修正目标/净空后的结果单独报告。

本次重新运行了五个原场景。baseline 到达误差为 0.0036 m，与早期 executed_path.png 的约 0.004 m 接近；gates 本轮仍未复现历史成功，需要继续修复感知与规划/执行偏差，不能将本轮画成成功路线。

## 主测试条件

主数据目录为 `logs/scenario_tests/recheck_20261014_diagnostic`。baseline/gates 与其余三个场景分两段执行，每场单独启动仿真和导航，使用相同任务、运动及停止条件。

- 原始水池可见性、障碍位置、起终点和导航参数保持原样；五个默认场景文件已逐字节核对，与测试前副本一致，当前活动场景仍为 gates。
- Headless Isaac Sim + OceanSim，ROS_DOMAIN_ID=89，ROS 仿真时钟，理想深度和真值位姿。
- z=1.0 m，目标速度上限 0.3 m/s；相机 640×360，点云 stride=4。
- 每场最多 180 秒仿真；650 秒墙钟仅作为运行保护。计时从仿真主循环开始，目标在位姿/地图就绪后发送。
- 到达判据：距离目标小于 0.01 m，连续保持 2 秒；交互配置中的 0.3 m 提示阈值未修改。

## 五个原场景实测结果

| 场景 | 最终误差(m) | 仿真时长(s) | 规划更新数 | 完成到达判据 |
|---|---:|---:|---:|---|
| baseline | 0.003621 | 74.07 | 75 | 是 |
| slalom | 4.109586 | 180.00 | 42 | 否，180秒预算结束 |
| gates | 2.029122 | 180.00 | 66 | 否，180秒预算结束 |
| pillars | 0.003263 | 73.13 | 67 | 是 |
| mixed | 0.002486 | 74.40 | 65 | 是 |

这是一轮每场景单起终点的结果，不是统计成功率。到达也不自动等于全程无碰撞：slalom 接触报告中 EntryBlock 和 OuterA 均出现非零冲量；pillars/mixed 记录的最大接触冲量为零。最早 baseline/gates 的仪器版本仅保存接触事件，不能由事件数推断实际碰撞次数。

## 为什么与旧 baseline 不同

旧五场景图使用 150 秒墙钟预算，并在 0.3 m 阈值处结束；当时有其他仿真竞争资源，各场实际仿真时间不一致。旧轮 baseline 约运行 58.6 秒仿真，早期 executed_path.png 则来自约160秒仿真的不同运行。
此次 baseline 运行约74.07秒仿真并连续满足1厘米判据，最终误差0.0036205米。旧参考图的完整逐点 run.json 没有保留，且来自早期时钟适配版本，因此不能声称两次运行条件完全相同或轨迹逐点复现。局部规划还受点云到达与重规划时序影响；停止时间差不能单独解释整条曲线形状变化。

## gates：成功记录与本轮失败可以同时成立

历史成功运行保存在 `logs/scenario_tests/gates_suite/gates/run.json`，最终误差0.1454306米，轨迹在立杆附近从 y≈0.49米处通过。它采用较早的时钟实现及不同的0.3米阈值，不混入本轮五场景结果。
本轮 ROV 停在约(1.471, -0.020, 1.0)米；跑满180秒仿真后误差仍为2.0291米。`controls.json`/`progress.json` 表明受阻时仍有约0.3m/s向前指令和约9N的X向力，但实际位置不前进。原水池三角网格在 x≈1.6、y≈0.22/-0.37处包含细立杆；碰撞报告持续关联原水池网格与ROV船体。
该网格 `/World/Environment/Platform/Collision/Platform_collision_clean/mesh` 的 visibility=invisible，会参与物理碰撞，但不会出现在理想渲染深度中。已提供资源还存在若干缺失视觉瓦片。这解释了原图看似空旷却被阻挡的问题。
另一个可量化问题：最后一条规划轨迹起点约(3.291,0.019,1.0)，当时实际位置约(1.471,-0.020,1.0)，偏差约1.8204米。baseline对应偏差约0.00023米。上游 FSM 从当前名义轨迹状态开始重规划，并按名义轨迹时间判断完成；受阻后可能继续推进名义规划，不能据此判断ROV真的到达。此次没有改写规划器或控制律来制造成功。

[gates 历史成功与本轮失败对照图](figures/recheck_20261014/gates_success_vs_recheck.png) · [细立杆局部排查图](../logs/scenario_tests/recheck_20261014_diagnostic/gates_contact_diagnosis.png)

## 独立排查实验（不混入主图）

只显露原水池碰撞网格的对照保存在 `recheck_20261014_visible_pool`：baseline最终0.004324米，gates在180秒内仍未完成（4.190136米），说明可见性不是唯一问题。slalom对照在约100秒时主动结束，不计正式完整试验。原场景已恢复，默认构建不显露碰撞网格；`build_scene.py --show-pool-collision` 仅为诊断选项。

- 显露碰撞网格 + 密集点云 stride=1：90秒仿真预算，最终误差 3.546012 m，停止原因 `simulation_time_limit`。见 `logs/scenario_tests/recheck_20261014_dense_depth/gates`。
- 原场景 + 带窗口 GUI：90秒仿真预算，最终误差 2.023246 m，停止原因 `simulation_time_limit`。见 `logs/scenario_tests/recheck_20261014_gui/gates`。

GUI 对照同样在原水池细立杆处受阻，记录的接触点约为(1.6826, 0.2259, 0.9736)米，最大接触冲量范数约0.5624 N·s。这次带窗口与无窗口运行都未完成，尚未复现历史成功；增加采样密度及显露网格也未单独解决问题。

## 路线图与复现实验

[五场景汇总图](figures/recheck_20261014/five_routes_overview.png) · [五张4K单图及SVG/PDF目录](figures/recheck_20261014/README.md) · [图片压缩包](figures/recheck_20261014_figures.zip)

绿色为实际位置采样，红色为新增障碍，灰色为原水池网格在船体高度范围内的截面，橙色X为未完成案例真实结束位置。灰线仅用于解释图形，没有注入主实验导航地图。没有平滑、拼接不同轮次或把终点延伸到目标。

旧图与 executed_path.png 均保留。每场保存 run.json、plans.json、controls.json、日志和视图；后三个主场景及补充实验另存源码快照与SHA256清单。前两个主场景在开始增加清单功能前已运行，其原场景副本保存在主目录的 original_scenes 下。

```bash
cd /home/ache/Coding/rov_navigation
python3 scripts/run_suite.py --scenarios baseline slalom gates pillars mixed --sim-time-limit 180 --arrival-tolerance .01 --settle-time 2 --wall-time-limit 650
python3 scripts/plot_five_routes.py --suite logs/scenario_tests/recheck_20261014_diagnostic --output docs/figures/recheck_20261014
```

复测保留失败，不将修改感知条件的对照冒充原场景结果。当前仍需处理不可见碰撞结构、受阻后的实际状态重规划，以及跟踪偏差/碰撞恢复，才能获得稳定可重复的复杂场景导航。
