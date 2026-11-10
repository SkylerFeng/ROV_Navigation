# Platform 水中导航与避障 demo

沿用 Platform_black_water.usda 原场景及其水面、碰撞体。加入一根半径 0.35 米的静态橙色障碍柱，挡在起终点连线上。A* 使用原扫描碰撞三角形、水域边界与新增障碍生成固定深度的栅格路径，分辨率 0.15 米，ROV 保守球半径 0.40 米；规划检测另留半格对角线余量。路径跟踪沿用速度 PI 和浮力、阻力、推进响应滞后、0.06 m/s 横流。

## 操作

```bash
cd /home/ache/Coding/rov_navigation
/home/ache/isaac-sim/python.sh scripts/run_platform_water_demo.py
```

自动开始，默认运行 75 秒仿真时间后退出。浅蓝线为规划路线，橙线为实测轨迹在水面上的投影，绿球标记起终点。`--waypoint-only` 可以运行上一版无新增障碍的航点 demo。

## 实测

运行 75.03 秒，航程 4.694 米，成功绕柱并到达终点，最终误差 0.000022 米（理想仿真稳态值，不代表实机精度）。最大深度偏差 0.0188 米，全程浸没，无 CONTACT_FOUND/PERSIST 碰撞事件。相对新增柱体的水平保守船体间距最小 0.191 米；每 0.25 秒抽样的原扫描三角形保守球间距最小 0.150 米，抽样检查不构成连续碰撞证明。

[A* 绕行录像](validation/platform_navigation_20261028/demo.gif) · [轨迹与速度](validation/platform_navigation_20261028/result.png) · [指标](validation/platform_navigation_20261028/metrics.json) · [几何审计](validation/platform_navigation_20261028/audit.json) · [完整实测数据](validation/platform_navigation_20261028/motion.json)

此版使用已知静态地图规划，未连接相机感知、动态障碍或 EGO 在线重规划。逐栅格点跟踪使速度存在起伏，后续可通过安全走廊内路径平滑和前视跟踪改善。规划范围为世界 X [2,8]、Y [0,3.45] 米，Z 固定 -0.30 米；范围外目标需要扩展栅格边界。

复现验证：

```bash
/home/ache/isaac-sim/python.sh scripts/run_platform_water_demo.py --headless --output-dir logs/platform_navigation_final
bash scripts/usd_python.sh scripts/audit_platform_navigation.py logs/platform_navigation_final
python3 scripts/package_platform_demo.py
```
