# 2026-11-11 三条 Qwen 指令组会材料

本次实际串行运行三个独立任务，使用 Qwen API（qwen-plus）、YOLO、A*/EGO 导航与部件级水动力。Isaac Sim 使用 headless 模式并实际渲染相机，没有录制 GUI 视频，没有改导航参数或提交 GitHub。

## 材料入口

- [三页汇报 PDF](figures/meeting_report_20261111/report_slides.pdf)
- [完整材料索引](figures/meeting_report_20261111/README.md)
- [蓝管单页](figures/meeting_report_20261111/blue_pipe/report_slide.png)
- [黄箱单页](figures/meeting_report_20261111/yellow_box/report_slide.png)
- [红箱单页](figures/meeting_report_20261111/red_box/report_slide.png)

每任务包含实测路径图、末次保存的 RGB 原图、同批快照的检测叠加图、轨迹 CSV、运动曲线、决策阶段 MD/CSV、原始决策事件、离线审核、配置和物理接触记录。sources.json 保存原始数据文件校验值。

## 本次结果

| 指令 | 仿真耗时 | 航程 | 最终水平表面距离 | 运行时决策调用 | 离线审核 |
|---|---:|---:|---:|---:|---|
| 不要黄色管子，请靠近蓝色管子，距它表面保持一米。 | 29.5 s | 0.95 m | 0.995 m | 2 | 通过，无接触报告 |
| 靠近黄色方块，不要找管子。 | 64.5 s | 2.19 m | 0.988 m | 4 | 通过，无接触报告 |
| 请找到红色箱子，在距离它表面八十厘米的位置停住。 | 223.6 s | 3.89 m | 0.738 m | 9 | 未通过，有接触；运行时停靠确认成功 |

调用数不包含各任务启动时的一次自然语言指令解析。黄箱指令未指定距离，使用任务默认 1 m。

## 建议讲述顺序

1. 蓝管：先解析颜色、类别、排除目标和停靠距离，再扫描，识别后接近。展示相同场景中能区分不同语义目标；不能仅凭本次结果宣称具备任意语言理解能力。
2. 黄箱：1.9 s 扫描 → 19.5 s 探索 → 31.9 s 再扫描 → 48.3 s 接近 → 64.8 s 输出成功事件。轨迹中的绕行包含探索阶段，不是从开始就知道目标坐标。耗时统计与事件时钟存在起始时间差。
3. 红箱：两轮探索后在 84.3 s 接近目标，109.0 s 和 191.3 s 两次停靠确认失败，经历恢复和重新接近，223.9 s 输出成功事件。该项展示复杂任务与局限，不作为无碰撞成功案例。

红箱物理日志记录 ROV CollisionHull 与 Screen 遮挡板约在 77.93–90.30 s 发生接触报告：同一对碰撞体有 743 条报告，其中 668 条非零冲量，最小间距 -0.000265 m，最大记录冲量模长约 0.0995。不能将“1 个接触物体对”解释为“仅碰撞一次”，也不能忽略运行时成功前的接触。109 s 的确认失败记录目标不可见，之后恢复超时并重新探索。具体见对应 stages/stages.md、semantic/events.jsonl 和 sim/run.json。

## 复现与导出

```bash
cd /home/ache/Coding/rov_navigation
python3 scripts/run_semantic_diversity.py \
  --cases config/semantic/meeting_report_suite.json \
  --output "logs/meeting_report_$(date +%Y%m%d_%H%M%S)" --domain 167

# 本次已完成运行的离线导出，不再次调用 API
python3 scripts/package_meeting_report.py \
  logs/meeting_report_20261111/suite.json \
  --output docs/figures/meeting_report_20261111
```

使用现有本机密钥配置，材料中不复制凭据。脚本语法检查与 git diff --check 通过。

## 统计边界

三项各运行一次，不能估计稳定成功率。目标起始均未被检测到；定位使用仿真深度及真值位姿。目标真值仅用于离线轨迹标注和审核。最终距离是 ROV 参考位置到目标水平投影表面的距离，与检测图中的相机测距不同。

相机图为末次已保存快照，保存间隔约 2 s，未必是仿真结束的最后曝光帧；对应处理时刻分别为 28.3、63.3、222.1 s，见 camera_metadata.json。原始水下图像较暗，未做增亮或重推理。GUI 运行的调度条件不同，不能保证与本批结果一致。
