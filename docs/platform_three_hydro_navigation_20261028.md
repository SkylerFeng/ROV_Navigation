# Platform 水动力导航三场景测试

本轮在 OceanSim-Highbay 的 `Platform_black_water.usda` 水体场景中，沿用传感器点云、A* 全局引导、EGO Planner 局部 B 样条重规划和 ROS2 tracker，加入 0.08 m/s 横向水流、浮力、阻力与推进器响应滞后，测试了三种障碍布局。障碍位置只用于生成 USD 场景；导航栅格仍来自运行时相机点云。

## 场景

- `platform_ego_slalom`：三个交错箱体，要求连续左右绕行。
- `platform_ego_gates`：两组上下箱体形成错位门洞，用于测试狭窄通道。
- `platform_ego_mixed`：箱体与圆柱混合，测试不同障碍外形。

## 实验命令

```bash
for s in platform_ego_slalom platform_ego_gates platform_ego_mixed; do
  bash scripts/usd_python.sh scripts/build_scene.py --scenario "$s" --no-select
done
python3 scripts/run_suite.py --scenarios platform_ego_slalom platform_ego_gates platform_ego_mixed \
  --output-dir logs/suites/platform_three_hydro_20261028_final --domain 111 \
  --sim-time-limit 120 --wall-time-limit 420 --arrival-tolerance .05 --settle-time 2
```

## 实测结果

| 场景 | 结果 | 终点误差 | 仿真时间 | EGO 更新 | 路径长度 | 最小保守间距 | 最大速度 | 接触冲量 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Slalom | 到达 | 0.0345 m | 47.93 s | 30 | 6.538 m | 0.433 m | 0.287 m/s | 0 |
| Gates | 到达 | 0.0140 m | 48.07 s | 11 | 4.196 m | 0.821 m | 0.185 m/s | 0 |
| Mixed | 未到达，时间上限 | 2.2188 m | 120.00 s | 13 | 2.910 m | 0.188 m | 0.268 m/s | 0 |

混合场景没有发生接触冲量，但局部规划在障碍附近停滞，说明该布局对当前 0.5 m 障碍膨胀和局部地图保留策略仍然过于苛刻。它应作为待改进案例，不应表述为成功率结果。三组均为单次试验，不能替代统计意义上的成功率。

## 轨迹证据

- [三场景汇总图](figures/platform_three_hydro_20261028/three_routes.png)
- [三场景汇总矢量图](figures/platform_three_hydro_20261028/three_routes.pdf)
- [Slalom 轨迹动画](figures/platform_three_hydro_20261028/platform_ego_slalom/trajectory_updates.gif)
- [Gates 轨迹动画](figures/platform_three_hydro_20261028/platform_ego_gates/trajectory_updates.gif)
- [Mixed 轨迹动画](figures/platform_three_hydro_20261028/platform_ego_mixed/trajectory_updates.gif)

各场景目录还保留 `run.json`、`plans.json`、`metrics.json`、`scene_evidence.json` 和输入源哈希，可追溯实际运行内容。运行日志位于 `logs/suites/platform_three_hydro_20261028_final/`，未纳入 Git 提交。

