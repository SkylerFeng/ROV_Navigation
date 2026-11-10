# 导航调参入口

规划、速度、转向与轨迹跟踪参数请先看 [navigation/README.md](navigation/README.md)，配置位于 `navigation/default.json`，实验配置放 `navigation/profiles/`。

# 配置与调参入口

## 目录职责

| 文件/目录 | 作用 | 修改后何时生效 |
| --- | --- | --- |
| semantic/providers.json | Qwen/DeepSeek 的 API 地址、模型名、密钥变量名 | 下次启动 |
| 项目根目录 .env.semantic | 私有密钥，不提交 Git；可从 .env.example 复制 | 显式 --env-file 或 ROV_SEMANTIC_ENV_FILE 加载 |
| semantic/task.json | 目标类别/颜色、接近距离、确认帧数、网格分辨率、任务超时 | 下次启动 |
| semantic/runtime.json | 扫描、探索候选、完成验证、保持控制、LLM 调用参数 | 下次启动 |
| semantic/profiles/ | 仅包含想改变的语义运行参数；不复制整个默认配置 | --runtime-config 选择 |
| experiment.json | 共享导航、相机、水动力基础参数 | 下次启动 |
| experiments/hydro_components.json | 部件水动力覆盖参数；语义启动默认使用 | --overrides 选择 |
| scenarios_semantic.json | 语义场景边界、起点、观察相机位置 | 下次启动 |
| hydrodynamic_components/bluerov_mesh.json | 编译后的几何采样；通常不手工改 | 从网格提取工具重建 |

scripts 保留既有启动路径；semantic_config.py 集中加载与校验，semantic_navigation.py 管任务状态，semantic_core.py 管定位/地图/候选/动作校验，semantic_llm.py 管 API，semantic_motion.py 管保持和扫描控制。scripts/start_*.sh 为环境启动层，ros_ws 为规划层，scenes 为 USD，docs 为版本记录/正式图表，logs 为每次运行产物。此次不移动历史实验和原始资产。

## 推荐使用方式

先检查，不启动 Isaac，也不请求云端：

```bash
cd /home/ache/Coding/rov_navigation
python3 scripts/run_semantic_trial.py --check-config
python3 scripts/run_semantic_trial.py --policy qwen --check-config
```

第二条会输出 credential_present 的布尔值，不输出密钥。配置检查通过不等于 API 连通或账号权限通过。

从模板创建本地密钥文件时不要覆盖已有文件：

```bash
cp -n .env.example .env.semantic
# 在编辑器中填写 DASHSCOPE_API_KEY，勿发到聊天中。
```

可视化运行 Qwen：

```bash
run_dir="$PWD/logs/qwen_demo_$(date +%Y%m%d_%H%M%S)"
python3 scripts/run_semantic_trial.py --gui --policy qwen \
  --env-file .env.semantic \
  --scene-file scenes/pool_platform_semantic.usda \
  --output "$run_dir"
```

规则模式用 --policy rule，不需要 --env-file。现有启动命令仍然有效。普通导航的 start_navigation.sh/start_sim.sh 接口保持不变。

## 常用调参

### 任务与感知：semantic/task.json

- instruction、category、color：目标描述及匹配字段；目前需要手动保持一致，不是任意自然语言解析。
- detector_confidence：YOLO 置信度阈值，默认 0.45；提高可能减少误检，也可能漏检。
- confirmation_frames：目标确认累计观测次数，默认 3。
- surface_standoff_m：接近候选的目标表面水平间距，默认 0.8 m，不是船体净距。
- grid_resolution_m：观测网格分辨率，默认 0.15 m。
- clearance_m：地图障碍膨胀参数，默认 0.5 m；减小会影响避障裕量。
- max_observation_age_s：目标候选、规则决策、JSON 校验共同使用的最大观测年龄，默认 2 s。
- hold_seconds、max_speed_at_completion：完成前停稳持续时间和速度阈值。
- timeout_sim_s、action_timeout_sim_s：总任务和单动作的仿真时间限制；仿真进程总上限由任务上限 +10 s 推导。
- depth_m 当前只允许 1.0：现有规划、候选和控制固定世界 Z=1.0 m，不能误当成相对水面深度。改变高度需要联合修改系统，暂不开放伪调参。

自定义任务文件支持部分覆盖：例如保存 {"instruction":"找到蓝色管子并靠近","color":"blue"}，启动时传 --task-config 文件路径；未填写项继承 task.json。

### 扫描与探索：semantic/runtime.json

