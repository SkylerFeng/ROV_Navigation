# 最终五场回归：已观测地图引导与执行进度修正（2026-10-15）

> 后续实际运行发现转向复发，本页结果属于历史版本。本轮进一步修复低速朝向、引导拐角与终端接近，并完成三种发目标时序及五场回归，见[最新修复记录](slalom_turn_fix_20261015.md)。

> 正式入口更新（2026-10-15）：修正后的门洞已替换 `gates`，不再提供 `gates_clearance` 场景入口；slalom 使用当前默认修正配置。本页历史命名、旧命令和对照数据仅供追溯，当前运行与汇报见[组会汇报](group_meeting_ROV_navigation.md)。

本批五场均重新运行并到达；不是把此前不同版本的成功数据拼在一起。原 gates 未运行，门洞采用 gates_clearance。

- 起点 `(-3.0,0,1)`，目标 `(3.5,0.4,1)`；0.3 m/s、固定参考高度 z=1 m、XY 膨胀 0.5 m。
- 前视相机 640×360、水平视场 90°、逐像素深度；理想深度、真值位姿。原池碰撞代理双面渲染，建图高度上限 1.28 m。
- 已观测地图 A* 全局引导 + EGO 局部 B 样条；转向等待期间共享并冻结执行相位。
- 已知水域边界约束全局引导，保留 0.4 m 池边余量；障碍输入来自深度地图。
- 无窗口运行；每场最多 180 s 仿真，650 s 墙钟保护；到达误差 <0.01 m 并保持 2 s。

| 场景 | 到达 | 最终误差(m) | 仿真时长(s) | 轨迹更新数 | 跟踪恢复数 | 最大接触冲量(N·s) |
|---|---|---:|---:|---:|---:|---:|
| baseline | 是 | 0.002648 | 84.63 | 49 | 0 | 0.000000 |
| slalom | 是 | 0.001718 | 87.23 | 50 | 1 | 0.000000 |
| gates_clearance | 是 | 0.003109 | 87.27 | 45 | 0 | 0.000000 |
| pillars | 是 | 0.007587 | 133.07 | 59 | 8 | 0.000000 |
| mixed | 是 | 0.002849 | 93.83 | 47 | 0 | 0.000000 |

已核对五场核心导航源码与配置快照一致、最后 2 秒保存采样误差均小于 0.01 m，且原五个测试 USD 文件与上一轮逐字节一致。初始化由运行时配置覆盖，未重写旧布局。核验结果见 [verification.json](../logs/suites/five_scenarios_20261015_guide_fix/verification.json)。

本批 5/5 是五次单次测试的完成数量，不是统计成功率。slalom 任务允许外围绕行，不要求强制按 S 形逐门通过。

- [五场路线汇总](figures/five_routes_20261015_guide_fix/five_routes_overview.png)
- [五张 4K 单图与 SVG/PDF](figures/five_routes_20261015_guide_fix/README.md)
- [图片压缩包](figures/five_routes_20261015_guide_fix_figures.zip)
- [slalom 规划更新动画](../logs/suites/five_scenarios_20261015_guide_fix/slalom/trajectory_updates.gif)
- [修复原因、分步失败对照与运行方式](slalom_execution_fix.md)
- [新旧 slalom 对照](figures/slalom_execution_fix/slalom_before_after.png)
- [完整数据汇总](../logs/suites/five_scenarios_20261015_guide_fix/summary.json)

重复运行命令（使用新目录）：

```bash
python3 scripts/run_suite.py --scenarios baseline slalom gates_clearance pillars mixed \
  --output-dir logs/suites/NEW_FRESH_DIRECTORY
```

本批 sources/ 与 manifest.json 保存核心代码、参数与场景快照。中间版本的失败与未完成批次均保留在诊断目录，不能算入最终版本的完成数量。


## 最终窗口模式复验

同一核心导航代码与配置下，slalom 带窗口运行 **95.20 s** 到达，最终误差 **0.002746 m**，最大接触冲量为零；末尾 2 秒保存采样均在 0.01 m 内。无窗口最终版本为 87.23 s、0.001718 m。两次完整实测均通过，但不代表统计成功率。

[窗口复验数据](../logs/diagnostics/slalom_phase_20261014/final_gui_validation/slalom/run.json) · [窗口运行规划更新动画](../logs/diagnostics/slalom_phase_20261014/final_gui_validation/slalom/trajectory_updates.gif)
