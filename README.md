# ROV 水池避障导航实验

基于 Isaac Sim 5.1、OceanSim 和本机 ROS2 EGO-Planner-Swarm。
原始 Platform / OceanSim / EGO 文件均保持不变；此目录保存独立实验代码。

## 2026-10-15 slalom 修复与最终回归

本轮针对实际运行中复发的转向问题，统一低速朝向判定、沿可通行引导前缀选局部目标，并加入精确终端接近轨迹。五场统一回归均到达；正常启动slalom为67.07 s / 误差0.34 mm，55秒延迟发目标的窗口复验在接到任务后约135.23 s到达。均满足0.01 m内保持2 s，最大接触冲量为零。
[本轮修复与实测报告](docs/slalom_turn_fix_20261015.md) · [最新路线图](docs/figures/five_routes_20261015_turn_fix/five_routes_overview.png)


## 当前正式场景（2026-10-15）

现在只保留 baseline、slalom、gates、pillars、mixed 五个正式入口。
slalom 使用最终验证的共享执行进度、已观测地图全局引导和感知配置；gates 已直接替换为净空校核后的布局，不再单列 gates_clearance。
公共起点 `(-3.0,0,1)`、目标 `(3.5,0.4,1)`、前视相机水平视场 90°、逐像素深度采样。
[本次组会汇报](docs/group_meeting_ROV_navigation.md)包含当前架构、五场结果、路线图和 Demo 操作。
旧配置和场景归档在 `logs/archives/scenario_promotion_20261015/`，历史测试数据保持原样。

## 多场景与在线规划轨迹

当前默认场景为 **gates**。`scenes/pool_navigation.usda` 保持为当前场景入口，
其他场景文件可以分别在 Isaac Sim 中打开预览。

项目自带 `ros_ws` 规划器副本，以 `/clock` 为时间基准；转向等待时暂停轨迹执行进度，规划器与轨迹服务器共享这一进度，地图和物理仿真继续运行。
已在本机编译；迁移或修改 C++ 后运行 `bash scripts/build_planner.sh` 重建。
原 EGO 复现仓库保持不变。代码来源与改动见 `ros_ws/README.md`。

| 名称 | 场景文件 | 障碍数量 | 测试内容 |
|---|---|---|---|
| baseline | pool_baseline.usda | 3 | 原始基准对比 |
| slalom | pool_slalom.usda | 7 | 交错箱体与立柱、连续转向 |
| gates | pool_gates.usda | 6 | 校核净空后的双错位门洞 |
| pillars | pool_pillars.usda | 8 | 立柱阵列、多条绕行路径 |
| mixed | pool_mixed.usda | 8 | 箱体、墙段、立柱混合 |

停止旧的仿真和导航节点后，选择场景，再按本文后面的三个终端步骤启动：

```bash
cd /home/ache/Coding/rov_navigation
bash scripts/select_scenario.sh gates
```

名称可替换为表中的其他名称。选择记录在 `config/active_scenario.json`，三个终端会读取同一选择。
布局写在 `config/scenarios.json`，公共参数仍在 `config/experiment.json`。
切换场景需要重新启动仿真和导航，避免沿用上个场景的障碍缓存。

Isaac Sim 的 **ROV navigation** 面板提供图例、显示开关、俯视/透视切换和规划更新计数：
启动时默认使用俯视；可在面板切换透视，或通过 `start_sim.sh --view perspective` 启动透视视角。

- **青色**：最近收到的 EGO B 样条，按真实控制点和节点向量采样。
- **橙色**：最近三次旧规划，每收到新轨迹就替换，便于观察重规划。
- **绿色**：ROV 的实际行驶轨迹。
- **黄色**：可选的 B 样条控制多边形和控制点。

线条投影到水面上方显示，仅用于观察 XY 规划；不是机器人实际深度或三维可行性证明。
显示采用视口 debug overlay，不创建带碰撞/深度几何的 USD 轨迹，防止轨迹本身进入障碍地图。
单独打开 USD 不会显示在线规划，必须启动仿真和导航节点。

新增 ROS 话题为 `/rov/planned_path`、`/rov/control_polygon`（nav_msgs/Path）及
`/rov/plan_info`（轨迹编号、更新数、时长）。所有消息使用 world 坐标。
面板另显示 `/rov/planner_status` 与 `/rov/tracking_status`：`ALIGNING` 为先转向，`HOLDING` 为保持，`BLOCKED_GOAL` 表示目标在膨胀障碍内。

