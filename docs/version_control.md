# 项目版本管理

本仓库管理导航源码、ROS2 规划器 overlay、实验配置、场景描述、文档与已有汇报图片。
实验日志 `logs/`、ROS 编译/安装产物和 Python 缓存保留在本机，不纳入 Git。
Git 中的场景描述仍引用外部资产，不代表资产已经随仓库分发。

## 初始基线

`baseline-navigation-20261027` 标签保存引入新水动力模型之前的导航工程。
文档中的五场景成绩属于已有实验，本次归档没有重新运行仿真。
后续水动力迭代使用独立分支，保留原执行方式作为对照。

## 外部依赖

- Isaac Sim：当前默认 `/home/ache/isaac-sim`；仿真脚本支持 `ISAAC_SIM_PATH`。
- OceanSim 相机：`/home/ache/isaac-sim/extsUser/OceanSim`。
- 水池和水面：`/home/ache/Platform1013/Platform`。
- BlueROV：`/home/ache/OceanSim_assets/Bluerov/BROV_low.usd`。
- ROS2 Humble：`/opt/ros/humble`。
- EGO underlay：`/home/ache/Coding/ego/ego-planner-swarm`。
  来源提交及 overlay 说明见 `ros_ws/README.md`，保留其 GPL 许可证。
- `/home/ache/OceanSim-Highbay` 是候选仿真能力来源，当前未作为整个工程直接加载。

以上依赖包含本机绝对路径；更换机器后需配置并重新生成场景、编译 overlay。
已有实验日志及源码快照应另行备份，文档内指向未提交日志的链接在远端不可用。

## 日常迭代

```bash
git status
git diff
git add <本次修改的文件>
git commit -m "Describe the change and its purpose"
git push
```

每次实验应记录代码提交号、完整配置、场景来源、仿真时间和评估指标。
大体积原始数据与资产宜使用独立存储，记录其位置与校验值。

## 水动力迭代顺序

1. 保存当前模型为可选基准，新增可配置的机体系阻力与执行器一阶响应。
2. 显式处理重力与浮力，避免同时启用中性浮力近似和重复浮力补偿。
3. 使用相对水流速度计算阻力，加入可复现的定常水流实验。
4. 验证耗散性、响应时间常数、静水浮力平衡和水流坐标变换。
5. 先验证保持与转向，再运行五场回归；报告轨迹误差、接触、到达与饱和情况。

新增参数属于待标定的简化模型，完成测试后再决定是否设为默认。