| 参数 | 默认 | 含义 |
| --- | --- | --- |
| scan.sweep_deg | 351.4056 | 无目标时单次累计扫描角度，原实现为 2π−0.15 rad |
| scan.timeout_s | 45 | 单次扫描超时，仿真秒 |
| scan.yaw_step_rad | 0.8 | 扫描时动态目标朝向偏差；不是实际角速度 |
| motion.max_yaw_rate_rad_s | 0.25 | 语义扫描/保持控制输出的角速度上限 |
| motion.yaw_kp | 0.8 | 朝向误差到角速度命令的增益 |
| motion.hold_max_speed_m_s | 0.12 | 保持位置时每轴速度命令限幅，不是航行最高速度 |
| exploration.max_candidates | 6 | 最大探索候选数 |
| exploration.min_viewpoint_separation_m | 0.7 | 与已扫描位置的最小距离 |
| exploration.min_travel_m | 0.45 | 探索候选的最小路径长度 |
| exploration.candidate_separation_m | 0.6 | 同批探索候选之间的间距 |
| exploration.viewpoint_radius_m | 3.0 | 从未知区域附近选观察位置的范围 |
| exploration.min_unknown_cells | 10 | 值得探索的未知连通区域最小单元数 |

实际转向还受到 experiment.hydrodynamics.max_yaw_rate_rad_s、力矩限制和阻力影响。调整一个上限不能保证实际速度达到该值。

试验配置 semantic/profiles/short_scan.json 将扫描角度改为 180°、超时改为 35 s，其余沿用默认值：

```bash
python3 scripts/run_semantic_trial.py --check-config \
  --runtime-config config/semantic/profiles/short_scan.json

run_dir="$PWD/logs/short_scan_$(date +%Y%m%d_%H%M%S)"
python3 scripts/run_semantic_trial.py --gui --policy rule \
  --runtime-config config/semantic/profiles/short_scan.json \
  --output "$run_dir"
```

缩短扫描可能减少初始等待，也可能漏掉背后的目标；这不是已验证优于默认的方案。此次未修复候选受阻后重复选择等策略问题，调参不等于修复状态机。

### 完成验证与 API 调用

- verification：heading_tolerance_deg=12、freshness_s=0.6、timeout_s=20、distance_near_margin_m=0.12、distance_far_margin_m=0.35。距离判定为 standoff−near 到 standoff+far。
- execution.max_llm_calls=30：每任务调用次数上限；tick_s=0.1、snapshot_interval_s=2 控制状态更新与快照间隔。
- llm.timeout_s=15：HTTP 墙钟超时；temperature=0、max_tokens=350、enable_thinking=false。当前 JSON 协议只支持关闭 thinking。
- 模型/服务地址在 providers.json，不把密钥写入这里。ROV_LLM_MODEL / ROV_LLM_BASE_URL 环境变量优先于文件；如之前设置过 DeepSeek 的覆盖，切换 Qwen 前应检查或 unset。

### 水动力、规划与显示

复制 experiments/hydro_components.json 为自己的实验文件，在保留 component_model_file 等字段的基础上加入 hydrodynamics.current_world_m_s、force_tau_s、torque_tau_s 或 velocity_kp。用 --overrides 指定。该文件在共享 experiment.json 与场景配置上覆盖；选择新文件是替换默认 hydro_components 覆盖文件，不是再叠一层，因此应从它复制。

max_velocity、max_acceleration、max_heading_error_deg 等导航参数也可放在实验覆盖文件顶层。观察视角可用 --view top / perspective；语义观察位置在 scenarios_semantic.json 的 overview_eye/overview_target。水面反光值属于 USD 材质，display_water_opacity 是配置说明字段，不能假定修改它就会实时改材质；重建规则在 build_semantic_scene.py。

## 参数优先级和复现

语义参数：默认 JSON → --task-config/--runtime-config/--providers-config 部分覆盖。运行参数若未指定 CLI 路径，也兼容 ROV_SEMANTIC_RUNTIME_CONFIG。API 模型/地址还受 ROV_LLM_MODEL/ROV_LLM_BASE_URL 覆盖。

密钥：进程已有环境变量优先；--env-file 优先于 ROV_SEMANTIC_ENV_FILE 指定文件。文件加载使用 setdefault，不覆盖已有环境。不会自动读取项目内任意 .env；规则模式忽略密钥文件。

每次运行保存 effective_config.json 与 config/{task,runtime,providers,experiment}.json；语义节点、tracker、仿真和规划器使用这次的配置快照。manifest 包含快照与所选模型/覆盖文件校验和，不复制 .env 或 API 密钥。--wall-limit 与 HTTP timeout 使用真实秒；任务/动作/扫描超时使用仿真秒。

