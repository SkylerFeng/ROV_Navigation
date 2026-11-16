# 复杂场景感知与导航修正（2026-11-16）

## 最终回归结论（候选版，未验收）

保持原布局，真实 Qwen，任务上限420s；未提交 GitHub。新增432张图，留出场景mAP50 0.9355→0.9660，97项测试通过。但最终三场景均超时，不能宣称端到端改善或稳定可用。

| 场景 | 仿真秒 | 航程m | 接触证据 | 结果 |
|---|---:|---:|---|---|
| west_baffles | 420.0 | 15.67 | positive_separation_zero_impulse_only | 超时 |
| east_equipment | 420.0 | 17.41 | penetration_or_impulse_recorded | 超时 |
| wrong_hint_box | 421.1 | 15.66 | no_reports | 超时 |

西侧仅接近报告：separation正值0.227m、冲量0；东侧挡板有一次约0.0150冲量。错误先验场景无接触，但未完成目标靠近。

成果：难例数据与检测对照、跨帧／同帧冲突保护、共享池体占用地图、膨胀形状核对、显式跨区转移已实现。限制：正确先验尚未充分观测就被预算策略放弃；遮挡视角选择与局部执行仍不稳。单次试验不支持成功率结论。

建议下一步优先：区域覆盖证据驱动的退出条件；基于遮挡和可见性的候选视角；在线规划占用反馈与跟踪偏差联合安全检查。不要增加超时，也不要把本套配置替换为稳定默认。

[最终三场景轨迹与材料](validation/complex_hardening_20261116/latest/README.md)。

## 约束与问题

保持三份 complex USD 的布局、目标和障碍不变，任务时间仍为 420 仿真秒。本次不修改全局默认检测器，不提交 GitHub。此前 wrong_hint_box 出现黄色管子被识别为黄色方块、东侧扫描碰撞体接触和错误先验取消后仍在东侧搜索三类问题。

## 难例数据

`generate_semantic_hardcases.py` 在原场景中移动离线相机，采集每个目标周围 12 个角度、3 个距离（0.9/1.5/2.3m）。包含管子端面、侧面、自然遮挡和低照度视角；不移动或重存场景。不保证全部相机点都能由 ROV 实际到达。

共 432 张。西侧／东侧场景用于补充训练和验证；错误先验场景 144 张仅用于测试，不参与训练和选权重。合并原数据后 train/val/original-test 为 540/108/72 张。训练验证视角共享场景，有相关性，不能宣称是真实水下泛化测试。标签来自离线实例掩码，运行时无真值访问。`box_partial_views.png` 展示被管子／设备部分遮挡的方块。附带 mask/bbox 比例仅描述可见掩码在框中的占比，不等于遮挡率（未渲染无遮挡参照）。采集 manifest 保留场景 SHA 和每帧视点、可见目标框。

`train_semantic_detector.py --weights` 可从旧模型微调，候选训练 25 epochs，由验证集选最佳权重。原测试集与独立难例集均比较旧／新模型。

## 跨帧类别冲突

ObjectMemory 对同颜色、表面定位距离小于配置的 0.65m 的异类别检测尝试关联到同一轨迹。最近至少 8 次检测存在类别冲突时禁止 confirmed；需恢复连续稳定证据。间隔超过 1.5s 则重新累计。单帧同色、0.65m 内出现矛盾类别时也阻止确认；几乎重合（0.15m 内）的框避免重复建轨迹。已开始靠近的目标出现类别冲突会停车重新观察。阈值在 `agent.json/category_conflict_radius_m`。

限制：这不是识别真值。如果模型连续稳定地认错，时序投票仍不能纠正；距离很近的同色异类目标也可能被保守地延后确认。因此须同时补充数据，不能只靠投票。

## 池体碰撞地图

`export_pool_collision_prior.py` 只读取原池体 `/World/Environment/Platform/Collision/Platform_collision_clean/mesh`，转换到世界坐标，裁剪 z=0.84..1.28m 高度范围，保守投影到 0.1m XY 网格。不读取语义目标坐标。地图与几何来源记录在 `config/maps/platform_static_collision.{npz,json}`。

