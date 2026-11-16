# 水下图像偏黄修正：2026-11-16 第二次迭代

## 本次结论

旧灰世界白平衡将整个画面视为平均中性，会错误补偿蓝色水体、蓝色物体和场景照明。其后的 CLAHE/融合继承该偏色。本次不把旧方法输出当作恢复成功，而是补充同帧参考，采用距离恢复和保色提亮，并将处理预览与识别输入分离。

直接看三张前后图：

- [蓝管：原图 / 旧白平衡 / 新预览](validation/vision_color_fix_20261116/paired/blue_pipe/before_after.png)
- [黄箱：原图 / 旧白平衡 / 新预览](validation/vision_color_fix_20261116/paired/yellow_box/before_after.png)
- [红箱：原图 / 旧白平衡 / 新预览](validation/vision_color_fix_20261116/paired/red_box/before_after.png)
- [八种输入及参考图](validation/vision_color_fix_20261116/paired/README.md)

## 同帧参考如何获得

`scripts/capture_vision_reference.py` 在三个既有场景中，使用历史末次相机的世界位姿和内参重新渲染。静态采集关闭 ROV 的刚体运动，固定随体照明，预热 60 帧，再同时读取同一渲染缓冲区的：

1. `reference`：OceanSim UW_render 之前的 LdrColor；
2. `rgb`：该图经 OceanSim 衰减、散射后的输出；
3. 逐像素射线距离、可见实例掩码和实际水体参数。

参考仍包含场景的材质、水面和照明，是**光学后处理之前的参考图**，不是空气中拍摄的真值。重新渲染也不保证与历史曝光一模一样。参考图、目标真值和掩码只用于离线审核，没有进入导航或 LLM。原始成对数据在 `logs/vision_color_fix_20261116/static_pairs/`，导出的图、参数和 SHA256 在 docs 验证目录。

## 实现变化

### 1. range_preserve：恢复与提亮分开

先使用既有独立直接衰减/后向散射模型恢复；恢复阶段仍使用当前已知 OceanSim 系数，并限制逆增益。然后从像素最大通道计算亮度增益，对 R/G/B 三个通道同时乘相同系数，避免红通道单独拉高。默认 `preview_gamma=0.8`、`preview_max_gain=2.0`，并联合限制饱和，减少逐通道截断产生的偏色。

保留无效/过远距离处原始像素，不用猜测的距离做颜色逆变换。恢复不能重建原本没有曝光出来的细节；参考图中本来就很暗的背景仍可能很暗。

### 2. neutral_balance：白平衡只接受明确的中性区域标定

不再以“全图平均颜色”作为推荐的校正依据。新增固定 `neutral_gain_rgb` 接口，默认 `[1,1,1]`，未标定时不改变颜色。

`scripts/calibrate_neutral_card.py` 接受人工指定的真实灰卡掩码，排除过暗/截断像素；要求至少 64 个有效像素，增益默认限制在 `[1/1.25,1.25]`，超出时拒绝而非继续过补偿。脚本不能自动证明掩码中的物体是灰卡；本次场景没有已标定灰卡，因此没有伪造白平衡参数。

```bash
python3 scripts/calibrate_neutral_card.py \
  --image /path/to/underwater_gray_card.png \
  --mask /path/to/gray_card_mask.png \
  --output config/semantic/vision_profiles/my_neutral_card.json
```

### 3. 处理预览与识别输入分离

`vision.detector_source` 可选 `raw / processed`。为兼容上次实验，默认值为 processed，但默认 method 仍为 none；新的 `range_preserve.json` 推荐配置明确指定：

```json
{
  "method": "range_preserve",
  "detector_source": "raw",
  "color_source": "raw"
}
```

该配置下 YOLO 和颜色定位使用几何对齐后的原始图像，处理结果用于预览与保存。`latest_sensor.npz` 的 `rgb` 始终为实际检测输入，`processed_rgb` 为处理图，`raw_rgb` 为原始曝光，`rectified_raw_rgb` 为几何对齐后的原图；另保存 `latest_processed.jpg`。

