# 导航参数接口（2026-11-10）

用户需求：将导航参数整理为清晰可调接口，避免修改 ROS 启动代码或跟踪器。

## 实现

- `config/navigation/default.json`：planner / tracker 保留原默认值，limits 默认继承场景。
- `config/navigation/profiles/conservative.json`：局部覆盖示例。
- `scripts/navigation_config.py`：校验参数名、数值、布尔类型及控制周期约束，统一生成 ROS 规划参数。
- `scripts/experiment.py`：所有导航/仿真入口读取同一导航配置。
- `scripts/navigation.launch.py`：EGO 规划视距、重规划、地图和优化参数、轨迹前瞻从配置读取。
- `scripts/tracker.py` / `tracking_control.py`：增益、偏航限幅、刷新率和输入超时从配置读取。
- `scripts/run_semantic_trial.py`：新增 --navigation-config，支持 --check-config，最终配置随实验冻结，子进程不再重新应用外部导航 profile。

完整使用说明、单位、相互作用与优先级见 `config/navigation/README.md`。未更改场景、水动力、语义验证阈值和默认规划/控制行为。limits 显式设置会覆盖场景/实验同名顶层值；这是刻意设计的调参优先级。

## 验证

单元测试检查默认控制行为等价、局部覆盖、规划器两处视距同步、冻结快照复载、错误参数拒绝、控制输出随参数变化。ROS 启动文件编译检查；真实 Isaac 基础语义场景使用保守 profile 的结果见后续记录。并非所有参数组合或复杂场景均已验证，不代表导航性能提升。

全部保留本地，未提交 GitHub。

### 实测结果

71 项回归测试通过，记录于 `docs/validation/navigation_config_20261110/tests.txt`。

`logs/navigation_config_20261110_basic`：headless Isaac、rule 策略（0 次 API 调用）、部件水动力、保守 profile，SUCCEEDED；16.5 s 仿真时间，0.338 m 实测路径，1 次 EGO 更新，0 接触记录，离线审核通过。冻结配置确认 max_velocity=0.2、max_acceleration=0.2、max_heading_error_deg=15。基础短程测试验证接口接通，不代表复杂障碍场景已验证或参数更优。审计及轨迹位于 `docs/validation/navigation_config_20261110/basic/`。
