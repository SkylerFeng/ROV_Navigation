# Highbay 语义导航第一版 — 2026-11-04

> 2026-11-05 归档更新：用户已授权提交本版。以下正文保留开发时状态；当前归档范围、最终权重和验证边界见 semantic_release_20261105.md。best.pt 与 best.onnx 在本次作为明确例外纳入 Git，其他 logs 输出仍忽略。

## 完成状态

已实现独立语义场景、YOLO 数据集及训练、检测与空间定位、规则探索/接近、Qwen/DeepSeek 文本 JSON 决策接口及串行对照工具。平移继续使用 A* + EGO，物理继续使用部件级水动力。

**规则版已在真实 Isaac Sim 中完成三种场景的闭环验证；云端对照尚未完成。** 用户选择 DeepSeek，但当前 agent 环境没有 DEEPSEEK_API_KEY。HTTP/JSON 适配通过本地 stub 测试，这不代表 DeepSeek 实测。Qwen 同样只有适配代码，尚未实际请求。没有 commit 或 push，等待用户验收。

## 最终回归结果

以下每个场景只有一次最终回归，不是统计成功率。目标在初始检测中均不可见。

| 场景 | 结果 | 仿真用时 | 实测路径 | EGO 更新 | 接触记录 | 终态至目标表面 XY 距离 |
| --- | --- | --- | --- | --- | --- | --- |
| basic 基础搜索 | 成功 | 16.5 s | 0.341 m | 1 | 0 | 0.990 m |
| screened 遮挡探索 | 成功 | 142.3 s | 2.919 m | 17 | 0 | 1.007 m |
| relocated 目标换位 | 成功 | 30.0 s | 1.129 m | 1 | 0 | 0.752 m |

screened 实际执行扫描、移动探索、发现黄色管子、接近、朝向和悬停验证。基础场景目标较近，主要验证转向识别和短距离接近。不同运行时间/轨迹存在差异。

离线可见表面定位误差中位数为 1.23、0.92、4.73 cm，衡量估计点到理想圆柱表面的距离，不是目标完整中心误差；依赖理想距离与仿真真实相机位姿。表中终态距离以 ROV 位姿原点计算，不是船体外壳最小净距。

压力案例 occluded 在当前保守膨胀和观测地图下未找到连通观察点，记录失败，证据保留于 validation/semantic_navigation_20261104/blocked。不能据此断言连续真实空间绝对无路。

最终完整运行：logs/semantic_final_20261104/。发布证据：docs/validation/semantic_navigation_20261104/，包含 rule_comparison.json、各场景 audit.json、trajectory.png、latest_detection.jpg、scene_evidence.json、数据集统计、检测指标及单元测试结果。

## 独立场景与数据

scenes/pool_platform_semantic.usda 继承已有 pool_platform_ego.usda，最终引用 OceanSim-Highbay 的 Platform_black_water.usda 与其嵌入水体。独立添加黄色空心管、蓝色空心管、黄色箱子、红色箱子、ROV 前部检查灯；未覆盖原场景或修改外部源资产。灯光是合成条件，未经实物标定。

变体为 pool_platform_semantic_screened.usda（遮挡后目标）、pool_platform_semantic_relocated.usda（目标换位）和 pool_platform_semantic_occluded.usda（压力案例）。场景真值仅供训练标签与离线审计；运行时节点不读取 USD 或 evaluation_scene.json 的目标坐标。水池边界是已知先验。

数据集 logs/semantic_dataset_lit：36 布局 × 12 视角 = 432 帧，train 300 / val 60 / test 72；按完整布局分割，标签分别为 769 / 150 / 193 个。采用 OceanSim UW_Camera 渲染后的 RGB，以及可见实例掩码生成 YOLO bbox。两类为 pipe / box，颜色独立判断。

YOLO11n 训练 45 epoch，held-out test：precision 0.9833、recall 0.9116、mAP50 0.9570、mAP50-95 0.8826。这些是检测指标，不包含颜色准确率、导航成功率或真实水下泛化率。

