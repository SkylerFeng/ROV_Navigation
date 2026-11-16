# 实时地图与决策调试窗口

新增只读 ROS 调试窗口，独立于 Isaac 窗口。无 API 调用，不发布控制指令，不读场景真实目标坐标。新增代码未提交 GitHub。

## 启动

先重新启动一次 run_semantic_trial.py（旧进程没有新增 debug 发布器）。保持仿真运行，第二个终端：

```bash
cd /home/ache/Coding/rov_navigation
bash scripts/start_semantic_debug.sh --save logs/semantic_debug_last.png
```

默认 ROS_DOMAIN_ID=137，与 trial 默认一致。如果试验用了 `--domain 147`，则使用 `ROS_DOMAIN_ID=147 bash scripts/start_semantic_debug.sh`。关闭调试窗口不会停止仿真。save 在正常退出时保存最后一帧。

## 图层与语义

左侧不是 Nav2 costmap：当前系统未使用 Nav2。底图为语义探索节点自己的占据/安全栅格：灰色未知、深色水域外、浅色已观测安全空闲、橙色已观测空闲但安全余量不足、红色已观测占据。safe() 使用当前语义地图的实际判定。底图数组按 [x,y] 存储，显示时转置，坐标为 world 米。

紫色为自动发现 `*/occupancy_inflate` PointCloud2 后订阅的实际 EGO 膨胀点云，在 ROV 当前高度上下0.06米切片；没有收到就明确显示 waiting，不伪造 EGO 地图。若有多个同域规划器，可能发现首个匹配话题，应避免同域多次仿真。上下平面可能落在切片中，需根据实际高度解释。

绿色为真实轨迹；青色为最新收到的 EGO 路径（停止后可能仍显示旧路径，以 Plan age 与状态为准）；紫红星号为当前 active 子目标。蓝叉是**最后一次决策时**的候选点，不代表每帧重新计算。黑圈为视觉估计目标位置，OK仅代表跟踪器的多帧确认，仍可能误检。右侧显示任务、策略、状态、原因、规划和跟踪状态、最后接受的 JSON 决策、接收时间与地图/路径数据年龄。未显示API内部推理过程。

## 更新与开销

semantic_navigation 以2Hz发布 `/rov/semantic/debug`，只有订阅者存在才序列化地图。只读取已存在的候选/决策记录，不调用会改变状态的 observation()；实际轨迹截取最近2000个采样。窗口2Hz重绘，EGO切片显示最多约6000个点。大地图和桌面渲染仍有额外CPU成本，可随时关闭。

## 验证与限制

14项地图/配置/扫描单元检查、12项状态机检查通过；ROS消息通道使用合成载荷验证成功；使用已记录的真实导航数据通过离线渲染检查（validation/semantic_debug_20261110/offline_preview.png）。离线预览没有重建安全膨胀层与域外层，也没有实时EGO点云，不能作为实时界面完整截图。当前未重新启动Isaac进行端到端GUI验证。已确认本机Tk、matplotlib与sensor_msgs_py可导入。
