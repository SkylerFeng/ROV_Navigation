# 组会准备：部件级水动力与视觉语义导航

准备日期：2026-11-05。代码基线：2538983；部件水动力历史版本：919b2a4。建议 8–10 分钟，7 页主讲，另附实验边界。

## 一句话主线

上一阶段解决已知坐标下的 A* + EGO 导航；这一阶段同时完善运动模型与任务输入：按几何位置计算分布式阻力及力矩，并让 ROV 从视觉中发现语义目标、估计位置并执行接近。LLM 的结构化决策接口已实现，先用规则策略验证完整闭环。

## 版本核对

已比较 919b2a4 与当前 HEAD：scripts/hydrodynamics.py、scripts/component_hydrodynamics.py、config/experiments/hydro_components.json、config/hydrodynamic_components/bluerov_mesh.json 没有差异。当前版本可显式启用相同模型，不需要切换主分支。工作区 mixed 场景存在既有未提交材质改动，因此当前视频应标注为“当前版本启用相同部件水动力模型”，不能声称是历史提交完整环境逐字复现。

## 第 1 页：本阶段目标（约 40 秒）

标题：从坐标导航走向水动力环境下的视觉目标导航。

讲稿：此前已打通相机点云、A* 全局引导、EGO 局部规划与 ROV 控制。本阶段主要完善两端：运动端从整体阻力走向几何分布受力；任务端从指定坐标走向寻找指定类别和颜色的物体。

## 第 2 页：部件级水动力怎样工作（约 90 秒）

配图：[网格采样与几何连通片](figures/component_hydrodynamics_20261102/mesh_components.png)。

整台 ROV 仍然是一个刚体。从实际 USD 网格中提取 1,127 个几何连通片，聚合成 8,441 个表面采样，每个采样保留面积、位置与法线。这里的连通片不是已经语义标注的机械总成。

每个采样相对质心的力臂为 r_i，局部相对水流速度为：

    u_i = R^T (v_world - current_world) + omega_body × r_i
    F_total = Σ F_i
    torque_total = Σ (r_i × F_i)

F_i 由局部法向/切向速度、面积、浸没比例和阻力系数计算。转向时各位置速度不同，因此阻力分布不同；不对称受力通过力臂产生姿态力矩。各处受力在数值上汇总，最后将等效合力与合力矩施加到同一 PhysX 刚体，不是把 ROV 拆成多个独立刚体。

推荐措辞：“引入几何依赖的分布式阻力与力矩，使模型能够表达不同部位的运动响应。”不要直接说“已经证明更接近实机”：系数未标定，尚无实物对照。浮力和附加质量仍保留原近似，并非全部由网格求解。

## 第 3 页：水动力验证与导航 demo（约 90 秒）

配图：[急停、滑行与转向探针](figures/component_hydrodynamics_20261102/motion_probes.png)；可附[Mixed 轨迹与姿态](figures/component_hydrodynamics_20261102/platform_ego_mixed.png)。

- 历史主动制动探针：最大俯仰绝对值 3.681°。撤推滑行探针：最大前向位移约 16.91 cm。两者初速 0.3 m/s；主动制动使用固定反推，不等同生产导航急停控制。
- 历史 Mixed 单次导航：横流 0.08 m/s，129.47 s 到达，路径 7.435 m，终点误差 7.79 mm，最大俯仰绝对值 4.812°，未记录接触事件。
- 视频展示绕障、转向、减速与停稳；姿态曲线补充肉眼不明显的变化。不要人为调大扰动来冒充模型验证。
- 当前角速度控制会主动制动，停转后的净续转较小；净角增量不能称为最大过冲。

来源：[部件水动力记录](component_hydrodynamics_20261102.md)及其 validation 汇总。以上数值来自历史实验，不应直接贴到新录制视频上当作新测结果。

## 第 4 页：YOLO 与决策系统的分工（约 90 秒）

建议画成如下框图：

    目标描述 / 类别与颜色配置
                  ↓
    RGB → YOLO 类别检测 → 颜色判断
                + 同步距离图、相机内参/位姿
                  ↓
        目标表面位置 + 时序记忆 + 观测地图
                  ↓
          可达探索 / 接近候选位置
                  ↓
        规则策略（已验证） / 文本 LLM（接口已实现）
                  ↓
            JSON 动作校验与执行
                  ↓
          A* → EGO → 控制器 → 部件水动力刚体
                  ↓
                 新观测

YOLO 检测 pipe / box，颜色由独立模型判断；距离与相机参数负责空间定位，不能说 YOLO 单独输出三维位置。LLM 接收精简结构化信息，选择已有候选 ID，不直接输出推进器指令或任意世界坐标。