水下颜色模型仅从 train 布局采样 yellow / blue / red / background 像素，构建平滑 RGB 直方图似然；置信不足输出 unknown。原 HSV 阈值因水下黄→暗绿偏移失败，已替换。新水质、灯光、曝光和真实相机的颜色效果尚未验证。

权重位于 logs/semantic_detector_lit/train/weights/best.pt 与 best.onnx；颜色模型位于 config/semantic/color_model.npz。logs 被 Git 忽略，提交源码不会携带 YOLO 权重；换机器须重训或另行分发带校验和的权重。数据与 ONNX 校验和见 dataset_summary.json。

## 同步感知与定位

run_sim.py 发布 /rov/rgb、/rov/depth_range、/rov/camera_info、/rov/camera_pose，同一帧时间戳。节点只处理四项均齐备的帧。

OceanSim distance_to_camera 是沿视线距离 r，不能作为 optical Z：

~~~text
ray = normalize([(u-cx)/fx, (v-cy)/fy, 1])
p_world = R_world_camera * (r * ray) + camera_position
~~~

ROS optical frame 为 x 右、y 下、z 前；四元数输入顺序 wxyz。检测框内用颜色前景与距离中值抑制背景；输出可见表面质心，不是完整物体中心。需要连续多帧确认并进行时空关联。

当前使用理想距离图与真实相机/ROV 位姿，**不是 SLAM**，没有定位漂移模型。模拟水动力真实执行不等于感知已达到真实水下条件。

## 探索、导航与成功判定

0.15 m free/occupied/unknown 网格来自有效距离射线。端点在导航高度内记 occupied，射线在该高度内的经过段提供 free；端点落在地板/天花板上的射线也可贡献部分自由空间。候选中心需已观测、与当前位置连通，并以 0.5 m 净距保守膨胀障碍/边界。

采用视线信息增益、未知区域连通块、已扫描位置及访问惩罚选择观察点。这是 2.5D 近似，不是完整体积安全证明；EGO 继续根据原导航占用图避障。

规则逻辑：scan → explore → approach → 本地验证；探索途中发现目标可打断。接近点取观测表面外约 0.8–1.08 m，并朝向目标。成功条件：类别/颜色及多帧身份有效、最近可见、距离合格、朝向误差 <12°、速度 <0.045 m/s，连续维持 2 秒。LLM 无权直接宣告成功。

平移目标经 /move_base_simple/goal 调用 A* + EGO。tracker 的短时控制租约负责扫描和终态朝向，只有 ROV_SEMANTIC=1 时开启；失联时停止执行旧轨迹，传感器超时明确失败。水动力配置为 config/experiments/hydro_components.json，包含已有部件阻力、水流、浮力、附加质量和推进响应；不是 CFD。

## 文本 JSON 决策

semantic_llm.py 通过标准库 HTTP 调用服务，不依赖 OpenAI SDK。发送文本任务、目标属性、简化对象观测、候选 ID、执行结果；不发图像、USD 或目标真值坐标。

允许 scan / explore / approach / hold / report，示例：

~~~json
{"task_id":"...","observation_id":12,"action":"approach","object_id":"obj_008","candidate_id":"approach_obj_008","reason_code":"confirmed_target"}
~~~

验证字段、task/observation ID、目标类别/颜色、确认状态、时效及候选可达性；异步等待时悬停，响应回来后重新计算候选并校验。API 错误或非法动作明确失败，不静默退回规则而伪装成云端结果。任务最多 30 次请求，单次 HTTP 超时 15 秒，真实延迟与费用尚未验证。

任务在 config/semantic/task.json；文字与 category/color 必须一致，本版尚无任意自然语言的独立解析器。视觉词汇只覆盖 pipe / box 与 yellow / blue / red。

## 本机 demo

先关闭其他 Isaac 实例，避免 8 GB 显存不足。本机依赖及权重已准备，不需重训。