每次仿真保存到 `logs/runs/<场景_时间>/`，包括 `run.json` 实际轨迹、`plans.json` 规划修订。
可导出二维轨迹图和**真实规划更新动画**：

```bash
python3 scripts/export_run.py logs/runs/<场景_时间>
```

会生成 `trajectory_updates.png`、`trajectory_updates.gif` 和 `metrics.json`。
逐个自动测试全部场景（建议先关闭其他 Isaac Sim 实例）：

```bash
python3 scripts/run_suite.py --scenarios gates
python3 scripts/run_suite.py --scenarios baseline slalom gates pillars mixed
```

批量测试使用独立 ROS domain，逐场景启动、发送目标和清理节点；保存到达误差、规划更新数、
保守障碍间距、运行日志和汇总 CSV/JSON。未到达/超时会明确记录，不当作成功。
批量复测默认每场 180 秒仿真预算，650 秒墙钟保护；以距目标小于 0.01 米并连续保持 2 秒作为完成判据。
可用 `--sim-time-limit`、`--wall-time-limit`、`--arrival-tolerance`、`--settle-time` 调整。
交互运行未指定覆盖参数时仍使用配置中的 0.3 米提示阈值。
每次测试保存实际配置、控制指令、原水池接触报告；新运行另存源码快照和 SHA256 清单。
旧离线检查仅覆盖新增障碍，未包含原水池碰撞网格；不能据此认定真实通道或目标可行。请结合实际膨胀地图与实测记录。
复杂布局还可能暴露当前规划/跟踪参数的局限，应以每次实际运行的 metrics.json 为准。

重建所有场景与离线检查：

```bash
bash scripts/usd_python.sh scripts/build_scene.py --all
bash scripts/usd_python.sh scripts/validate_scenarios.py
python3 scripts/plot_scenarios.py
```

`logs/scenarios_overview.png` 是五套布局总览，`logs/scenario_validation.json` 保存离线检查结果。

本次多场景运行报告：`logs/scenario_tests/ros_clock_suite/report.md`。
该报告是旧轮次：baseline、pillars、mixed 达到 0.3 米阈值；slalom 与 gates 在 150 秒墙钟预算内未达到。
完整指标和规划更新动画分别保存在各场景目录，不将未到达的运行计为成功。
2026-10-14 重新测试的条件、碰撞排查及路线图见 [复测记录](docs/navigation_recheck_20261014.md)。

## 场景

各场景引用 `Platform.final.usd`，加入对应静态障碍、BlueROV、
显式机器人碰撞体、起终点标记及可视水面。可用 Isaac Sim 的 File → Open 预览。
单独打开 USD 只得到场景；相机、ROS2 与跟踪控制由下面的启动脚本创建。

第一版是固定深度（2.5D）避障，后续再扩展完整三维导航。
世界坐标为 Z 向上、米为单位。原平台几何坐标加 `(-7.500032, -4, 1.35)`
得到实验世界坐标（此变换已包含 Platform.final 自身平移）。
当前公共起点 `(-3.0, 0, 1)`，目标 `(3.5, 0.4, 1)`，水面 `z=1.55`，池底约 `z=0.60`。旧起点/目标只在历史记录与旧场景标记中保留；启动脚本按当前配置设置机器人与标记。
池底是对原碰撞网格采样的近似值；启动与终点附近仍需运行时检查。
蓝色/绿色标记位于水面上方，实际导航高度是 1 米。

## 启动

先关闭其他 Isaac Sim 实例，避免 16 GB RAM / 8 GB 显存资源竞争。

终端一：

```bash
bash /home/ache/Coding/rov_navigation/scripts/start_sim.sh
```

终端二，等待仿真输出 `ROV ready` 后：

```bash
bash /home/ache/Coding/rov_navigation/scripts/start_navigation.sh
```

终端三，位姿与点云均持续发布后发目标：

```bash
source /opt/ros/humble/setup.bash
ros2 topic hz /rov/odom
# Ctrl+C 后继续检查点云
ros2 topic hz /rov/cloud_world
# Ctrl+C 后发送目标
bash /home/ache/Coding/rov_navigation/scripts/send_goal.sh
```

仿真用绿色曲线显示已执行轨迹。Isaac Sim 中的水面只是视觉效果，
第一版采用禁用重力、中性浮力近似、阻尼、姿态恢复和闭环力控制。
不是完整水动力、推进器或 ArduSub 模型。