## 第 5 页：已验证的视觉闭环（约 90 秒）

配图：[RGB、距离与检测](figures/semantic_report_20261105/01_camera_and_detection.png)、[轨迹与决策时间线](figures/semantic_report_20261105/02_trajectory_and_decisions.png)。

任务：固定高度寻找黄色管子；初始检测中没有目标。系统扫描、选择探索点、确认目标类别和颜色、估计表面位置、规划接近、朝向目标并低速停留。

报告图对应反光修复前的 screened 单次规则实验：142.3 s、路径 2.919 m、EGO 更新 17 次、接触记录 0；不能称为 LLM 的决策结果。最新反光修复后基础场景已单次通过，但复杂场景尚未全部重测。

可选感知指标：独立渲染布局测试集上，pipe / box 检测 mAP50=0.957、mAP50-95=0.883。指标不包含颜色正确率、导航成功率或真实水下泛化。

## 第 6 页：LLM 已实现什么、还缺什么（约 60 秒）

已实现 Qwen/DeepSeek 文本接口、JSON 输出约束、候选 ID 和观测时效校验、超时处理及本地 HTTP stub 测试。动作集合为 scan、explore、approach、hold、report；report 表示无法继续，不是宣告成功。任务完成由本地身份、距离、朝向、速度与停留检查判定。

目前云端模型尚未完成真实闭环对照。可讲：“为 LLM 接入建立了可运行的感知、候选动作与执行接口，并用规则基线先验证闭环。”不要讲“LLM 已学会水下探索”或把 rule 视频标为 DeepSeek。

任意自然语言理解也尚未验证：当前 instruction 与 category/color 配置应保持一致。

## 第 7 页：下一步（约 40 秒）

1. 同场景、同模型、同初态重复运行规则与 DeepSeek，对比任务完成、碰撞、用时、路径、调用次数与延迟；明确区分失败与未运行。
2. 水动力筛除内部面、识别机械部件类别并标定阻力系数；现模型不含遮挡、尾流或 CFD 压力求解。
3. 逐步加入测距噪声与定位误差；当前深度和位姿是理想仿真条件。

## 录制 A：当前版本启用历史部件水动力（一个终端）

关闭其他 Isaac Sim 与导航进程，先准备好录屏。下列入口自动启动仿真、导航和目标发布，默认俯视，等待就绪后延迟 5 秒仿真时间发送目标；到达或触发终止条件后窗口关闭。

```bash
cd /home/ache/Coding/rov_navigation
hydro_run="$PWD/logs/suites/meeting_hydro_$(date +%Y%m%d_%H%M%S)"
env -u ROV_SEMANTIC python3 scripts/run_suite.py \
  --gui --scenarios platform_ego_mixed \
  --overrides config/experiments/hydro_components.json \
  --output-dir "$hydro_run" --domain 123 --goal-delay 5 \
  --sim-time-limit 180 --wall-time-limit 650 \
  --arrival-tolerance .05 --settle-time 2
```

env -u ROV_SEMANTIC 防止此前语义控制开关污染普通导航；此命令不改活动场景配置。结果位于输出目录下 platform_ego_mixed/run.json、controls.json 与导出的分析文件。录制时可手动靠近 ROV 观察姿态，但保留轨迹全景作为主画面；旧默认 Perspective 位置可能被扫描环境遮挡，优先使用 Top view。现有 probe_component_hydrodynamics.py 是 headless 物理验证，不是完整水池录像入口。

## 录制 B：视觉探索与接近（另一次运行）

```bash
cd /home/ache/Coding/rov_navigation
semantic_run="$PWD/logs/semantic_meeting_$(date +%Y%m%d_%H%M%S)"
python3 scripts/run_semantic_trial.py --gui --policy rule \
  --scene-file scenes/pool_platform_semantic_screened.usda \
  --output "$semantic_run"
python3 scripts/analyze_semantic_trial.py "$semantic_run" \
  --output "$semantic_run/analysis"
```

此入口自动启用部件水动力；不需要另发目标。录像字幕写“规则基线：视觉探索与接近”。如复杂场景未成功，保留结果并使用已有真实历史成功录像/图表，不能将失败片段剪辑成成功实验。用于快速检查可把 scene-file 改为 scenes/pool_platform_semantic.usda。

## 汇报结尾

本阶段完成了两个基础能力：运动端具有几何依赖的水动力与姿态响应；任务端建立了视觉目标到导航执行的闭环。下一步用相同环境对照规则策略与真实云端 LLM，评估高层决策是否带来可量化收益。

本文件是汇报准备材料；本次未启动 GPU 录制、未切换版本、未新提交 GitHub。
