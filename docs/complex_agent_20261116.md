# 较复杂场景下的区域搜索 Agent 测试

日期：2026-11-16。本轮新建独立场景，不覆盖之前的语义 demo，不提交 GitHub。

已完成三种场景的真实 Qwen/Isaac 测试，以及东侧场景的时序修复复测。西侧 100.1 s、东侧复测 192.7 s 均无接触并通过离线审核；错误提示黄箱场景在 420 s 超时，有池体碰撞和类别混淆，明确保留为失败压力测试。87 项语义测试通过。

建议录制西侧或东侧成功 demo。最新图：[三组轨迹](validation/complex_agent_20261116/latest/complex_scenes.png)。详细数据：[验证 README](validation/complex_agent_20261116/README.md)。

## 三种布局

| 场景 | 任务 | 难点 | 区域先验 |
|---|---|---|---|
| west_baffles | 找黄色管子、停在表面 1 m | 错位挡板遮挡目标；黄色方块和蓝管干扰 | 正确西侧提示 |
| east_equipment | 找蓝色管子、停在表面 1 m | 起点到目标约 5.8 m；设备挡板与立柱，需多次观察与探索 | 正确东侧提示 |
| wrong_hint_box | 找黄色方块、停在表面 1 m | 西侧挡板遮挡；黄管、红箱干扰 | 故意给错误东侧提示 |

每个场景使用四个已有目标资产和 2–3 个灰色静态碰撞体。沿用 Highbay 水面材质、真实渲染 RGB/距离相机、YOLO、Qwen、A*/EGO 和部件级水动力。灰色挡板只作为几何障碍，不把其语义标签提供给运行时模型。未引入移动障碍、流场随机化或真实测距误差。

场景定义：`config/semantic/complex_scenes.json`；生成器：`scripts/build_complex_semantic_scenes.py`。每个 USD 都叠加到 `pool_platform_semantic.usda`，因此旧场景的水体配置保留。独立 `.truth.json` 只供离线审核和绘图；决策只接收感知与可达候选及宽区域提示。

布局和结果图：[complex_scenes.png](validation/complex_agent_20261116/complex_scenes.png)。图中目标真值与障碍为离线展示，不代表导航预先知道目标位置。目标图标为示意，障碍矩形按实际尺寸绘制。

## 运行单个 GUI demo

```bash
cd /home/ache/Coding/rov_navigation
python3 scripts/run_semantic_trial.py \
  --gui --policy qwen --env-file .env.semantic \
  --instruction '请找到黄色管子，不要黄色方块，停在管子表面一米处。' \
  --search-region '西侧设备区' \
  --task-config config/semantic/complex_task.json \
  --scene-file scenes/pool_platform_semantic_complex_west_baffles.usda \
  --domain 178 --wall-limit 850 \
  --output "logs/complex_west_demo_$(date +%Y%m%d_%H%M%S)"
```

第二个终端：`ROS_DOMAIN_ID=178 bash scripts/start_semantic_debug.sh`。

另两组的场景、指令和提示见 `config/semantic/complex_suite.json`。测试超时预算为 420 仿真秒；增加预算用于更长的任务，不修改默认 task 配置、控制速度或障碍膨胀。

## 串行测试三组

```bash
python3 scripts/run_semantic_diversity.py \
  --cases config/semantic/complex_suite.json \
  --domain 178 \
  --output "logs/complex_suite_$(date +%Y%m%d_%H%M%S)"
```

`--gui` 可显示窗口；默认 headless 也渲染相机并运行真实视觉与物理。GPU 测试串行执行。输出目录保存 API 指令解析、决策、传感器快照、路径、地图、碰撞和水动力记录，以及冻结配置和代码哈希。失败也保留。

## 验证与限制

预检查 `scripts/check_complex_layouts.py` 用 5 cm 栅格与半径 0.4 m 圆盘近似检验起点安全和到目标邻域的连通性；三组均通过。这不是 USD 网格碰撞证明，不验证所有相机视线、所有通道或实际可控性。

真实测试结果与证据见 [验证说明](validation/complex_agent_20261116/README.md)。必须区分运行时成功、零接触审核及初始不可见条件。单次每场景测试不代表统计成功率，不与之前较简单场景的耗时直接比较算法性能。

## 场景重新生成与离线打包

```bash
python3 scripts/build_complex_semantic_scenes.py
python3 scripts/check_complex_layouts.py
python3 scripts/package_complex_semantic.py logs/complex_agent_20261116 \
  --output docs/validation/complex_agent_20261116
```

只在对应测试全部结束后做最终打包。生成器是显式离线步骤，导航启动不会读取场景定义中的目标位置。布局配置和真值只用于生成与评估。

## 东侧场景暴露的时序问题与修复

首轮东侧设备区测试中，目标检测确认状态在等待相机新帧和计算候选地图时发生变化：API 请求发送时没有接近候选，返回时却已有稳定目标和接近候选。执行端原先只验证旧探索点是否仍可达，因此执行旧探索动作，随后又因目标可见中断，反复切换。

新增 `decision_superseded_by_target` 检查：当旧请求没有接近候选，而返回时出现了接近候选，旧探索动作不执行；保持当前位置，用刚得到的观测重新调用 Qwen。没有直接替模型生成 approach JSON。新请求仍受 API 调用预算、目标新鲜度和执行前碰撞/可达性验证约束。

首轮所有日志保留。新复测的冻结 manifest 与首轮不同，结果应分别列出。此修复不声称解决所有掉帧、定位噪声或长距离探索效率问题。

调参建议：先保持默认导航膨胀与速度，单独改变 Agent 的 `region_search_budget_s`、`region_weight`，再比较同一个布局的有提示/无提示/错误提示；不要同时改变障碍尺寸和多个导航参数后，把结果差异归因于 Agent。当前区域扩展为软先验释放，不包含“原区域搜索完成”的覆盖率证明，也不会强制回到某个预设目标方向。


首轮西侧与东侧通过零接触离线审核；错误提示组在 420 s 超时，并在东侧与原始扫描池体碰撞网格发生实际接触、出现黄色管子被预测为黄色方块的类别混淆。该组是失败压力测试，不推荐作为成功 demo。详细证据见验证 README。


东侧同场景复测命令（仅修复决策时序，不改变布局）：

```bash
python3 scripts/run_semantic_diversity.py   --cases config/semantic/complex_east_retry.json   --domain 178 --output "logs/complex_east_retry_$(date +%Y%m%d_%H%M%S)"
```
