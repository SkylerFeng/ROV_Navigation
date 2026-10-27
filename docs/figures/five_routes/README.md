> 这是旧轮次（150秒墙钟预算）的历史图。最新复测见 [2026-10-14 路线图](../recheck_20261014/README.md)。

# 五种场景实测路线图

与参考图使用相同的绿色实际轨迹、红色障碍、绿色起点、蓝色目标样式。

五张图统一使用 ros_clock_suite 的同一轮多场景测试记录；基准图误差因此与早期参考图的 0.004 m 不同。
未做轨迹平滑或延伸到目标。未到达案例保留真实终止位置，并标出橙色 X。
所有图使用相同坐标范围与 XY 等比例，便于比较。圆形表示立柱，矩形表示箱体/墙段。

PNG 为 3840×2160，可直接用于 PPT；SVG/PDF 为矢量版本。

| 场景 | 最终误差(m) | 本轮达到0.3m阈值 | 图片 |
|---|---:|---|---|
| baseline | 0.2099 | 是 | [PNG](route_baseline.png) · [SVG](route_baseline.svg) · [PDF](route_baseline.pdf) |
| slalom | 0.5192 | 否 | [PNG](route_slalom.png) · [SVG](route_slalom.svg) · [PDF](route_slalom.pdf) |
| gates | 2.0291 | 否 | [PNG](route_gates.png) · [SVG](route_gates.svg) · [PDF](route_gates.pdf) |
| pillars | 0.2995 | 是 | [PNG](route_pillars.png) · [SVG](route_pillars.svg) · [PDF](route_pillars.pdf) |
| mixed | 0.2998 | 是 | [PNG](route_mixed.png) · [SVG](route_mixed.svg) · [PDF](route_mixed.pdf) |

[五场景汇总图](five_routes_overview.png)

数据来源见 sources.json。本轮为理想深度、真值位姿、固定高度实验，各场景一组起终点；不代表统计成功率。
