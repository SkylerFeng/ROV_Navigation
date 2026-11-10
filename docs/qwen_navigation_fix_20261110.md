# Qwen 导航失败诊断与迭代（2026-11-10）

## 原始故障

`logs/qwen_demo_20261110_154503`：扫描后仍有 6 个可达探索点，但 Qwen 返回 report，系统主动结束任务。
`logs/qwen_demo_20261110_154731`：第二次决策 ValueError；旧日志未保留具体原因，无法事后断言是哪一字段错误。两次仿真都记录正常关闭，非已确认的 Isaac 崩溃。

## 修复

- 扫描未完成或仍有可达探索点时，拒绝 report。
- 模型输入增加 allowed_actions，剔除不匹配目标的 approach 候选；探索候选仍来自观测地图，未注入场景真值。
- 明确观测新鲜度只约束接近，探索不要求先看到目标；增加带 candidate_id/object_id 的完整 JSON 示例。
- 本地校验动作类型、ID、目标身份与新鲜度，API 返回后再次校验实时状态。
- 无效响应/请求异常时悬停，用新观测与错误反馈重试；默认连续 3 次错误终止，总调用上限保留。有效执行后清零，无规则策略回退。
- 日志保存具体校验原因与被拒动作（适用时），终端显示 semantic_reason；不记录认证头和密钥。

## 中间测试（均保留）

screened_01：提前 report、reason_code 超长，3 次错误后受控终止，验证了重试上限。
screened_02：明确了探索行为，但模型漏填 candidate_id，3 次错误后受控终止。
用 screened_02 的第二次请求观测调用真实 Qwen 重放，补充完整示例后返回有效 frontier_24_26。
详细记录：`docs/validation/qwen_navigation_fix_20261110/iterations.json`。

最终完整测试结果见下文。

## 使用

```bash
python3 scripts/run_semantic_trial.py --gui --policy qwen --env-file .env.semantic \
  --scene-file scenes/pool_platform_semantic_screened.usda \
  --output "logs/qwen_demo_$(date +%Y%m%d_%H%M%S)"
```

配置：`config/semantic/runtime.json` 的 `llm.max_consecutive_errors`，默认 3。此前两次失败记录不代表修复后的成功率；少量场景测试也不构成统计成功率。水动力继续使用原部件模型，未更改物理参数。

## 首次完整成功：screened_03

真实 qwen-plus，headless Isaac Sim，相同 screened 遮挡场景：128.400 s 仿真时间，3.556 m 实测路径，3 次 API 调用，16 次 EGO 更新，0 接触记录。目标初始未检测到，最终距离目标表面约 0.990 m，符合当前接近容差。离线验证通过。

决策：1.50 s scan → 44.70 s explore(frontier_24_26) → 117.50 s approach(obj_008)。没有规则回退或向模型提供目标真值。

轨迹：`docs/validation/qwen_navigation_fix_20261110/screened_03/trajectory.png`。
核验：同目录 `audit.json`。最终仍使用理想距离传感器及真实相机/机体位姿，未验证真实水下视觉与定位误差。

screened_03 启动后仅细化了 missing candidate_id 的错误文本；screened_04 用细化后的版本复测。API 每次真实请求均可能有波动，少量成功不能保证所有场景成功。

## 复测：screened_04

同一遮挡场景再次真实调用 qwen-plus：143.300 s 仿真时间，3.844 m 实测路径，3 次调用，16 次 EGO 更新，0 接触记录，最终距目标表面约 0.999 m，离线验证通过。两次最终完整运行均没有 llm_error。

两次均为 scan → explore → approach，目标初始不可见；未修改场景、初始位置、水动力参数或成功判定来获得通过。测试使用 headless 模式，仍渲染 RGB/距离传感器；尚未做本轮 GUI 录像验证。现有扫描与转向对齐仍较慢，本次未宣称效率改进。

复测轨迹：`docs/validation/qwen_navigation_fix_20261110/screened_04/trajectory.png`；审计同目录 `audit.json`；统一指标、真实 API 响应及原始证据哈希在 `summary.json`（上一级目录）。启动器的终端字段随后由 failure_reason 更名为 semantic_reason，避免成功时误导；不改变决策或仿真行为。

## 回归与保存

66 项测试通过，覆盖语义约束、HTTP 协议、本地配置、部件水动力、跟踪与样条；详见 `docs/validation/qwen_navigation_fix_20261110/regression_tests.txt`。新增提前放弃拒绝、探索无需目标、搜索耗尽可报告、过滤干扰物接近候选及重试配置有效性测试。

原始失败与本次中间失败都保留在 logs 下，未冒充成功。没有提交或推送 GitHub，未修改 providers.json、task.json 的用户配置及本地密钥。此前项目结构整理等已有未提交修改保留。