`static_collision_prior.py` 统一加载；语义探索网格及 EGO 点云地图均注入相同占用位置。未知区不会被标为空闲，仍需相机观测。地图是**已知静态池体先验**，不是相机建图成果，不适用于换场景后未经核验的网格。

全局默认 `static_collision_prior=null`。本次显式使用 `config/experiments/hydro_components_known_pool.json`。地图文件哈希进入运行 manifest。该固定深度投影不替代完整三维碰撞安全验证。

## 错误先验搜索

任务指定区域后，从 `search_regions.json` 获取其他区域，作为有序备选，不读取目标真值。原区域预算耗尽、扩展次数耗尽后，先对备选区域施加强优先权，再恢复全局搜索。每个备选区域的局部搜索仍受原预算约束，前往该区域的途中不计入局部搜索时间；总任务 420s 上限仍生效。已尝试视点和失败冷却仍有效。

调参入口：`config/semantic/agent.json` 的 `alternative_regions`、`alternative_region_weight`、`region_search_budget_s`、`region_max_expansions`。搜索事件记录换区原因。当前策略基于预算与已有任务执行反馈，不是概率语义地图，也未实现全区域覆盖证明。

## 运行与结果

本次专用套件：`config/semantic/complex_hardening_suite.json`；原失败场景先跑，其后做西侧／东侧回归。真实 Qwen + Isaac + 原水动力，结果与离线审核另存，不覆盖此前失败证据。

### 检测离线对照

| 测试集 | 旧 mAP50 | 新 mAP50 | 旧 mAP50–95 | 新 mAP50–95 |
|---|---:|---:|---:|---:|
| 原测试 72 张 | 0.9570 | 0.9591 | 0.8826 | 0.8882 |
| 留出场景 144 张 | 0.9355 | 0.9660 | 0.8869 | 0.9299 |

留出场景召回率 0.8757 → 0.9440。这里 precision/recall 为 Ultralytics 验证工作点，不是在线固定阈值统计。

另外用实际 ONNX、阈值 0.45、IoU≥0.5 检查“每张图的聚焦物体”：两模型的端面 11/11、侧面 12/12、斜面 47/48、方块 70/70 均相同。这说明中心视角子集仍偏容易，不能声称已复现并解决原运行中所有类别错误；mAP 改善来自全图目标统计。原失败运行仅保留最后帧，未保存 361s 瞬时误识别帧；最后帧上两个模型都识别为 pipe。

完整指标和逐帧结果位于 `logs/hardening_20261116/{evaluation.json,runtime_detection_eval.json}`。第一轮主动中止以修正 0.25m 关联距离过小的问题；诊断记录见 `docs/validation/complex_hardening_20261116/diagnostic_v1/README.md`。第二轮实跑结果待补充。

## 手动查看候选版

在项目根目录执行（模型文件需要保留本次训练产物）：

```bash
python3 scripts/run_semantic_trial.py \
  --gui --policy qwen --env-file .env.semantic \
  --instruction '请找到黄色方块，不要管子，距方块表面保持一米。' \
  --search-region 东侧设备区 \
  --scene-file scenes/pool_platform_semantic_complex_wrong_hint_box.usda \
  --overrides config/experiments/hydro_components_known_pool.json \
  --model logs/hardening_20261116/detector/train/weights/best.onnx \
  --task-config config/semantic/complex_hull_task.json \
  --navigation-config config/navigation/profiles/complex_hull_clearance.json \
  --wall-limit 850 \
  --output "logs/hardening_demo_$(date +%Y%m%d_%H%M%S)"
```

`wall-limit` 是进程看护的墙钟时限，沿用旧复杂场景设置；任务的仿真超时仍为 420s。此命令显式给出错误的东侧先验，目标实际位置只供离线审核，运行决策不可见。


### 第二轮与外廓修正

