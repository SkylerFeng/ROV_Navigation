# Debug相机与YOLO同帧显示（2026-11-11）

新增三栏窗口：左侧语义安全地图/实际轨迹/规划路径，中间相机原图与YOLO检测框，右侧任务、状态、接受的决策和阶段记录。

导航节点保留最后一次推理的RGB和完整检测结果，通过已有debug话题以2Hz发送JPEG和同帧检测元数据。只有有订阅者时编码；不另启YOLO推理，不改变控制策略，也不调用额外API。原图指同一推理输入帧，经JPEG压缩用于显示，不是无损传输或独立高帧率相机流。

框标注类别和YOLO置信度。颜色与距离来自后续颜色/深度定位模块，不是YOLO直接预测；距离沿用range_m含义，不等同于离线水平表面距离。绿色框表示定位模块返回结果，橙色表示仅检测、未获得定位结果；绿色不表示已通过多帧确认、目标一定正确或最终任务成功。无检测时仍显示图像和0 detections。图像和框在同一消息中传输，不会将旧框绘到新帧。

标题显示源图仿真时刻和相对地图快照的延迟；过期时标STALE。编码/解码失败给出状态，旧图不套新框。关闭调试窗口不影响导航。新增图像源需要重新启动导航进程，不能只重启viewer。

```bash
# 先正常退出旧仿真，再启动一场；不要同时启动多场
python3 scripts/run_meeting_demo.py blue --policy qwen --domain 153
# 第二终端
ROS_DOMAIN_ID=153 bash scripts/start_semantic_debug.sh --save logs/debug_camera_last.png
```

验证：4项debug/相机测试和12项状态机测试通过；640×360合成图JSON消息经真实ROS传输解码通过。使用既有蓝管运行的传感器帧进行离线YOLO重推理并绘制三栏预览，已检查布局与中文显示。预览不是新的实时GUI仿真，其底图仅使用记录的free/occupied层，没有重建安全余量与域外层。验证目录：validation/semantic_debug_camera_20261111。尚未跑新增完整Isaac GUI联调。未提交GitHub。
