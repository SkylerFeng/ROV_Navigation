# 语义场景水面显示修复（2026-11-05）

语义场景继承了基础场景的弱反光材质，没有继承 mixed 的反光覆盖。本次仅在语义场景层恢复 opacity=0.38、roughness=0.12、ior=1.333、specularColor=(1,1,1)，并设置 useSpecularWorkflow=0。四个语义场景均已核对合成参数；生成脚本同步更新。外部 Highbay 资产和水动力参数未修改。

实测旧默认 perspective 位置被扫描场景遮挡。语义配置增加 overview_eye=[-2,-2.8,2.6]、overview_target=[-2,0,1.3]；启动与 Perspective 按钮使用相同配置，其他场景保留默认位置。

验证：screened 场景在 Isaac Sim 中实际渲染 150 步，最终截图可见反射与高光。基础场景规则导航单次 SUCCEEDED，任务时间 15.6 s，路径 0.342 m，EGO 更新 1 次，接触记录 0，离线核验通过。语义与接口测试 21 项通过。此次未重跑复杂场景完整导航，也未测试云端决策；不据单次结果推断成功率。

最终证据：validation/semantic_water_visual_20261105/perspective.png 与 basic_audit.json。完整输出：logs/semantic_water_visual_20261105/。

关闭旧实例后，使用原 run_semantic_trial.py --gui --policy rule 启动命令即可加载修改；旧窗口不会自动刷新材质。未提交或推送 GitHub。
