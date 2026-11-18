# 西侧挡板问题定位与导航优化（2026-11-18）

本轮针对 `west_baffles` 的探索失败和轨迹折返，联合检查 YOLO 原始输出、定位过滤、Agent 决策、逐时地图、规划参考与真实运动。保留原场景布局、部件水动力、0.4 m 硬膨胀半径、420 s 总任务预算和 75 s 单动作预算。用户已于 2026-11-18 确认将当前代码、配置及验证材料提交至 GitHub 留档。

## 原因不是单独一层

### 1. 识别到了黄管，但过滤层把它丢弃

v11 西侧运行在 92.3 / 94.3 s，YOLO 的黄管分数约 0.954 / 0.956；表面定位约 [-4.607, 0.557] / [-4.607, 0.571] m。深度支撑分别有 336 / 236 像素，深度 MAD 约 0.008 / 0.004 m，但框内有效前景比例仅 4.6% / 2.8%，低于原 8% 门槛，均以 `insufficient_depth_or_foreground_support` 被拒绝。没有进入物体记忆，因而 Qwen 没有收到可接近的黄管候选。

这类细管、管口和遮挡外观不能用整个矩形检测框的填充比例一刀切。此前 v4 的低支撑日志还同时包含真正黄管表面和黄箱附近的误分类碎片；不能把全部被拒样本都称为错误目标。v11 当时未保存对应历史 RGB，因此其具体外观判断有局限；v13 已保留带时间戳的传感器快照，并人工检查细管框与末帧画面。

修改：保留原正常门槛，增加 `semantic_support.py` 的稀疏支撑分支：至少 200 个深度像素、前景比例至少 2%、YOLO 分数至少 0.85、深度 MAD 不超过 0.025 m，而且需要至少八帧连续一致类别确认；类别冲突锁、定位稳定性和新鲜度检查仍生效。单帧稀疏检测不构成确认。普通检测帧不能立即绕过同一轨迹尚未满足的稀疏确认窗口。

参数入口：`config/semantic/runtime.json` 的 `perception.sparse_*`。这些阈值是针对当前渲染和相机分辨率的工程配置，不代表真实水下通用标定值。

### 2. 覆盖率达标就提前放弃正确区域

v11 在 100.1 s，Agent 仅根据西区覆盖率 0.691 和两个独立扫描位置就切到东区。回放该时刻保存地图，西区仍有 1,431 个未检查格，并存在经过可达性、失败点和新颖性过滤后仍有收益的观察点。因此，转向东侧是区域释放规则触发的，不是那个时段 Qwen 把黄管误认成了东侧目标。

修改：两阶段评估。先在当前区域生成并过滤真实可达视点，再检查是否仍有生产性视点；达到覆盖率和独立扫描条件还不够，只有剩余可用视点耗尽才换区。最低收益按面积定义为 `agent.region_min_gain_area_m2=0.05`，避免随着 5 cm / 15 cm 网格变化而改变含义。零收益的跨区转移不算新观察证据。

v12 作为区域规则诊断试验，换区延后到 219.9 s、覆盖率 74.8%、可用生产性视点为零；尚未包括新的稀疏感知修复。在确认感知根因后于约 276 s 主动中止，`reason=interrupted`，不计完整任务成绩。

### 3. 候选可达性与执行约束不完全一致

`observed_guide.h` 原来在已经完成机体膨胀的地图上，再对直线和简化线段检查四向 0.1 m 偏移点。语义层未施加这一额外硬边距，部分被认为可达的路线在执行层被拒绝或绕远。

修改：去掉这层重复硬偏移；0.4 m 机体膨胀、池边界约束、连续线段检查和样条碰撞检查仍保留，优化器额外软距离仍为 0.1 m。不是把安全半径改成 0.1 m。此差异确实存在，但不能据此断言旧日志中每一次绕行都由它单独导致。

### 4. 中间路点被当成需要完全停住的终点

原轨迹到中间引导点后速度接近零，真实水动力与推进器响应滞后会使 ROV 略越过参考位置。随后位置反馈要求向后追参考点，前视相机朝向约束又要求先转向，造成不必要的转向和停顿。

修改：在原连续碰撞检查的中间段将结束、参考速度已低且真实机体接近路点时，从实测状态交接下一段。交接条件只作用于中间引导点，最终目标的身份、距离、朝向、低速停稳验收不变。v11/v13 运行反馈均记录 `runtime_revision=measured_guide_handoff_v11`，确认使用了新构建的规划器。

v9 上方探索动作 50.3→125.3 s 超时；v11 对应上方视点 50.1→81.0 s 到达，v13 为 50.3→81.3 s。它支持执行改善，但多项改动同时存在，不是严格单因素消融。

## 已完成的验证

| 场景 | v9 | v13 | 实测航程 v9→v13 | 接触报告对 v9→v13 | v13 严格离线审核 |
|---|---|---|---|---|---|
| 西侧挡板黄管 | 390.6 s 失败 | 103.6 s 成功 | 12.68→4.05 m | 0→0 | 通过 |
| 错误东区提示找黄箱 | 374.6 s 成功 | 307.8 s 成功 | 14.25→12.97 m | 1→0 | 通过 |
| 东侧设备蓝管 | 200.6 s 成功 | 171.7 s 成功 | 7.42→7.21 m | 1→0 | 通过 |

