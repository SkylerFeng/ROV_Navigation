# 障碍膨胀距离减半（2026-11-11）

按用户要求，将两层默认障碍外扩距离从0.50 m缩至0.25 m：

- config/navigation/default.json: planner.obstacle_inflation_m，传入EGO grid_map/obstacles_inflation。此默认值也影响其他使用默认导航配置的场景。
- config/semantic/task.json: clearance_m，语义探索/停靠候选使用的安全余量。

减半的是外扩距离，不是障碍自身面积或膨胀后总面积。语义安全判定仍保留0.71×网格分辨率的离散补偿：默认0.15m网格下，距离阈值从0.6065m降为0.3565m，并不严格减半。EGO也有栅格离散效应。

优化器 collision_distance_m=0.35保持不变，它是另一个轨迹避障代价参数，不能与地图膨胀距离混为一谈，也不保证轨迹贴着0.25m边缘行驶。ROV碰撞几何、水动力、速度及成功判定未改。较小安全余量尚未进行物理碰撞回归，不能保证更窄通道一定适合实体ROV。

blue/yellow/red三套meeting配置通过--check-config验证均继承0.25/0.25；38项配置和语义回归测试通过。结果见validation/inflation_half_20261111。未调用API，未重新启动Isaac，未提交GitHub。

需退出旧仿真后重新运行，运行中的冻结配置不会自动更新。旧docs/validation或logs中的完整task/experiment快照可能仍显式指定0.5，刻意保留用于复现；若继续用旧快照的--task-config，则会覆盖新默认值。推荐使用scripts/run_meeting_demo.py的blue/yellow/red入口。自定义navigation配置也可能覆盖默认值，以新运行effective_config.json为准。
