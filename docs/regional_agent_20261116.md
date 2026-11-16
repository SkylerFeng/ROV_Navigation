# 区域先验驱动的目标搜索 Agent（2026-11-16）

## 目的与边界

把老师提出的“知道大致区域、通过实际观测确定目标、再局部接近”接入现有固定深度导航。区域先验只影响搜索观察点评分，既不是目标坐标，也不会覆盖已观测障碍或允许进入未知空间。导航和水动力沿用原系统，本次不改变水体、图像处理或障碍膨胀。

## 实现

1. `config/semantic/search_regions.json` 定义人工地图区域名称与世界坐标矩形，单位米。用 `--search-region 西侧设备区` 明确给任务附加先验；未知名称在启动前拒绝。也可通过 agent 配置直接提供 `coarse_region_xyxy`。目前不声称能从任意自然语言自动解析空间关系。
2. Agent 搜索阶段为 REGION_SEARCH / EXPANDED_SEARCH / GLOBAL_SEARCH。已观测、可达的候选观察点获得区域加权，区域外候选仍保留。区域时间预算在决策观测刷新时检查，未确认目标的搜索累计达到预算后，边界向外扩大；扩展次数用尽后取消区域偏好。这个条件是时间预算，**不等于已完成区域覆盖**。
3. 视觉检测按类别、颜色和空间邻近关联对象，保留最近八次可见表面位置，用原有指数平滑得到导航位置，新增相对窗口中位点的最大离散距离。持续多帧确认且离散度不超过阈值，才提供接近候选。位置离散度不是统计置信区间，也不能衡量位姿系统误差；目前仿真仍使用理想距离和真实位姿。
4. 确认的视觉目标优先于区域提示，即使目标在提示区域之外也可以接近。沿用有界局部重观测恢复策略处理目标丢失。
5. 接近途中，目标表面位置若持续可见、观测稳定且相对下发时位置变化超过阈值，在最小时间间隔后取消旧动作、安全保持，并重新生成/校验可达接近候选。不会直接把目标坐标发给控制器，也不绕过 A*/EGO。最终仍需满足视觉身份、距离、朝向和低速停留检查。
6. Agent 记忆向 Qwen 提供阶段、有效区域、扩展原因、之前动作结果；Qwen 在允许的动作与候选 ID 内选择。区域扩展和安全检查由确定性代码负责，LLM 不计算精确几何或低层推力。

## 参数

都在 `config/semantic/agent.json`，支持 `--agent-config` JSON 局部覆盖。

| 参数 | 默认值 | 用途 |
|---|---:|---|
| region_weight | 2 | 区域候选的软加权强度 |
| region_search_budget_s | 45 | 每级搜索预算，仿真秒；在观测刷新时检查 |
| region_expand_step_m | 1.5 | 每次向矩形四边扩展的距离 |
| region_max_expansions | 2 | 两次扩展后，下一次预算耗尽转为全局搜索 |
| localization_max_spread_m | 0.20 | 表面观测离散距离上限 |
| approach_update_distance_m | 0.35 | 接近目标位置变化触发阈值 |
| approach_update_interval_s | 8 | 两次接近下发之间的最小更新间隔 |

未提供区域时从 GLOBAL_SEARCH 开始；仍保留同一 Agent 的行动记忆。对照中所有分支使用同一视觉输入和同一目标命令。

## GUI 演示

```bash
cd /home/ache/Coding/rov_navigation
python3 scripts/run_semantic_trial.py \
  --gui --policy qwen --env-file .env.semantic \
  --instruction '请靠近黄色方块，距它表面保持一米。' \
  --search-region '西侧设备区' \
  --scene-file scenes/pool_platform_semantic_yellow_box_turn.usda \
  --domain 177 \
  --output "logs/region_demo_$(date +%Y%m%d_%H%M%S)"
```

另一个终端：`ROS_DOMAIN_ID=177 bash scripts/start_semantic_debug.sh`。有效区域和搜索反馈保存在 `semantic/events.jsonl` 的请求观测以及 `semantic/agent_memory.json`；现有 debug 的 costmap 和决策显示继续使用，尚未增加区域边界叠加绘制。

无提示对照：删除 `--search-region`；错误提示对照：改为 `东侧设备区`。这是可复现的人工任务先验，不从离线目标真值提取运行时坐标。

## 验证

记录见 [验证目录](validation/regional_agent_20261116/README.md)。单次场景对照用于验证集成行为，不用于估算成功率或证明搜索效率提升。状态机测试另外覆盖区域逐步释放、视觉目标优先、定位不稳定、稳定目标位置变化后的局部重规划。

四次真实 Qwen + Isaac 仿真全部通过离线审核、没有接触记录。常规三组：无提示 62.6 s / 1.983 m，正确提示 64.7 s / 2.103 m，错误提示 83.8 s / 2.569 m。短预算探针实际触发区域扩展和全局搜索转换后完成。91 项相关测试通过。

当前场景没有显示正确先验的效率收益；局部位置更新仅由状态机测试触发，真实导航中未出现足够大的位置变化。轨迹及相机截图已保存到上述验证目录。

没有提交或推送 GitHub。