~~~bash
cd /home/ache/Coding/rov_navigation
python3 scripts/run_semantic_trial.py --gui --policy rule --scene-file scenes/pool_platform_semantic_screened.usda --output logs/semantic_demo_my_first
~~~

命令自动启动 Isaac、A*/EGO 和语义节点，设置独立 ROS domain 与部件水动力。不要另外运行 send_goal.sh。输出目录必须新建，结束自动退出仿真。仅 GUI 打开 USD 不会启用这些回调。

基础场景改成 scenes/pool_platform_semantic.usda，换位使用 scenes/pool_platform_semantic_relocated.usda。绘图和审计：

~~~bash
python3 scripts/analyze_semantic_trial.py logs/semantic_demo_my_first --output logs/semantic_demo_my_first/analysis
~~~

## DeepSeek 和对照

在运行终端设置 DEEPSEEK_API_KEY，也可建立被 Git 忽略的 .env.semantic，内容为 DEEPSEEK_API_KEY=...。不要发到聊天。文件只按 KEY=value 解析，不执行 shell；其他终端 export 不会自动进入已经运行的 IDE/agent 进程。

~~~bash
export ROV_SEMANTIC_ENV_FILE="$PWD/.env.semantic"
python3 scripts/run_semantic_trial.py --gui --policy deepseek --scene-file scenes/pool_platform_semantic_screened.usda --output logs/semantic_deepseek_my_first
python3 scripts/compare_semantic_policies.py --policies rule deepseek --scenes basic screened --repeats 3 --env-file .env.semantic --output logs/semantic_comparison_my_first
~~~

无密钥的项记为 NOT_RUN。配置在 config/semantic/providers.json，可由 ROV_LLM_MODEL / ROV_LLM_BASE_URL 覆盖；账号可用型号需实际请求验证。Qwen 选择 --policy qwen 并设置 DASHSCOPE_API_KEY。

对照固定场景、权重、水动力，串行运行；记录完成、用时、路径、碰撞、EGO 更新。API latency/usage 记录在 events.jsonl。一次运行不能得出成功率结论。

## 从源码复现

~~~bash
bash scripts/setup_semantic.sh
bash scripts/usd_python.sh scripts/build_semantic_scene.py
bash scripts/usd_python.sh scripts/build_semantic_variants.py
/home/ache/isaac-sim/python.sh scripts/generate_semantic_dataset.py --output logs/semantic_dataset_new --layouts 36 --views 12 --seed 41
python3 scripts/semantic_color.py --samples logs/semantic_dataset_new/color_samples.npz --output config/semantic/color_model.npz
PYTHONPATH="$PWD/.venv/semantic_packages" /home/ache/isaac-sim/python.sh scripts/train_semantic_detector.py --data logs/semantic_dataset_new/dataset.yaml --output logs/semantic_detector_new --epochs 45
~~~

生成/训练拒绝覆盖已有目录。新权重可通过 start_semantic.sh --model 指定；一键 trial 默认 logs/semantic_detector_lit/train/weights/best.onnx。setup 复用本机 Isaac Python 3.11 的 torch/torchvision 和系统 ROS Humble Python 3.10 的 numpy/OpenCV/scipy/matplotlib，非跨平台通用安装器。

## 限制

小型合成数据、静态物体、固定水质与照明、理想深度/定位、保守二维探索；没有声呐融合、真实水下验证或真实云端对照。已保留失败压力案例，不能把迭代失败或未运行云端项混入成功统计。后续先由用户看 demo，配置 DeepSeek 后再进行真实对照，确认后才提交 GitHub。

## 测试记录

最终本地回归通过 55 项测试，包括 19 项语义/HTTP协议/凭据解析测试及已有水动力、跟踪、样条测试。详见 validation/semantic_navigation_20261104/regression_tests.txt。DeepSeek 实际跳过结果见 deepseek_comparison_pending.json，状态为 NOT_RUN，未发出云端请求。