批量对照 compare_semantic_policies.py 同样支持 --task-config、--runtime-config、--providers-config、--overrides、--model、--env-file。新配置先做 --check-config，再单场验证，最后做重复实验。已有成功结果对应其原参数，不随配置修改自动成为新版的成绩。

### 云端决策失败重试（2026-11-10）

`config/semantic/runtime.json` 中 `llm.max_consecutive_errors` 控制连续无效响应/请求异常的终止阈值，默认 3（初次失败后最多再尝试两次）。每次使用最新观测，悬停等待，向模型反馈校验原因；有效执行后清零。总调用数仍受 `execution.max_llm_calls` 限制。不自动回退规则策略。

尚未完成扫描或仍有可达探索点时，禁止模型通过 `report` 提前结束搜索。终端输出 `semantic_reason`，详细记录位于 `semantic/events.jsonl`。

### 接近验证与恢复

`exploration.approach_retry_separation_m`（默认 0.45 m）：一次到达验证超时后，本次任务后续接近候选必须与该失败停靠位置保持此间隔。候选仍需通过原安全可达性与距离检查。验证中用新鲜目标位置更新朝向；超时后请求就地重新观察。`semantic/events.jsonl` 的 `verification` 事件包含可见性、观测年龄、距离、速度、朝向误差；`verification_sensor.npz` 保存最近一次验证的相机快照（不是视频）。

### 稳定导航与目标局部恢复（2026-11-10）

`semantic/runtime.json` 新增 recovery：`timeout_s`（局部重观测上限16秒）、`look_s`（先面向目标4秒）、`sweep_deg`（左右各25度）、`max_attempts`（最多2次）、`association_radius_m`（0.7米，用于关联已确认的附近目标）、`target_memory_s`（记忆方向有效期30秒）、`cooldown_s`（恢复失败后12秒不打断探索）、`explore_commit_s`（探索至少执行4秒才可因目标打断）。记忆只用于朝向与恢复，不作为完成证据。

默认 scan.sweep_deg 从约351度改为120度，timeout_s 改为25秒；超过预算结束扫描转入决策，而非无限转动。仍可能因转向对齐短暂原地旋转。原任务完成标准、300秒总预算不变。

### 自然语言任务与多环境验证

`run_semantic_trial.py --instruction "不要黄色管子，请靠近蓝色管子。" --policy qwen` 会先真实调用文本模型解析任务，再冻结 category/color/距离，保存 instruction.json。含糊或超出当前单目标能力时返回 instruction_clarify / instruction_unsupported，不启动仿真。--check-config 不调用 API。

`execution.progress_timeout_s`（30秒）及 `progress_distance_m`（0.15米）用于识别持续未接近子目标的情形，并触发重新选择视点。值过小可能把必要绕行/转向误判为停滞。

多环境批次配置：semantic/diversity_suite.json；命令 `python3 scripts/run_semantic_diversity.py --output logs/新的目录`，串行启动真实 Qwen 和 Isaac，会产生 API 费用。详见 docs/semantic_diversity_20261110.md。

`runtime.json` 的 `exploration.explore_retry_separation_m`（默认 0.6 m）控制本次任务中受阻、无进展或超时探索点的排除邻域。它不改变障碍膨胀距离，也不用于判定导航成功。`scan.max_sectors_per_viewpoint` 限制候选耗尽时追加的观察扇区数量。

`runtime.json` 的 `exploration.inspection_range_m`（默认 2.5 m）是语义搜索的近距离视觉覆盖范围。深度射线仍可更新更远处的可通行地图；只有实际相机射线在此范围内覆盖的区域才记为已近距离检查。该标记不等于目标已被正确识别，完成条件仍要求多帧 YOLO 身份、距离、朝向和低速停留验证。

探索评分的 `gain_power`（默认 0.5）控制信息收益递减程度，`travel_cost_weight`（默认 2.0）控制旅行距离代价。提高前者更偏向大块未检查区域，提高后者更偏向附近视点。最小视点间距和失败点排除仍独立生效。

导航 `tracker.near_track_crab_deg`（默认 15°，上限 30°）限制近轨迹范围内的横向修正角，避免厘米级横向误差让 ROV 追着目标航向原地转圈。该参数和 `tracker.position_kp` 同时传到 C++ 的轨迹暂停判定；修改 C++ 后先运行 `bash scripts/build_planner.sh`。
