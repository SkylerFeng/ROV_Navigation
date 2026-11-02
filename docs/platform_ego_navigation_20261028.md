# Platform 水环境 A* + EGO 导航

这个入口复用了 `/home/ache/OceanSim-Highbay/data/Platform(new1)/Platform_black_water.usda` 的原始水体、扫描几何和碰撞层。Isaac Sim 发布 ROV 里程计与 OceanSim 水下相机点云；ROS2 中的观测栅格先用 A* 生成全局引导，再交给 EGO Planner 做 B 样条局部重规划，tracker 输出速度，`run_sim.py` 每个物理步施加浮力、相对水流阻力、恢复力矩和执行器响应滞后。

## 运行

先生成场景：

```bash
bash scripts/usd_python.sh scripts/build_scene.py --scenario platform_ego --no-select
```

分别启动三个终端（终端使用同一个 `ROS_DOMAIN_ID`）：

```bash
export ROV_SCENARIO=platform_ego ROS_DOMAIN_ID=107
bash scripts/start_navigation.sh
```

```bash
export ROV_SCENARIO=platform_ego ROS_DOMAIN_ID=107
bash scripts/start_sim.sh --scenario platform_ego --scene-file scenes/pool_platform_ego.usda
```

```bash
export ROV_SCENARIO=platform_ego ROS_DOMAIN_ID=107
bash scripts/send_goal.sh --goal 2.1 0.0
```

`--goal X Y` 可以在同一仿真中重复执行，目标点会重新进入 EGO 规划器；目标深度由现有 planner 固定为 1.0 m。手动运行时不要使用 `--stop-on-goal`，否则达到配置目标后 Isaac Sim 会退出。

障碍物由 `config/scenarios.json` 中的 `platform_ego.obstacles` 生成。复制该场景为自己的场景并修改位置、尺寸即可，每次重新 build USD 后，规划器仍只通过相机点云观察障碍，不读取障碍配置作为导航地图。

## 实测结果

无额外障碍的闭环试跑在 45.53 s 仿真时间到达目标，终点误差 0.0138 m，EGO 轨迹更新 12 次，无接触冲量。加入一个位于直线路径上的可编辑方块后，试跑在 44.70 s 到达目标，终点误差 0.0014 m，轨迹更新 18 次，路径长度 5.696 m，最小保守间距 0.456 m，无接触冲量。结果保存在 `logs/platform_ego_trial/` 和 `logs/platform_ego_obstacle_trial/`。

当前局部地图会保留已经观察到的占用单元，因此移动障碍离开后仍可能留下旧占用。对会持续移动的障碍应先刷新地图或增加时间衰减，再用于动态场景验证。
