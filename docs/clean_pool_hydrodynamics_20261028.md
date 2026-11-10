# 整洁池形场景与水动力嵌入（2026-10-28）

新增独立场景 `clean_pool`，不切换原有 active scenario，不修改 OceanSim 源资产。

## 场景来源与坐标

水面引用 `/home/ache/OceanSim-Highbay/data/Platform(new1)/Tile3_water.usda`。
其 19 点边界同时生成静态池壁和规划/水动力水域。池底复用水面三角网格的 XY 顶点，避免另画矩形水体。
池沿外轮廓按相邻边交点连接，消除第一轮独立墙段的接缝。

这是沿现成水域多边形构造的工程水池，不是真实扫描池壁的重建。未加载 Platform 或 HighBay 的扫描网格，池边没有扫描碎片、屋顶和悬空模型。保留一块训练障碍、起终点与轨迹叠加。

源水面由脚本按 Z 高度生成；本场景显式将其数值定义为米制 Z-up，并仅平移 `[-5.8,-4.65,1.35]`。
没有依据源 Stage 的默认 Y-up/厘米元数据自动旋转缩放，也不据此声称扫描几何已标定。
世界水域约 X=[-7.45,7.45], Y=[-3.10,3.10]，水面 Z=1.55，池底 Z=0.70，水深 0.85 米。
静态审计比较 USD 水域元数据、变换后水面顶点、物理边界与池底高度。

## 水动力

复用已有 `Hydrodynamics`，以 60 Hz 物理回调施加力和力矩：

- PhysX 重力与密度×排水体积×重力的浮力，近似浸没比例和浮心恢复力矩。
- 相对水流速度下的线性/二次平移阻力及转动阻力。
- 有限推进力与力矩；一阶响应时间常数 0.25/0.12 秒。
- 默认 Y 方向横流 0.08 m/s，5 kg、0.00505 m³ 排水体积（约 1% 正浮力）。

关闭 PhysX 内置阻尼，避免重复计算阻力。控制器通过积分抵消稳定横流和浮力偏差。
水面没有碰撞；池壁、池底和训练障碍具有碰撞。
上述参数属于工程假设，尚非辨识后的真实 ROV 参数；不含 CFD、波浪、附加质量或推进器尾流。

## 启动

一条命令自动启动 Isaac Sim 窗口、规划器并发送目标（到达后保存结果并退出）：

```bash
cd /home/ache/Coding/rov_navigation
python3 scripts/run_suite.py --scenarios clean_pool --gui --domain 99 \
  --arrival-tolerance .05 --settle-time 2 --goal-delay 5
```

需要持续查看而不自动结束时，分别打开三个终端：

```bash
# 终端1
cd /home/ache/Coding/rov_navigation
ROV_SCENARIO=clean_pool ROS_DOMAIN_ID=99 bash scripts/start_navigation.sh
```

```bash
# 终端2
cd /home/ache/Coding/rov_navigation
ROS_DOMAIN_ID=99 bash scripts/start_sim.sh --scenario clean_pool
```

```bash
# 终端3，等待终端2出现 ROV ready
cd /home/ache/Coding/rov_navigation
ROV_SCENARIO=clean_pool ROS_DOMAIN_ID=99 bash scripts/send_goal.sh
```

仅 File > Open `scenes/pool_clean_pool.usda` 可检查几何，不会加载 Python 水动力回调。
新场景运行器启用 RTX fractional cutout opacity，使水下机器人透过水面可见；直接在编辑器打开时，可在 Render Settings 中启用 Fractional Cutout Opacity。

## 复现与验证

```bash
bash scripts/usd_python.sh scripts/build_scene.py --scenario clean_pool --no-select
bash scripts/usd_python.sh scripts/export_pool_geometry.py --scenario clean_pool
bash scripts/usd_python.sh scripts/validate_clean_pool.py
python3 scripts/test_hydrodynamics.py
/home/ache/isaac-sim/python.sh scripts/test_hydrodynamics_isaac.py --output logs/clean_pool_physx_probes.json
```

静态审计为机器人材质提供 Isaac Sim 的 MDL 搜索路径，以免将运行时内置的 OmniPBR.mdl 误报为文件缺失。
13 项本地单元测试和 9 项独立 PhysX 探针通过。探针检查中性/正浮力、横流漂移、抗流控制、浮心姿态恢复、出水自由落体及推进滞后，探针自身不使用新池体。

前两轮实际池内导航：

| 版本 | 仿真到达时间 | 最终误差 | 接触冲量报告 | 障碍保守采样净空 |
|---|---:|---:|---:|---:|
| 第一轮（独立墙段） | 48.33 s | 1.74 mm | 无 | 0.372 m |
| 第二轮（连续池沿、调整水色） | 49.03 s | 1.37 mm | 无 | 0.343 m |

到达判据为距离 5 cm 内连续保持 2 s，最终误差是停止时数值；不能解释为所有时刻均达到毫米精度。
测试采用理想深度，RGB 使用 OceanSim 水下渲染。净空是离散轨迹与包围球估计，不能替代连续碰撞保证。
