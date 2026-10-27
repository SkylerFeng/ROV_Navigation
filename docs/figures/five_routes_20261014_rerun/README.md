# 五种场景实测路线图

与参考图使用相同的绿色实际轨迹、红色障碍、绿色起点、蓝色目标样式。

本轮门洞采用 gates_clearance：Gate2North 下端由 y=1.3 m 提高至 1.8 m，保留 0.5 m XY 障碍膨胀。该结果不代表原 gates 布局通过。

数据批次：logs/suites/five_scenarios_20261014_rerun。到达阈值 0.01 m，连续保持 2 秒。
本批目标坐标：[3.5, 0.4, 1.0] m。
未做轨迹平滑或延伸到目标。未到达案例保留真实终止位置，并标出橙色 X。
所有图使用相同坐标范围与 XY 等比例，便于比较。圆形表示立柱，矩形表示箱体/墙段。
灰色细线表示原水池碰撞网格在 ROV 船体高度范围内的截面；与新增红色障碍一并显示。

PNG 为 3840×2160，可直接用于 PPT；SVG/PDF 为矢量版本。

| 场景 | 最终误差(m) | 本轮完成到达判定 | 图片 |
|---|---:|---|---|
| baseline | 0.0064 | 是 | [PNG](route_baseline.png) · [SVG](route_baseline.svg) · [PDF](route_baseline.pdf) |
| slalom | 6.4045 | 否 | [PNG](route_slalom.png) · [SVG](route_slalom.svg) · [PDF](route_slalom.pdf) |
| gates_clearance | 0.0022 | 是 | [PNG](route_gates_clearance.png) · [SVG](route_gates_clearance.svg) · [PDF](route_gates_clearance.pdf) |
| pillars | 0.0059 | 是 | [PNG](route_pillars.png) · [SVG](route_pillars.svg) · [PDF](route_pillars.pdf) |
| mixed | 0.0040 | 是 | [PNG](route_mixed.png) · [SVG](route_mixed.svg) · [PDF](route_mixed.pdf) |

[五场景汇总图](five_routes_overview.png)

数据来源见 sources.json。本轮为理想深度、真值位姿、固定高度实验，各场景一组起终点；不代表统计成功率。
