# HighBay 运行图（2026-10-28）

- `iteration_comparison.png/.pdf`：失败版本与最终版本的原始位置采样。两版同起点、目标和矩形水域；带箱图另画双倍横流路线。
- `open_route.png`、`obstacles_route.png`、`current016_route.png`：实际绿色路线、青色末次规划、橙色旧规划、灰色原扫描碰撞切片、蓝色虚线配置水域。切片只表示相应高度，不是池底全貌。
- `obstacles_dynamics.png`、`current016_dynamics.png`：实际/目标速度，实际/目标推进力，浮力/重量，目标误差；无平滑。
- `highbay_viewport_*.png`：Isaac 实际运行截图，平面为人为配置水面，扫描碎片和孔洞保留。轨迹线为视口叠加，不进入相机测距。

数据在 `../../validation/highbay_20261028/`；受测核心源码 SHA256 见核验报告。最终三项 HighBay 测试均采用 5 cm 内保持 2 s 的判据，不与历史 1 cm 成绩等同。