Debug 上方显示处理预览，下方显示真正识别输入及其检测框，并标注 detector_source。两幅图严格校验时间戳。旧白平衡、CLAHE、融合保留作对照分支，不默认推荐。

## 量化结果

固定三个视角，使用参考图中亮度足够、饱和度足够的目标像素，计算与参考的 HSV 圆周色相差。蓝管 4,960 像素、黄箱 24,666 像素、红箱 45,108 像素符合条件。

| 目标 | 原图误差 | 旧白平衡误差 | 新恢复＋保色提亮误差 |
|---|---:|---:|---:|
| 蓝管 | 2.92° | 13.04° | 0.30° |
| 黄箱 | 2.70° | 25.54° | 0.43° |
| 红箱 | 7.46° | 1.45° | 0.05° |

在有效距离像素中，未经额外提亮的 range_restore 对参考图的 RGB 平均绝对误差分别为 0.48、0.71、0.89（0–255）。提亮后的亮度有意不同于参考，因此应同时查看色相/色度指标，不能仅凭亮度误差判定颜色是否更准确。

这项恢复使用已知渲染系数与理想距离；既不是完整 Sea-thru，也不证明未知真实水质下能得到同样结果。

### 为什么识别仍保留原图

同一 YOLO、置信度 0.45、IoU≥0.5，与离线可见实例框匹配：原水下图三个目标都检出；处理后的蓝管和黄箱检出，红箱漏检。红箱甚至在参考图中也漏检，表明冻结检测器的输入分布适配仍是问题。不能用画面恢复更准确来推断识别一定提升。

因此推荐配置分离显示与识别。三幅图只是小规模诊断，不构成整体召回率评估；颜色掩码评估也不等于完整运行时定位评估。

## 实际 Qwen 导航验证

- [推荐配置的导航轨迹](validation/vision_color_fix_20261116/qwen_blue_safe_preview/trajectory.png)：真实 Qwen 蓝管任务，29.6 s，航程 0.951 m，无接触报告，离线审核通过，最终水平表面距离 0.995 m。
- [实际处理预览](validation/vision_color_fix_20261116/qwen_blue_safe_preview/last_processed_preview.png)
- [实际检测输入与检测结果](validation/vision_color_fix_20261116/qwen_blue_safe_preview/latest_detection.jpg)
- 已逐数组核对：保存的检测输入等于几何对齐原图，processed_rgb 与检测输入不同。
- 另一次将处理图直接输入检测器的蓝管试验也成功，但固定视角红箱漏检说明它不能作为全场景默认配置。保留在 `qwen_blue_processed_ablation`。

两次为 headless 实际渲染和真实 Qwen API；未做多种水质重复统计。107 项测试通过，涵盖通道比例、显式灰卡校验、无效深度、识别/预览路由、预览时戳和既有 Agent/导航测试。GUI 双画面的时戳与解码路径通过离线单元测试，尚未另做人工 GUI 验收。

## 如何运行

```bash
cd /home/ache/Coding/rov_navigation
python3 scripts/run_semantic_trial.py --gui --policy qwen --env-file .env.semantic \
  --instruction '不要黄色管子，请靠近蓝色管子，距它表面保持一米。' \
  --scene-file scenes/pool_platform_semantic_blue_search.usda \
  --vision-config config/semantic/vision_profiles/range_preserve.json \
  --domain 176 --output "logs/color_safe_demo_$(date +%Y%m%d_%H%M%S)"
```

另一个终端用同一个 ROS domain 启动调试界面：

```bash
ROS_DOMAIN_ID=176 bash scripts/start_semantic_debug.sh
```

场景的第三人称视窗仍显示原场景，视觉前端的改动体现在相机处理预览，不会更改水面材质或全局场景颜色。

本次没有修改水动力和导航参数，也没有提交 GitHub。
