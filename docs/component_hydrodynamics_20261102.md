# 网格部件级水动力迭代（2026-11-02）

本轮按用户要求实现按真实几何分布的水动力阻力，保留整台 ROV 为一个 PhysX 刚体。初次迭代仅保留本地；2026-11-04 用户明确授权提交到 GitHub。本次保存模型实现、编译后几何、实验覆盖配置、测试脚本、图像与验证证据。没有修改 OceanSim 源资产、既有 USD 场景或水面材质。旧版六点模型仍可通过原覆盖配置复现。

## 实际资产与部件含义

检查的资产为 /home/ache/OceanSim_assets/Bluerov/BROV_low.usd，米制、Z-up。只有一个合并 Mesh：/BlueROV/Mesh/Mesh；其下大量 Diffuse_* 子集为绘制分组，不能当作已标注的浮块、密封舱或推进器。

本轮将真实三角形顶点通过 USD 完整层级变换转换到机体原点坐标；保留网格表面，按 10 微米焊接容差识别几何连通片，以几何 ID 追溯，未捏造语义部件名称。共有 1,287,357 个源三角形、1,127 个连通片。连通片包含小螺钉、CAD 碎片及接触但未焊接的表面，不等于 1,127 个机械总成。

按连通片、4 cm 空间单元与主法向轴聚合面积加权表面中心和法线，得到 8,441 个表面采样。总网格表面积约 3.024 m²，含内部/重叠 CAD 表面，不能解释为净外部湿表面积或迎流面积。机体坐标包围范围约 X [-0.237,0.220]、Y [-0.284,0.282]、Z [-0.011,0.243] m。实时计算不再用长方体的六个虚拟点代替阻力几何。

配置 config/hydrodynamic_components/bluerov_mesh.json 保存源资产 SHA256、连通片清单、表面积、位置和法线；scripts/export_hydrodynamic_components.py 可重新提取，运行时只读取编译后的 JSON，不需要 SciPy 或 USD 网格遍历。

## 受力方法

每个采样相对质心位置 r = patch_center_body - configured_COM；机体系相对流速 u = Rᵀ(v_world-current_world) + omega_body × r。将 u 分为法向 u_n 和切向 u_t：

    F_patch = -0.5 * rho * area * wet_fraction * surface_factor
              * (Cd * abs(u_n) * u_n * normal + Cf * norm(u_t) * u_t)
    F_drag = sum(F_patch)
    torque_drag = sum(r × F_patch)

法线采用双面阻力规律，翻转法线不会改变结果，避免资产绕序引起反向推力。surface_factor=0.5 是明确公开的两侧表面配对近似，不是遮挡求解；Cd=1.0、Cf=0.01 均为未标定工程假设。聚合相邻不同法向存在近似误差，后续需要采样分辨率收敛检查和拖曳实验。

每个采样根据世界坐标水面、底面和水域边界独立计算湿润面积，水面附近采用 4 cm 线性过渡；没有把 CAD 表面积转成排水体积。阻力替换旧线性/二次集中阻力和六点阻力，不叠加旧整体阻力；新覆盖配置将额外整体转动阻尼置零，避免与表面转动阻力重复。附加质量反力仍按上一版解析模型计算。

逐步记录部件数、采样数、几何 SHA256、湿润表面积、相对流动耗散功率、总阻力矩及受力最大的八个几何连通片。全体连通片力与力矩在计算中均参与汇总，日志只限制显示前八项。

## 保留的近似与未实现项

浮力仍是预设排水体积与浮心、包围盒浸没比例；对角附加质量/惯量、刚体质量/惯量和推进合力作用线也仍采用上一版假设，未由网格辨识。推进器没有按安装位置做独立推力分配。碰撞体保留原长方体，导航几何安全界仍按既有保守船体计算。

未模拟部件遮挡、尾流、内部干燥空间、压力场、涡脱落、波浪或近壁流动，也不是 CFD。以单一 Cd 配合全部 CAD 表面可能明显高估阻力，不能把几何更细直接等同于实机更准确。当前工作是建立可追溯几何依赖与可测受力链路，下一步需要语义标注/筛除内部面，并辨识各类部件系数。

## 启用与复现

在仿真、导航和发目标的终端统一设置：

    cd /home/ache/Coding/rov_navigation
    export ROS_DOMAIN_ID=123
    export ROV_SCENARIO=platform_ego_mixed
    export ROV_EXPERIMENT_OVERRIDES="$PWD/config/experiments/hydro_components.json"

分别启动：

    bash scripts/start_sim.sh --scenario platform_ego_mixed --scene-file scenes/pool_platform_ego_mixed.usda --view perspective
    bash scripts/start_navigation.sh
    bash scripts/send_goal.sh --goal 2.1 0.0

三个命令在不同终端执行，等待仿真 ROV ready 后再启动导航、发送目标。旧 Isaac Sim 进程不会热加载此次 Python 修改，需退出后重新启动。只打开 USD 并按 Play 不会加载流体回调。

