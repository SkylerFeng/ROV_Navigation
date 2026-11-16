# 偏黄修正实验材料

- [方法、测试结果与启动命令](../../vision_color_preservation_20261116.md)
- [蓝管前后对比](paired/blue_pipe/before_after.png)
- [黄箱前后对比](paired/yellow_box/before_after.png)
- [红箱前后对比](paired/red_box/before_after.png)
- [包含同帧参考的完整对照](paired/README.md)
- [全部离线量化数据](paired/metrics.json)
- [实际导航审核](qwen_blue_safe_preview/audit.json)
- [实际导航路径](qwen_blue_safe_preview/trajectory.png)
- [实际相机处理预览](qwen_blue_safe_preview/last_processed_preview.png)
- [实际原图检测结果](qwen_blue_safe_preview/latest_detection.jpg)
- [107 项测试](tests.txt)

已知水体参数、三个固定视角的颜色验证；不是未知真实水质验证。推荐配置保留原图识别，仅将恢复画面用于预览。原始成对数据保存在 logs，来源校验见 paired/sources.json。
