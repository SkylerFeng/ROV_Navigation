# 11月12日组会：多目标语义导航录制

准备日期：2026-11-11。新增录制入口和阶段导出尚未提交。当前不是已经录制完成的三段视频。

## 展示顺序

1. 蓝管：指令“不要黄色管子，请靠近蓝色管子，距它表面保持一米”。讲目标类别/颜色和距离约束。
2. 黄箱：指令“靠近黄色方块，不要找管子”。讲相同颜色不同类别的区分。最近GUI运行曾错误确认目标并折返，不能保证每次成功，应保留失败与恢复片段。
3. 红箱遮挡：指令“请找到红色箱子，在它旁边停住”。讲探索、视野遮挡、重规划。历史版本通过，当前录制版本尚未复测；更适合作为复杂案例，不能提前标注成功。

这些场景不提供真实目标位置给运行时决策。固定高度、理想深度与真值位姿等已有实验限制仍存在。

## 录制布局

桌面左侧Isaac场景（约60%宽），右侧调试窗口（约40%）。用系统录屏或OBS捕获整个桌面/组合窗口。建议1080p、30fps；这是录制建议，不是已验证的性能配置。关闭其他Isaac实例，三组串行录制。

先打开调试窗口：

```bash
cd /home/ache/Coding/rov_navigation
bash scripts/start_semantic_debug.sh
```

录屏开始后，另一终端每次只启动一个：

```bash
python3 scripts/run_meeting_demo.py blue --policy qwen
python3 scripts/run_meeting_demo.py yellow --policy qwen
python3 scripts/run_meeting_demo.py red --policy qwen
```

使用本地.env.semantic；Qwen会真实解析指令并在运行中决策。若接口不可用，切换 `--policy rule`，必须在汇报中称为规则策略基线，不能称为LLM演示。没有自动静默回退。DeepSeek可用同名policy。当前未确认云端账户恢复情况，也未替用户启动付费调用。

默认domain137，调试窗口可一直保留；每次结束后再启动下一场。更换domain时窗口也要相同ROS_DOMAIN_ID。窗口有消息年龄提示，上一场结束后的旧数据不代表新场当前状态。

每次启动打印日志目录及可保存截图的调试窗口命令。不要同时启动多个调试窗口。界面使用最新本地扫描逻辑与默认0.25转向限幅，不启用实验加速配置。

## 每个阶段怎么讲

- WAITING/DECIDING：“根据当前视觉观测和候选动作选择下一步；Qwen时调用真实API，rule时执行规则。”指令解析在仿真启动前完成，记录于instruction.json。
- SCANNING/SCAN_ALIGN：“转动相机方向，补充观测；灰色未知区域逐渐被观察。”
- EXPLORING：“尚未可靠找到目标，选择有信息增益的安全探索点。”蓝叉为上次决策候选，紫红星为当前子目标。
- APPROACHING：“目标通过当前确认规则，生成安全停靠点，A*/EGO规划并跟踪。”OK并非真值，确认也可能误检。
- VERIFYING：“再次检查目标身份、距离、朝向、低速停留。”界面具体状态名以运行日志为准。
- RECOVERING/verification_failed：“目标丢失或验证不满足，重新观察，而不是直接宣告成功。”
- SUCCEEDED/FAILED：“报告实际最终状态。”不要只凭接近物体的画面判断成功。

右侧显示当前模式、原因、最后接受的JSON动作以及最近6条关键事件。决策候选是历史快照；EGO点云是实际发布的膨胀障碍切片，未收到显示等待。底图是语义探索安全栅格，不是Nav2 costmap。

## 运行后素材

run_meeting_demo.py在有semantic/result.json时自动生成：

- presentation/stages.md：阶段时间表。
- presentation/stages.csv：可供剪辑标注。

阶段时间为仿真秒，与视频墙钟时间不同，不能直接作为字幕时间戳。

另外将打印的目录填入：

```bash
python3 scripts/analyze_semantic_trial.py logs/实际运行目录 --output logs/实际运行目录/analysis
python3 scripts/analyze_navigation_motion.py logs/实际运行目录 --output logs/实际运行目录/analysis/motion
```

结果包括轨迹图、目标审计、速度和转向曲线；相机最新检测图在semantic/latest_detection.jpg（不是完整相机视频）。需要相机连续视频时另做录制，当前入口不自动保存摄像头视频。

建议每段保留：任务指令、一次探索决策、目标确认与接近、最终验证，共约1–2分钟素材；实际任务时间可能更长。任何加速剪辑注明倍率，保留完整原始录制及失败日志。

## 本次验证范围

三种规则配置均通过launcher --check-config；阶段导出在既有蓝管真实日志上运行通过；debug单元检查与12项状态机检查通过。没有新增完整Isaac GUI测试、真实云端测试或录像，不声称三个当前版本demo均已通过。

## 11月11日真实Qwen运行核查

用户确认API恢复。已核查用户运行的 meeting_blue_qwen_20261111_122528：真实qwen-plus，4次决策调用（不等同于4个执行动作），49.0仿真秒，1.024米，零接触，严格离线通过，最终水平表面距离0.946米。证据在validation/meeting_demo_20261111/blue_qwen，含阶段表和轨迹图。

检查时红箱仿真仍运行，但同时存在黄箱和前次红箱语义节点，需核对同域残留进程。不能将受多节点干扰的运行作为独立验证。录制每场前确保前次启动终端退出，必要时使用不同--domain，并让调试窗口使用相同ROS_DOMAIN_ID；切勿同时在同一domain运行多个语义控制器。未替用户终止正在运行的窗口。
