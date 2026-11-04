# 语义导航版本归档（2026-11-05）

用户授权将本次语义导航版本提交到 GitHub，便于回溯。本版包含独立 Highbay 语义场景、YOLO 检测与颜色识别、同步距离图定位、规则探索与接近、Qwen/DeepSeek JSON 适配、水面反光和观察位置修复、凭据文件启动修复，以及报告图表和来源记录。保留已有 A* + EGO 与部件级水动力。

## 验证边界

- 提交前单元回归 57 项通过，记录：validation/semantic_release_20261105/regression_tests.txt。
- 反光修复前，basic/screened/relocated 各有一次成功的规则闭环实验，另保留 occluded 失败压力案例。
- 反光修复后，基础场景单次闭环成功；screened 做了渲染检查，未重跑全部复杂场景。
- 报告配图来自反光修复前同一次 screened 实验，来源和校验和见 figures/semantic_report_20261105/sources.json。
- 云端接口通过本地 stub 测试，未完成真实 DeepSeek/Qwen 对照；单次实验不是成功率。

## 权重与运行

logs 通常被忽略，但本次明确将下列两个最终模型文件纳入 Git，以保持默认启动路径可回溯。不保存 last.pt、训练缓存或密钥。

| 文件 | SHA-256 |
| --- | --- |
| logs/semantic_detector_lit/train/weights/best.onnx | ce2bf48cf6a87c8eedc3f6ca50ba51fcf54e46d59fdb7354c5246508812b9cbb |
| logs/semantic_detector_lit/train/weights/best.pt | ac12e83817979d8a3a6f0472d3b64ad422c9c9944ce60cb7af74186ac585cb24 |
| config/semantic/color_model.npz | 4b134946defea7c06bed36382f904d68f269219af367d12d57567eba06f19769 |

在已配置 Isaac Sim、ROS Humble、OceanSim/Highbay 和语义依赖的本机，执行：

```bash
cd /home/ache/Coding/rov_navigation
run_dir="$PWD/logs/semantic_demo_$(date +%Y%m%d_%H%M%S)"
python3 scripts/run_semantic_trial.py --gui --policy rule \
  --scene-file scenes/pool_platform_semantic_screened.usda \
  --output "$run_dir"
```

外部 Isaac Sim/OceanSim 安装、大型扫描资产、ROS 构建产物和完整训练数据不随此提交打包；场景引用仍包含本机绝对路径，换机器需配置相应环境。报告 PNG/PDF/CSV 和实验摘要保存在 docs，完整原始日志留在本机。

## 提交范围

本提交只保存本次语义导航及显示/报告修改。工作区原先的 active_scenario、旧 highbay/pool 场景、mixed 材质调整、clean_pool/platform_demo 实验文件保持原状，不混入此版；语义场景已独立保存反光参数，不依赖 mixed 的未提交修改。此前文档中的“等待提交”描述是当时的历史状态，以本归档记录为准。
