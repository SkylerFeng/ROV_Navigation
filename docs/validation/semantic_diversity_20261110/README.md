# 多场景 Qwen 导航验证

工作记录：../../semantic_diversity_20261110.md。

- command_eval_final.json：10 条真实 API 指令解析，5 条可执行命令的合成候选动作检查。
- command_summary.md：命令与预期行为表。
- second_batch 至 sixth_batch：保留中间失败与回归；目录名不是成功标记。
- seventh_batch：最新控制器复测；以 summary.json 和各 audit.json 为准。
- tests.txt / recovery_state_tests.txt / planner_phase_tests.txt：单元、状态机、真实 ROS 规划器回归。

图中绿色栅格表示近距离相机射线覆盖，浅蓝表示几何自由空间；并不代表每格都已正确识别物体。黄色星号属于离线评估真值，运行时未读取。

严格审核需要正确完成状态、单调仿真时间、零接触报告、合理表面距离和定位误差。接触报告可能是正间距预接触，另记录 separation 和冲量；当前仍按严格零报告筛选，不以此放宽通过条件。

所有物理测试使用 Highbay 引用场景、部件级水动力、YOLO、真实 Qwen API 与 A*/EGO 闭环。局限：理想距离传感、仿真真值位姿、固定深度、静态障碍；每项单次或少量重复不是成功率估计。未执行 DeepSeek 服务的实测。
