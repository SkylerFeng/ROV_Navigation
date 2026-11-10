# Platform 原场景水动力 demo

> 结果清理说明（2026-11-02）：本页涉及的部分中间迭代原始文件已删除；历史测量与诊断文字保留，各阶段最终结果见[保留结果索引](results_index.md)。缺失的中间文件不能再用于重绘。

直接引用 `/home/ache/OceanSim-Highbay/data/Platform(new1)/Platform_black_water.usda`，保留原扫描、水面与碰撞体和变换，不改动源资产。wrapper 显式采用米、Z-up；将原场景水域 metadata 通过根变换转换到世界坐标。水面透明度仅在 wrapper 中调为 0.10，以便观察 ROV。

运行：

```bash
cd /home/ache/Coding/rov_navigation
/home/ache/isaac-sim/python.sh scripts/run_platform_water_demo.py
```

脚本自动开始，默认运行 42 秒仿真时间并退出。不要仅打开 USD 并按 Play：Python 中的水动力回调才提供流体作用力。

模型：PhysX 重力和刚体碰撞，Python 每物理步更新浮力、相对流速线性/二次阻力、恢复力矩、推进器 0.25 秒响应滞后；横流为世界 Y 方向 0.06 m/s。参数为演示设定，非实测辨识或 CFD。控制为预设航点位置控制与速度 PI，不代表 EGO 自主导航验证。

最终跟随视角实测 32.03 秒，航程 5.015 米，完成航点，终点误差 0.0176 米，最大深度偏差 0.0196 米，全程浸没比例 1.0。数据中有 reset 后 t=0.033 秒的 CONTACT_LOST（type=1），没有新增 CONTACT_FOUND/PERSIST 记录；原始事件保留在 motion.json，后续脚本过滤 lost 事件。

可播放动画：[demo.gif](validation/platform_water_demo_20261028/demo.gif)。轨迹图：[result.png](validation/platform_water_demo_20261028/result.png)。完整数据：[motion.json](validation/platform_water_demo_20261028/motion.json)。橙线是实际 XY 轨迹在水面上的投影标注，绿球为航点。

headless 复现：

```bash
/home/ache/isaac-sim/python.sh scripts/run_platform_water_demo.py --headless --duration 32 --output-dir logs/platform_water_demo_reproduce
```
