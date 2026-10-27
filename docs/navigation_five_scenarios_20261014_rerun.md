# 五场景重新实测与路线图（2026-10-14）

> 正式入口更新（2026-10-15）：修正后的门洞已替换 `gates`，不再提供 `gates_clearance` 场景入口；slalom 使用当前默认修正配置。本页历史命名、旧命令和对照数据仅供追溯，当前运行与汇报见[组会汇报](group_meeting_ROV_navigation.md)。

> 更新：本页为历史诊断/复测；进一步修正执行进度、感知、初始化并加入已观测地图全局引导后，最终五场均到达，见[最新回归报告](navigation_five_scenarios_20261015_guide_fix.md)与[slalom 修复说明](slalom_execution_fix.md)。

五场均重新启动 Isaac Sim / OceanSim、EGO 与跟踪器顺序运行，未复用旧轨迹。结果：4 场到达，slalom 未到达。

## 实验条件

- 起点 `(-2.7,0,1)`，统一目标 `(3.5,0.4,1)`；固定参考高度 z=1 m，速度上限 0.3 m/s，XY 障碍膨胀 0.5 m。
- 原水池碰撞网格参与深度观测并保留物理碰撞；理想深度、真值位姿；无窗口运行，点云采样步长 4。
- 到达判据：三维误差 <0.01 m 并连续保持 2 s；每场最多 180 s 仿真，墙钟保护 650 s。
- 门洞采用 `gates_clearance`：Gate2North 下端由 y=1.3 m 提高至 1.8 m，上端保持 2.9 m。原 `gates` 未在本轮运行，本结果不代表原布局通过。
- 测试期间未调整导航参数。每场 sources/ 与 manifest.json 保存代码、配置和场景快照。

## 结果

| 场景 | 到达 | 最终误差(m) | 仿真时长(s) | 轨迹更新数 | 最大接触冲量范数(N·s) |
|---|---|---:|---:|---:|---:|
| baseline | 是 | 0.006367 | 82.07 | 82 | 0.000000 |
| slalom | 否，超时 | 6.404519 | 180.00 | 105 | 0.000000 |
| gates_clearance | 是 | 0.002199 | 82.27 | 73 | 0.000000 |
| pillars | 是 | 0.005930 | 75.60 | 66 | 0.000000 |
| mixed | 是 | 0.003988 | 87.33 | 76 | 0.000000 |

已复核成功场景最后 2 秒内保存的采样点均在 0.01 m 内。所有场景最大接触冲量为零；存在零冲量接触报告，不能直接将报告次数解释为实际碰撞次数。

## slalom 本轮仍未通过

实测 XY 范围约 x∈[-2.911,-2.568] m、y∈[0,1.559] m，尚未穿过障碍区。结束时状态为 REPLAN_TRAJ / ALIGNING，tracking_recoveries=24，目标格为空闲。当前程序仍存在重复恢复、转向与重规划之间的推进问题，具体原因需要进一步时序定位。无碰撞不等于导航成功；本轮不能声称 slalom 已稳定修复。

失败图保留实测终止位置并用橙色 X 标注，未延伸至目标，也未换用以前的成功轨迹。

## 文件

- [五场景汇总图](figures/five_routes_20261014_rerun/five_routes_overview.png)
- [五张单图及 PNG/SVG/PDF](figures/five_routes_20261014_rerun/README.md)
- [图片压缩包](figures/five_routes_20261014_rerun_figures.zip)
- [实测数据汇总](../logs/suites/five_scenarios_20261014_rerun/summary.json)
- 各场目录保存 run.json、controls.json、plans.json、日志与 trajectory_updates.gif（实际运动与规划更新）。

## 复现

```bash
python3 scripts/run_suite.py --scenarios baseline slalom gates_clearance pillars mixed \
  --overrides config/experiments/gates_free_goal.json --domain 89 \
  --wall-time-limit 650 --sim-time-limit 180 --arrival-tolerance .01 --settle-time 2 \
  --output-dir logs/suites/NEW_FRESH_DIRECTORY
python3 scripts/plot_five_routes.py --suite logs/suites/NEW_FRESH_DIRECTORY \
  --scenarios baseline slalom gates_clearance pillars mixed \
  --output docs/figures/NEW_FRESH_DIRECTORY
```

每场一次运行，4/5 是本批完成数量，不代表统计成功率。旧数据和旧图保留。
