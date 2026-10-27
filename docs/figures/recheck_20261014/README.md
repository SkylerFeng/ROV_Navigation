# 五种场景实测路线图

与参考图使用相同的绿色实际轨迹、红色障碍、绿色起点、蓝色目标样式。

数据批次：logs/scenario_tests/recheck_20261014_diagnostic。到达阈值 0.01 m，连续保持 2 秒。
未做轨迹平滑或延伸到目标。未到达案例保留真实终止位置，并标出橙色 X。
所有图使用相同坐标范围与 XY 等比例，便于比较。圆形表示立柱，矩形表示箱体/墙段。
灰色细线表示原水池碰撞网格在 ROV 船体高度范围内的截面；与新增红色障碍一并显示。

PNG 为 3840×2160，可直接用于 PPT；SVG/PDF 为矢量版本。

| 场景 | 最终误差(m) | 本轮完成到达判定 | 图片 |
|---|---:|---|---|
| baseline | 0.0036 | 是 | [PNG](route_baseline.png) · [SVG](route_baseline.svg) · [PDF](route_baseline.pdf) |
| slalom | 4.1096 | 否 | [PNG](route_slalom.png) · [SVG](route_slalom.svg) · [PDF](route_slalom.pdf) |
| gates | 2.0291 | 否 | [PNG](route_gates.png) · [SVG](route_gates.svg) · [PDF](route_gates.pdf) |
| pillars | 0.0033 | 是 | [PNG](route_pillars.png) · [SVG](route_pillars.svg) · [PDF](route_pillars.pdf) |
| mixed | 0.0025 | 是 | [PNG](route_mixed.png) · [SVG](route_mixed.svg) · [PDF](route_mixed.pdf) |

[五场景汇总图](five_routes_overview.png)

数据来源见 sources.json。本轮为理想深度、真值位姿、固定高度实验，各场景一组起终点；不代表统计成功率。

复测条件、gates历史成功对照和失败分析见[完整记录](../../navigation_recheck_20261014.md)。本轮主图使用原场景，显露碰撞网格及密集点云的诊断结果没有混入。
