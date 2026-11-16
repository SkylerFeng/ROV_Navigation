# 同帧水下处理对照

每幅图：reference 为场景渲染后、OceanSim 衰减/散射前的 LdrColor，不是空气中拍摄的真值。none 为同一帧经过 OceanSim 后的图像。

range_restore 用已知渲染参数恢复；range_preserve 在恢复后按像素同比例提亮；exposure_only 仅同比例提亮原图。提亮图的亮度不同于 reference，应结合色度/色相而非只看 RGB 误差。

检测阈值 0.45，IoU≥0.5，三个固定视角，不是完整测试集；目标颜色的掩码来自离线实例分割，不提供给运行时。

- [blue_pipe 对比图](blue_pipe/comparison.png)
- [yellow_box 对比图](yellow_box/comparison.png)
- [red_box 对比图](red_box/comparison.png)