## 数据链路

OceanSim 相机 → 深度 → 相机内参反投影 → 世界坐标点云
→ 观测障碍 XY 累积与竖直扩展 → EGO 占据地图和 B 样条 → PositionCommand → 世界坐标目标速度
→ 仿真速度闭环力/力矩 → PhysX 碰撞。

| Topic | 数据与约定 |
|---|---|
| `/clock` | 仿真时间，ROS 节点启用 use_sim_time |
| `/rov/odom` | 仿真真值；位置和线速度均为 world 坐标，供 EGO 使用 |
| `/rov/cloud_world` | 世界坐标 PointCloud2；约 5 Hz 仿真频率，无全局地图真值输入 |
| `/rov/cloud_navigation` | 已观测障碍的柱状近似，加配置的深度边界平面 |
| `/rov/rgb` | OceanSim 退化后的 RGB 图像 |
| `/rov/bspline` | EGO 轨迹 |
| `/rov/position_cmd` | EGO 轨迹采样后的目标位置与速度 |
| `/rov/cmd_vel_world` | 明确为 world 坐标的 Twist，非标准机体系 cmd_vel |
| `/move_base_simple/goal` | 手动目标；现有 EGO 回调会固定目标 z=1 |

最大速度 0.3 m/s、最大规划加速度 0.3 m/s²。
无指令或指令超过 0.5 秒未更新时，控制器减速至零。
第一版保持 z=1.0，完整三维目标需要后续适配 EGO 的目标回调和地图膨胀。
local_map.py 保留已观测的 XY 障碍格，排除池底，将导航高度带的障碍沿 z 扩展，
并加入 z=0.80 / 1.25 的约束平面，避免浅水池内的上下绕行。
障碍来自相机；高度平面来自预先配置的实验边界，不是传感器测得的障碍。
此方法针对静态场景，尚不具备动态障碍清除能力。
默认 `depth_mode: ideal` 使用仿真理想深度建立规划/控制基准，RGB 仍经过 OceanSim
水下渲染。设置 `depth_mode: degraded` 可切换到 OceanSim 退化深度做对比。
退化模型会丢弃暗物体深度；当前障碍在阴影中，不能假设退化深度足以安全导航。
理想深度绕障结果只能说明仿真导航基准成立，不能说明真实水下感知已解决。
由于 EGO 点云路径对 z 的膨胀只有一格，第一版不宣称具备三维机器人形状安全保证。

## 修改与检查

编辑 `config/experiment.json` 的障碍物、起点等参数后重建：

```bash
bash scripts/usd_python.sh scripts/build_scene.py
bash scripts/usd_python.sh scripts/validate_scene.py
```

`logs/scene_validation_<场景>.json` 保存组合层级、静态障碍碰撞、坐标变换和
起终点基本间距检查。`logs/build_scene.log` 中保留源资产加载警告。

目前原始视觉 Tile 4、6～14 为空文件，环境不能完整显示；碰撞网格仍独立存在。
未自动补造师兄的缺失模型。源码对水池范围的属性不是水动力或规划边界。
相机只观测当前视野，EGO 点云建图路径不提供完整历史融合；后续应评估盲区。
实际绕障到达、跟踪误差及碰撞次数需要运行闭环实验确认。

## 已完成的验证

此前 baseline 场景的一次无界面闭环基准实验已完成：4800 次渲染/控制循环（约 160 秒仿真时间），
理想深度模式、仿真真值位姿、固定深度 1.0 米。
最终距目标 0.0043 米；采样轨迹相对三块新增障碍的最小保守 XY 间距为 0.367 米。
间距计算使用机器人碰撞体的外接圆，不是 PhysX 接触事件统计，也不代表所有环境碰撞均已排除。

- `logs/executed_path.png`：实际执行轨迹。
- `logs/navigation_validation.json`：到达和保守间距结果。
- `logs/last_run.json`：采样位姿与最终位置。
- `logs/last_camera.png`：末帧水下相机图像。
- `logs/sim_ideal.log` / `logs/navigation_ideal.log`：本次基准运行日志。

场景离线检查、ROS 节点启动、控制限速/超时停止，以及障碍柱状地图过滤检查已通过。
这是一种场景、一组起终点下的基准结果；退化感知、更多任务与实机接口仍待验证。