三场景正式回归已完成，均零接触报告且通过严格离线审核。v13 西侧 7 次动作 API 调用、5 次轨迹更新，目标真实表面水平距离约 1.219 m；错误先验 12 次动作 API 调用、15 次轨迹更新，最终距离约 1.194 m；东侧蓝管 6 次动作 API 调用、7 次轨迹更新，最终距离约 1.104 m。任务都使用真实 Qwen API，未回退规则决策。

本轮三场均没有动作超时、无进展事件或 blocked_goal 工具失败。西侧最长跟踪 ALIGNING 采样段由约 18 s 降至约 1 s，东侧约 22→7 s。这只统计跟踪阶段；主动扫描和路径入口对准另计，不能解释为没有原地转向。

v11 是完整失败保留：420 s 超时，未确认目标。v10 源码与运行二进制诊断字段不一致，不作为干净的改动消融证据。v12 是主动中止诊断，不与正常完成试验混算。

130 项语义单元/集成测试通过；另 27 项跟踪、相位、配置、图像路由、区域搜索和点云膨胀检查通过；C++ 已膨胀窄通道回归通过，规划器构建通过。首次附加测试因未加载自定义 ROS 消息环境失败，加载 underlay/本地 install 后重新运行通过。

三场仿真完成后，另修复了可配置确认帧数大于八时的历史窗口长度，使该调参接口能够实际生效。正式 v13 使用的仍是普通三帧/稀疏八帧配置；修改前后在 100 条合成观测流、共 10,000 次更新中默认配置输出一致，见 [等价回归记录](validation/navigation_stability_20261118/default_window_equivalence.json)。这一接口边界修复已做单元和等价检查，未额外重跑 Isaac，不把它称为新的三场实跑版本。

## 证据与可复查入口

- [西侧轨迹](validation/navigation_stability_20261118/v13/west_baffles/trajectory.png)、[决策过程](validation/navigation_stability_20261118/v13/west_baffles/agent_trace.md)、[离线审核](validation/navigation_stability_20261118/v13/west_baffles/audit.json)。
- [错误先验轨迹](validation/navigation_stability_20261118/v13/wrong_hint_box/trajectory.png)、[决策过程](validation/navigation_stability_20261118/v13/wrong_hint_box/agent_trace.md)。
- [东侧蓝管轨迹](validation/navigation_stability_20261118/v13/east_equipment/trajectory.png)、[三场景汇总](validation/navigation_stability_20261118/v13/README.md)、[前后对照数据](validation/navigation_stability_20261118/comparison.json)。
- [三场景前后轨迹叠加](validation/navigation_stability_20261118/before_after_paths.png)、[稀疏黄管检测画面](validation/navigation_stability_20261118/v13/west_baffles/sparse_pipe_detection.png)。叠加图仅绘制测试物体/挡板和池边界，完整静态池体障碍请结合各场景观测地图图层查看；目标真值只用于离线解释。
- 原始运行：`logs/stability_20261118/v13/<case>/`；启动配置、选中模型与规划器二进制哈希都在运行 manifest 中。
- `semantic/events.jsonl` 记录全部周期采样 YOLO 框的接受/拒绝、支撑方式和原因；`sensor_snapshot` 对应 RGB/深度/内参与相机位姿。
- 决策及失败时的 `map_snapshot` 保存 free/occupied/inspected/safe 地图，同时附执行路径和跟踪状态；打包会保留 diagnostics。采样不是完整视频，不能据此计算全帧检测召回率。

## 结论边界

目前证据支持“感知过滤、区域释放、执行交接共同造成失败”，不能概括为 YOLO 不行或 LLM 自由发挥。西侧成功说明一米停车集合虽窄，并非因此证明任务不可能；运行与离线模型的保守几何集合也不完全相同。仍有扫描和合理路径对准，不能把所有原地转向都说成已消除。每场一次正式回归不构成统计成功率；相机定位仍依赖理想距离和真位姿，尚非真实水池验证。

## 自行运行西侧修复版

```bash
cd /home/ache/Coding/rov_navigation
python3 scripts/run_semantic_trial.py \
  --gui --policy qwen --env-file .env.semantic \
  --instruction '请找到黄色管子，不要黄色方块，停在管子表面一米处。' \
  --search-region '西侧设备区' \
  --scene-file scenes/pool_platform_semantic_complex_west_baffles.usda \
  --overrides config/experiments/hydro_components_fine_pool.json \
  --navigation-config config/navigation/profiles/stability_circular.json \
  --task-config config/semantic/stability_task.json \
  --model artifacts/detectors/hardening_20261116/best.onnx \
  --wall-limit 850 --output "logs/west_baffles_demo_$(date +%Y%m%d_%H%M%S)"
```

当前本地规划器已重新编译。GUI 运行使用相同控制接口，但本轮正式回归为 headless 相机渲染；GUI 录像效果仍由用户核验。
