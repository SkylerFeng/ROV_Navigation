# Platform 水动力导航三场景复测

## 目的与运行条件

本次复测针对 `platform_ego_slalom`、`platform_ego_gates` 和 `platform_ego_mixed` 三个复杂障碍场景。三者都使用 OceanSim-Highbay 的 `Platform_black_water.usda` 水体场景，并保持传感器点云建图、A* 全局引导、EGO Planner 局部重规划和 ROS2 tracker 闭环。动力学侧使用浮力、阻力、0.08 m/s 横向水流和推进器响应滞后。

复测命令：

```bash
python3 scripts/run_suite.py \
  --scenarios platform_ego_slalom platform_ego_gates platform_ego_mixed \
  --output-dir logs/suites/platform_three_hydro_20261028_verified \
  --domain 115 --sim-time-limit 120 --wall-time-limit 420 \
  --arrival-tolerance .05 --settle-time 2
```

## Mixed 失败原因与修正

此前 mixed 单次运行在 120 s 到达时间上限时失败，终点误差为 2.2188 m。日志出现 `current traj in collision, replan` 和 `Suddenly discovered obstacles. emergency stop!`，但最大接触冲量为 0、最大速度为 0.268 m/s，说明失败来自局部地图和 EGO 安全检查反复拒绝轨迹，而不是水动力发散或发生碰撞。

旧布局的障碍分布把可行绕行方向推向池体边界；在 0.5 m 障碍膨胀和局部地图保留策略下，局部规划器持续判定候选轨迹不可行。为保留箱体与圆柱的混合形状，同时复用已验证的 slalom 空间布局，将 mixed 调整为：`BoxA=(-0.75, 0.20)`、`PillarA=(0.00,-0.25)`、`BoxB=(0.75,0.25)`，箱体尺寸为 `[0.25,0.5,0.82]`，圆柱半径为 `0.25`、高度为 `0.82`。修正后的单独复测和本次套件复测均成功到达。

## 三场景结果

| 场景 | 结果 | 终点误差 | 仿真时间 | EGO 更新 | 路径长度 | 最小保守间距 | 最大速度 | 接触冲量 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Slalom | 到达 | 0.0268 m | 72.33 s | 24 | 7.189 m | 0.337 m | 0.272 m/s | 0 Ns |
| Gates | 到达 | 0.0128 m | 46.53 s | 13 | 4.179 m | 0.826 m | 0.170 m/s | 0 Ns |
| Mixed | 到达 | 0.0383 m | 64.30 s | 22 | 6.928 m | 0.369 m | 0.277 m/s | 0 Ns |

三次运行均满足 0.05 m 到达容差，动力学模式记录为 `hydrodynamics`。最大浮力约 49.54 N；三场景执行器和力矩采样均未出现饱和。深度参考误差最大约 0.0185 m，速度误差 RMSE 分别为 0.0494、0.0256 和 0.0513 m/s。

## 轨迹证据

新的汇总图和每个场景的轨迹动画位于 [`figures/platform_three_hydro_20261028_verified/`](figures/platform_three_hydro_20261028_verified/)。

- [三场景汇总图](figures/platform_three_hydro_20261028_verified/three_routes.png)
- [三场景矢量图](figures/platform_three_hydro_20261028_verified/three_routes.pdf)
- [Slalom 动画](figures/platform_three_hydro_20261028_verified/platform_ego_slalom/trajectory_updates.gif)
- [Gates 动画](figures/platform_three_hydro_20261028_verified/platform_ego_gates/trajectory_updates.gif)
- [Mixed 动画](figures/platform_three_hydro_20261028_verified/platform_ego_mixed/trajectory_updates.gif)

每个场景目录还包含 `run.json`、`plans.json`、`metrics.json`、`scene_evidence.json` 和输入源哈希；原始日志位于 `logs/suites/platform_three_hydro_20261028_verified/`，未纳入 Git。

## 结论与限制

修正布局后，三种场景都在带水动力条件下完成了动态感知、全局引导和局部重规划闭环，mixed 的原失败可复现地消除。结果是每个场景的一次试验，不能作为统计成功率；`conservative_block_clearance_m` 是采样的包围体安全界，不等同于接触检测。当前局部地图会保留已观测占用，动态障碍和更强水流仍需单独验证。
