# red_box

请找到红色箱子，在距离它表面八十厘米的位置停住。

状态：SUCCEEDED；严格离线通过：False
原因：visual_identity_range_heading_and_hold_verified；接触物体对数：1（非接触次数）

- trajectory.png：实测轨迹（目标真值仅离线标注）。
- last_camera_rgb.png：最后保存的相机原图。
- latest_detection.jpg：与快照对应的原始检测叠加图。
- stages/stages.md：实际执行的决策/恢复事件。
- semantic/events.jsonl：包含API请求、返回、拒绝与执行的完整记录。
- motion/motion.png：速度和转向曲线。

快照不是保证成功的一帧，也不保证为仿真结束的最后曝光帧；失败状态应一并展示。缺失文件表示该次未生成。
