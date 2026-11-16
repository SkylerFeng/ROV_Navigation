# 组会材料：三条真实Qwen指令

本批为真实Qwen API + YOLO + A*/EGO + 部件水动力，headless实际渲染相机；无规则回退。每任务一次，不是成功率统计。

| 任务 | 指令 | 结果 | 严格审核 | 仿真秒 | 航程m |
|---|---|---|---|---:|---:|
| [blue_pipe](blue_pipe/README.md) | 不要黄色管子，请靠近蓝色管子，距它表面保持一米。 | SUCCEEDED | True | 29.5 | 0.95 |
| [yellow_box](yellow_box/README.md) | 靠近黄色方块，不要找管子。 | SUCCEEDED | True | 64.5 | 2.19 |
| [red_box](red_box/README.md) | 请找到红色箱子，在距离它表面八十厘米的位置停住。 | SUCCEEDED | False | 223.6 | 3.89 |

直接用于PPT：[三页汇报PDF](report_slides.pdf)。每个任务目录的 report_slide.png 为对应单页图片；stages/stages.md 为决策时间线。

统计口径：时间为仿真时间；decision_calls 是运行中决策调用，不包含启动时的指令解析。停靠距离为 ROV 参考位置到目标水平表面的距离，检测图标注为相机测距，两者不等价。定位使用仿真深度和真值位姿，尚未验证真实传感器误差。

录屏版与本次headless运行调度条件不同，不能据此保证GUI复现结果。默认膨胀0.25m，不使用实验转向加速。相机为最后保存的快照，见各任务camera_metadata.json；不隐去失败、碰撞或定位偏差。