v2 为完整 420s 运行，`FAILED/task_timeout`。虽已换区并阻止同色管子／方块冲突导致的错误靠近，但西侧绕障时在北壁发生接触，不能算通过。三次执行的 approach 都指向真实黄色方块的可见表面约 [-4.43,0.88,1.05]，并非东侧管子；离线目标表面误差中位数约 0.0015m（理想深度环境，不代表真实相机精度）。实际碰撞盒平面 0.48×0.57m，外接半径约 0.373m；当前 0.25m 膨胀小于该半径。新增池体地图只是补齐占用信息，没有替代外廓安全距离。

第三轮使用独立 `config/navigation/profiles/complex_hull_clearance.json`（EGO inflation=0.40m、collision distance=0.45m）和 `config/semantic/complex_hull_task.json`（语义 clearance=0.40m、timeout仍420s），套件 `complex_hull_suite.json`。不改全局默认参数；窄通道可能被保守判为不可通行，这是保持真实碰撞盒不变时必须显式评估的代价。


### 膨胀形状一致性

第三轮完整运行 420.9s，14.04m，零接触，但仍 task_timeout，多次 BLOCKED_GOAL。源代码核对：外部 EGO `plan_env/src/grid_map.cpp/cloudCallback` 的 x/y 双重循环实现方形膨胀；语义候选原为欧氏圆形距离。第四轮在启用池体先验时明确切换语义 `inflation_metric=chessboard`，占用格来源、外廓距离和膨胀形状三者一起对齐；仍存在 0.1m 点云、0.15m 语义格、0.05m EGO 格量化差异，不宣称逐格完全相同。未修改外部 EGO 源码。


### 跨区转移候选

仅提高区域评分仍可能让算法留在东侧，因为原探索候选要求可见未知区域、具有信息增益。返回西侧的已观察走廊没有信息增益，因而没有候选。新增 `region_transfer`：备选搜索阶段，在已观察安全可达格中选择向目标区域进展的落脚点，沿已验证栅格路径截取不超过2m的中间目标。它不依赖目标坐标、不把未知区标为空闲。中途保持连续视觉检测，不重复执行完整原地扫描；接近目标区域后恢复局部扫描。遇到已知失败点仍使用原失败排除策略。

LLM 输入明确标记 `purpose=transit_to_unsearched_region_through_observed_free_space`，说明零信息增益的转移段仍是有效动作。不是直接把未知目标坐标交给导航。


第四轮结果：420.0s 超时，18.03m，零接触；表明膨胀形状修正并不能替代跨区转移策略。所有完整诊断轮保留失败原样，不能用它们宣称复杂错误先验场景已解决。第五轮测试显式跨区转移，同时回归另外两种布局。


### 第五轮错误先验结果

421.1s、15.66m、零接触，仍 `FAILED/task_timeout`（任务配置420s，日志终止时间有异步处理偏差）。Qwen 连续选择 `transfer_*`，完成经过已知走廊的分段返回；未记录 BLOCKED_GOAL。仍有两次进度不足，其中后期探索又转向区域外候选，最终未完成被遮挡目标确认和接近。不能宣称错误先验搜索已解决；下一步应对局部区域覆盖、遮挡视角选择和跟踪停滞做针对性迭代，而非提高超时。


### 回归注意

西侧正确先验场景的新配置也出现离开原区域的行为。当前换区根据预算而非覆盖率，无法区分“区域已充分看过”和“受遮挡尚未覆盖”，这是明确的策略不足。跨区转移只解决候选动作缺失，未解决何时应放弃一个区域。默认旧模型／旧导航入口保留，不推荐把本次整套候选配置作为已验收稳定版。


西侧回归也超时。PhysX 有1对接触报告，但最小 separation=+0.227m、最大 impulse=0，无穿透／冲量，属于接近报告，不能称为实际撞击。当前离线审核要求零接触报告，仍不通过；更主要的失败是正确西侧先验被过早放弃、最后未找到管子。


东侧回归在 EquipmentScreen 处出现1次非零冲量（约0.0150，最小 separation约+0.000025m），因此不满足无接触验收。池体静态先验不包含新增设备，设备仍由相机深度构建；不能将池体地图补齐解释为整个场景已无碰撞。正确东侧先验也被预算逻辑提前切换，应优先引入区域覆盖证据及可见性驱动视角选择。
