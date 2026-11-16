# 导航扫描效率迭代（2026-11-10）

## 回溯点

用户要求先保存当前版本，再继续迭代。基线提交 `373e25e` 已推送到 GitHub main，包含多场景语义导航实现、配置及既有验证记录。本文件及随后扫描改动尚未提交，等待用户验证。

## 问题与改动

原定向扫描总是转到 inspection_yaw + sweep/2，再顺时针扫描。当机器人离另一端更近时，会产生多余对齐旋转。新增 scan.nearest_endpoint（默认 true），选择更近的端点并决定扫描方向；不改变探索地图、扇区范围或目标确认条件，不使用场景真值。关闭参数可恢复固定端点选择。

扫描进度按指定方向累计，反方向摆动会扣除进度，避免把左右摆动误认为覆盖了新的视野。扫描仍受原时间预算和目标确认中断保护。

独立配置 config/semantic/profiles/efficient_scan.json 将 motion.max_yaw_rate_rad_s 从 0.25 提高到 0.30。该参数同时影响语义扫描、保持朝向和局部重观测；不是航行速度，也不是仅扫描时的加速。保持跟踪器角加速度限制及水动力系数不变。水动力控制器另有 max_yaw_rate_rad_s=0.25 限幅，单独调语义层无效。配套 config/experiments/hydro_components_fast_scan.json 将水动力控制器的指令限幅同步设为0.30；这是控制指令上限，不是修改阻力/浮力/惯性系数。默认速度暂不修改。

## 验证设计

相同黄箱场景、相同目标配置、同一 ROS domain 串行运行真实 Isaac Sim（headless、实际渲染相机）、YOLO、规则高层决策、A*/EGO 与部件水动力。

- baseline：提交版本，固定扫描端点，0.25 rad/s。
- nearest：新扫描逻辑，0.25 rad/s。
- efficient：中间试验，语义层0.35，但水动力控制器仍限幅0.25，验证了两层限幅不一致导致调参无效。
- consistent_limits：中间试验，两层限幅均0.35 rad/s。
- balanced：最终可选配置，两层限幅均0.30 rad/s。

所有原始结果在 logs/scan_efficiency_20261110，审计与图像在 docs/validation/scan_efficiency_20261110。规则策略没有真实 API 延迟，因此不能用本轮耗时直接与之前 Qwen 的 62.1 秒比较。本轮未调用云端 API，不能宣称新的 Qwen 闭环已通过。每组单次测试，不代表统计成功率。

## 可复现命令

```bash
python3 scripts/run_semantic_trial.py --gui --policy rule \
  --task-config docs/validation/semantic_diversity_20261110/seventh_batch/yellow_box_turn/config/task.json \
  --runtime-config config/semantic/profiles/efficient_scan.json \
  --overrides config/experiments/hydro_components_fast_scan.json \
  --scene-file scenes/pool_platform_semantic_yellow_box_turn.usda \
  --output "logs/efficient_scan_demo_$(date +%Y%m%d_%H%M%S)"
```

同时去掉 --runtime-config 和 --overrides 可使用默认较慢扫描；通过自定义补丁 {"scan":{"nearest_endpoint":false}} 可恢复固定端点。采用真正基线代码请使用 Git 回溯点，不覆盖当前工作区。

## 中间结果与取舍

nearest 54.8秒，对比基线54.6秒无明显改善：该场景原起点已是较近的一侧。这项修复改善不利朝向下的扫描对齐，不能宣称每个场景都会更快。

0.35双层限幅中间试验52.7秒，低速转向26.2秒，但累计偏航319.2°（基线256.4°），偏航加速度P95从0.150升至0.227 rad/s²。不能称作更平滑，因此不采用0.35作为默认设置，继续测试0.30折中。

61项单元检查、12项实际状态机方法检查通过。状态机测试覆盖反向摆动不误判扫描完成、双向扫描指令、目标确认中断和恢复预算；纯函数测试覆盖跨±π角度边界以及全部候选起始朝向。

## 黄箱实测汇总

| 配置 | 完成时间(s) | 低速转向(s) | 累计偏航(°) | 零接触审核 |
|---|---:|---:|---:|---|
| baseline | 54.6 | 28.8 | 256.4 | True |
| nearest | 54.8 | 28.8 | 257.2 | True |
| efficient | 54.7 | 29.2 | 258.7 | True |
| consistent_limits | 52.7 | 26.2 | 319.2 | True |
| balanced | 53.3 | 28.0 | 299.2 | True |

0.30同样没有表现为全面改进：耗时仅减少约1.3秒，累计转角及角加速度仍增大。因此较快配置仅供实验，不作为推荐默认值。默认保留0.25。当前可以确认完成了扫描端点选择和方向进度修复，不能宣称已经解决整体效率/平滑性问题。后续需要围绕目标进入视野时的减速与视线保持优化，而非继续增加扫描速度。

对照图：validation/scan_efficiency_20261110/comparison.png。上述低速转向包含必要的观察，不全部代表无效旋转。实际航程均约2.0–2.1米，单次差异不可当作稳定收益。

蓝管一米停靠回归（规则策略，0.30双层限幅）：23.8秒，0.802米，接触报告0对，严格审核True。仅作为第二场景可运行性检查，没有同轮蓝管基线，不宣称提速比例。
