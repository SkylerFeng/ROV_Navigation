# 导航调参入口

建议复制 `profiles/conservative.json` 为自己的配置，通过 `--navigation-config` 选择；只写想修改的参数，其余继承 `default.json`。修改配置后重新启动，不支持运行中热更新。`default.json` 的 planner/tracker 值保留原代码默认行为，limits 默认为空，沿用当前场景的速度等限制。

## 运行与核对

```bash
# 不启动仿真、不请求 API；检查 experiment.navigation 和 experiment.max_velocity 等最终值
python3 scripts/run_semantic_trial.py --policy qwen --env-file .env.semantic \
  --navigation-config config/navigation/profiles/conservative.json --check-config

# 带窗口，真实 Qwen 决策
python3 scripts/run_semantic_trial.py --gui --policy qwen --env-file .env.semantic \
  --navigation-config config/navigation/profiles/conservative.json \
  --scene-file scenes/pool_platform_semantic_screened.usda \
  --output "logs/qwen_tuned_$(date +%Y%m%d_%H%M%S)"
```

普通导航或 run_suite 可以用同一入口：在原命令前加 `ROV_NAVIGATION_CONFIG="$PWD/config/navigation/profiles/conservative.json"`。手动分别启动仿真、导航时，两个终端必须使用相同配置。

语义启动器把最终参数冻结到本次输出的 `config/experiment.json`，导航与仿真共同读取该快照。`effective_config.json` 可用于比较两轮实验。CLI 文件优先于 ROV_NAVIGATION_CONFIG；文件是对 default.json 的局部覆盖。limits 中显式给出的项覆盖场景和实验覆盖文件的同名顶层参数；未给出的项继续使用原场景/实验值。规划/跟踪的最终值位于 experiment.navigation。

## limits：规划与导航的公共约束

| 参数 | 单位 / 类型 | 作用 |
|---|---|---|
| max_velocity | m/s | 同时传给 EGO 速度限制与跟踪速度限幅 |
| max_acceleration | m/s² | EGO 轨迹加速度限制；不是物理推进器加速度的保证 |
| max_heading_error_deg | °，0–90（不含0） | 朝向误差超过阈值先转向再平移；规划执行与跟踪共用 |
| align_before_translation | bool | 是否按前视相机方向对齐后移动；默认建议保留 true |
| observed_global_guide | bool | 是否启用观测地图上的全局引导 |
| tracking_error_limit | m | EGO 执行时容许的跟踪偏差 |
| planner_goal_tolerance | m | EGO 的到达容差；不是语义任务的最终完成距离 |

保守示例：速度 0.2 m/s，加速度 0.2 m/s²，朝向门槛 15°。这只是调参示例，不代表已在所有场景验证。增大朝向门槛能减少等待，也可能让相机偏离运动方向；速度提高可能增加水动力下的跟踪误差。

## planner：EGO 规划

| 参数 | 默认 | 作用 |
|---|---:|---|
| replan_time_s | 0.5 s | EGO 重规划时间阈值，不是传感器刷新率 |
| no_replan_distance_m | 0.2 m | 接近目标时的“不再重规划”距离阈值 |
| planning_horizon_m | 3 m | 规划视距，同时设置 FSM 和 manager |
| map_resolution_m | 0.05 m | EGO 栅格分辨率，越小内存与计算负担越大 |
| obstacle_inflation_m | 0.5 m | EGO 障碍膨胀距离，影响通道是否可通过 |
| collision_distance_m | 0.35 m | 优化器障碍距离代价参数，不等于严格安全保证 |
| collision_weight | 3 | 碰撞代价权重 |
| trajectory_lookahead_s | 0.5 s | 轨迹服务前瞻时间 |

## tracker：沿轨迹运动

| 参数 | 默认 | 作用 |
|---|---:|---|
| position_kp | 2 s⁻¹ | 位置误差到速度修正的增益 |
| depth_kp | 0.8 s⁻¹ | 固定世界 Z=1 m 的高度保持增益 |
| yaw_kp | 1 s⁻¹ | 朝向误差到角速度的增益 |
| max_yaw_rate_rad_s | 0.5 rad/s | 导航跟踪的偏航指令上限 |
| update_hz | 30 Hz | 跟踪循环频率 |
| input_timeout_s | 0.5 s | ROS 输入接收时间的超时门槛；必须大于控制周期 |

## 与其他调参层的关系

- 语义扫描、悬停、最终朝向保持：`config/semantic/runtime.json` 的 motion、scan、verification。语义控制接管期间使用这些参数，而不是 tracker 的位置/偏航增益。
- 目标停靠距离与任务限时：`config/semantic/task.json`。arrival_tolerance_m 是进入停靠验证的位置容差；surface_standoff_m 是目标表面距离要求。
- 语义候选地图：runtime.exploration 和 task.grid_resolution_m / clearance_m，与 EGO 地图是不同层。改变 EGO 膨胀参数不会自动改变语义候选的 clearance_m。
- 真实施力、推力响应和水流：`config/experiment.json` / `config/experiments/hydro_components.json` 的 hydrodynamics。物理层 max_yaw_rate_rad_s 仍可把跟踪角速度指令限得更低；仅提高 tracker 上限并不保证转得更快。
- A* 引导、EGO、传感器地图仍有固定几何和内部参数；本接口覆盖常用项，不宣称所有底层参数均可调。固定世界 Z=1 m 未改成可任意修改的航深。

建议每次只改一组，保留运行目录，比较成功状态、接触、轨迹长度、耗时和验证指标，不只看画面中的移动速度。

### 偏航平滑

`tracker.yaw_acceleration_rad_s2` 默认 0.4 rad/s²，限制连续偏航指令的变化率，同时作用于导航与语义接管后的最终角速度指令。失效输入直接走原安全停机逻辑；不缓慢释放停机指令。不对平移停止添加拖尾，以免妨碍避障制动。实际角加速度仍取决于水动力与执行器。
