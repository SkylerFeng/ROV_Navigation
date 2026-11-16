# 最新蓝管真实Qwen工作流程核查

运行：logs/meeting_blue_qwen_20261111_124352，domain153，policy=qwen。instruction.json确认蓝色pipe和1.0米任务；events.jsonl记录4次qwen-plus动作返回，其中17.3s动作被刷新后的候选校验拒绝；3次执行动作。另有启动前的指令解析调用，不包含在result.llm_calls=4中。任务耗时62.6仿真秒，运行时SUCCEEDED；本次未新增独立几何/碰撞审核。

| 仿真时刻 | Qwen输出或系统事件 | 执行/原因证据 |
|---|---|---|
| 启动前 | 解析自然语言 | 接受blue/pipe/1.0m |
| 1.7 | scan / scan_required | 实际执行；初始未发现目标，需观察 |
| 17.3 | approach obj_004 / target_visible | 未执行；invalid candidate，本地进入恢复 |
| 17.3–33.6 | 本地恢复 | 根据记忆朝向重新观察，超时；不是新增Qwen指令 |
| 38.1 | explore frontier_34_28 / search_unseen_area | 实际执行；旧蓝管观测已过期约23.7s，去探索点(-2.625,-0.525,1) |
| 51.9 | approach obj_007 / target_visible | 实际执行；新蓝管观测新鲜约0.47s，已有可达停靠候选 |
| 54.8–62.9 | 本地验证 | 期间可见性/速度不连续满足要求，最终通过身份/距离/朝向/低速保持检查 |

模型接受结构化物体列表、目标类别颜色、确认/新鲜度、候选ID、可达性、路径长度、信息增益评分、上次动作结果和允许动作集。模型不接收原始图片、真实目标坐标或完整地图；位置等字段由semantic_llm剔除，模型选择ID。YOLO负责类别，颜色模型和深度/相机位姿负责颜色与空间估计；本地生成候选和评分；A*/EGO规划路径，跟踪器与水动力负责实际运动。

SYSTEM提示明确规定优先可接近目标、否则未完成扫描先扫描、否则优先最高分探索点。因此这是受限的LLM高层动作选择，不是自由自主规划，也不能凭本轮证明优于规则基线。模型短reason_code是日志中实际返回的理由；更详细解释为根据输入/程序约束所作的可核查解释，不是内部思维链。

Task文字正常存在，默认Matplotlib DejaVu Sans不支持中文；viewer新增本机CJK字体选择和缺失文本提示。字形覆盖和实际图片渲染测试通过，图见validation/qwen_stages_20261111/task_font.png。仅需重启调试窗口，ROS_DOMAIN_ID仍设153。没有修改导航逻辑、没有新API调用、没有提交。