离线单元测试：

    python3 scripts/test_component_hydrodynamics.py
    python3 scripts/test_hydrodynamics.py
    python3 scripts/test_tracking_control.py
    python3 scripts/test_spline.py

重新提取资产：

    bash scripts/usd_python.sh scripts/export_hydrodynamic_components.py

物理探针（与导航测试串行运行，避免多个 Isaac Sim 占满显存）：

    /home/ache/isaac-sim/python.sh -u scripts/probe_component_hydrodynamics.py --output logs/NEW_COMPONENT_PROBE.json

导航复测：

    python3 scripts/run_suite.py --scenarios platform_ego_mixed --overrides config/experiments/hydro_components.json --output-dir logs/suites/NEW_COMPONENT_NAV --domain 123 --sim-time-limit 180 --wall-time-limit 650 --arrival-tolerance .05 --settle-time 2

## 验证记录

6 项新单元测试通过，覆盖方向/面积依赖、力臂、纯旋转阻尼、随机运动功率耗散、干燥边界、替换旧阻力而非叠加及异常法线拒绝；原有 18 项水动力、9 项跟踪和 3 项样条测试通过。

实际 PhysX 探针含水平初速 0.3 m/s 主动反推制动、撤推滑行、偏航启停和边前进边转向。制动和滑行使用中性浮力，滑行组无主动深度保持。独立探针没有渲染实际 ROV 外观，使用刚体物理和相同网格派生受力；ROV 外观与环境由后续导航测试验证。反推固定 -6 N 0.5 s 会短暂倒车，不是导航生产急停策略。

追加探针与 GUI/导航并行曾触发 GPU 显存不足；该次未完成数据不作为通过证据。保留用户原 GUI，后续改为串行测试。最终探针已在导航结束后串行重跑成功，结果如下。


## 最终实测结果

PhysX 四动作探针的 5 项检查全部通过：有限值、表面阻力耗散、制动收敛、偏航停止收敛与偏航续转。探针的速度初值仅施加一次，后续每步通过力和力矩驱动，没有姿态动画。

| 动作 | 观测结果 |
|---|---|
| 主动制动 | 最大俯仰绝对值 3.681°；最大前向位移约 3.87 cm，反推会短暂倒车 |
| 撤推滑行 | 最大前向位移约 16.91 cm；最大俯仰绝对值 3.568° |
| 原地偏航启停 | 停转指令时角速度约 0.1719 rad/s；结束相对停转时偏航净增量约 0.121° |
| 前进中转向 | 最大俯仰 2.638°、横滚 0.347°；停止转向后的偏航净增量约 0.237° |

上述偏航角是最终净增量，不是停止后最大过冲角，不能混为一谈。当前角速度控制主动制动较强，续转幅度仍然很小；没有为增强视觉效果而放大参数。

Platform Mixed 单次导航沿用相机点云 → A* → EGO → tracker，在 0.08 m/s 世界 Y 横流下到达：仿真 129.47 s，终点误差 7.79 mm，48 次规划更新，路径长 7.435 m，最大速度 0.223 m/s，最大俯仰绝对值 4.812°、横滚 1.778°，最大深度参考误差 2.237 cm。无接触事件，最大接触冲量为零，执行器力和力矩均未记录饱和。

按实际姿态计算的新增障碍保守球至包围盒净空最小约 0.398 m；扫描三角网格球净空约 0.144 m；采样船体角点均在水域内。检查间隔约 0.2 s，不构成连续扫掠安全保证。

对照上一版六点模型 Mixed 的单次 88.30 s，本次较慢，不能宣称导航效率提升；当前参数下模型阻力更强，且路径和重规划时序不同。尚未重跑三场完整套件，也未形成重复试验成功率。当前导航仍为理想深度、真值定位、固定参考高度的平面规划。

图像：

- [真实网格采样与连通片投影](figures/component_hydrodynamics_20261102/mesh_components.png)
- [方向变化时的阻力与力矩](figures/component_hydrodynamics_20261102/directional_wrench.png)
- [实际 PhysX 急停、滑行与转向](figures/component_hydrodynamics_20261102/motion_probes.png)
- [Mixed 路线、姿态与速度](figures/component_hydrodynamics_20261102/platform_ego_mixed.png)
- [汇总指标与源码校验](validation/component_hydrodynamics_20261102/summary.json)

本机原始数据位于 logs/component_hydrodynamics_20261102 与 logs/suites/platform_components_20261102。导航 manifest 包含部件几何 JSON 的副本与 SHA256，保证几何配置也能追溯；水动力核心代码与受测快照逐字节一致。默认入口未切换到新模型，用户需显式设置 hydro_components.json 并重启。

## 提交前复核（2026-11-04）

6 项部件模型、18 项原水动力、9 项跟踪控制、3 项样条测试通过，共 36 项。已核对验证汇总中的源码 SHA256 与本次代码一致，PhysX 检查全部通过且 Mixed 记录为到达；本次未重复运行 GPU 仿真。提交范围限于本轮部件水动力及其记录，活动场景、现有场景材质和先前其他未提交文件保留在本地。后续迭代仍须用户明确授权后提交。
