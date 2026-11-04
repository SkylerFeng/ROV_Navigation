# 各阶段最终运行结果索引

清理日期：2026-11-02。清理时仅修改本地运行产物；其记录随本轮水动力迭代按用户后续明确授权纳入提交。

按每个已记录开发阶段保留最终完整批次，以及最终版本的不同条件对照；不以文件夹包含 final 或是否成功作为唯一标准。历史版本最终批次中的失败仍按失败保留，不把不同版本拼成成功批次。

| 开发阶段 | 保留的最终结果 | 说明 |
|---|---|---|
| 早期 ROS 仿真时钟接入 | logs/scenario_tests/ros_clock_suite；gates_suite | 最初五场图像对应的原始结果及早期门洞对照 |
| 原场景系统复查 | logs/scenario_tests/recheck_20261014_diagnostic | 完整复查批次，包含当时未通过场景 |
| 停滞与几何问题诊断 | logs/diagnostics/freeze_20261014 | 保留最终复验、地图审计及诊断证据；删除早期 fix/heading 调试运行 |
| 五场景重新测试 | logs/suites/five_scenarios_20261014_rerun | 该阶段最终五场批次，包含 slalom 失败 |
| 执行进度与全局引导修正 | logs/suites/five_scenarios_20261015_guide_fix | 五场最终结果；窗口复验在 logs/diagnostics/slalom_phase_20261014/final_gui_validation |
| 转向与终端接近修正 | logs/suites/five_scenarios_20261015_turn_fix | 保留 delay100、delay55_terminal_gui 及 final_validation.json，另保留 gates_promoted_20261015 |
| 初版水动力 | logs/suites/hydro_iteration2_20261027 | 最终五场；静水、斜流、旧模型对照分别在 hydro_still、hydro_oblique、hydro_legacy_check_20261027 |
| HighBay 实景导航 | logs/highbay_v5；highbay_v5_current016；highbay_v5_slalom | 最终默认流、强流和原场景回归，保留 highbay_audit |
| 整洁水池方案 | logs/clean_pool_iteration3 | 最新完整结果；早期两轮数值仍在历史报告，但原始运行目录已删除 |
| Platform 水中航点 demo | logs/platform_water_demo_follow | 对应 docs/validation/platform_water_demo_20261028 的最终录像与实测数据 |
| Platform 静态地图 A* demo | logs/platform_navigation_final | 对应 docs/validation/platform_navigation_20261028 的最终录像与实测数据 |
| Platform 接入 EGO | logs/platform_ego_trial；platform_ego_obstacle_trial | 无新增障碍与单障碍两种最终验证 |
| Platform 三场景首批结果 | logs/suites/platform_three_hydro_20261028_final | 本阶段最终批次包含 Mixed 失败，支撑修正前后比较 |
| Mixed 布局修正后三场复验 | logs/suites/platform_three_hydro_20261028_verified | 三场最终完整复验，删除 mixed_retry/rerun 等中间批次 |
| 姿态耦合水动力（待用户验收） | logs/suites/platform_coupled_20261102 | 保留三场全部原始数据、源码快照与日志 |
| 姿态耦合对照 | logs/suites/platform_centered_20261102；platform_coupled_current016_20261102 | 保留集中力基线与强流结果 |
| 最终 PhysX 姿态探针 | logs/hydro_coupled_20261102/physx_probe_review.json | 保留完整探针及对应 log、审计、测试日志和修改前备份 |

## 清理范围

删除已被最终批次替代的零散 logs/runs、HighBay v1–v4、中间水动力试跑、早期 Platform demo、重复探针文件、临时 last_cloud/last_camera 数组和旧启动日志。logs/archives 中的历史配置备份保留。

旧 demo 的逐帧 PNG 已精简为首帧、中间帧和末帧。最终 GIF、轨迹图和完整 motion.json 均保留；若要重新制作完整录像，需要重新运行。docs/figures 中六份逐字节重复的 ZIP 已删除，文档链接改为展开目录的 README；存在独有内容的旧 five_routes ZIP 保留。

历史 Markdown、已发表轨迹图和精简验证证据保留。历史报告中的已清理目录名用于说明原始来源，不代表文件仍然存在。部分中间结果已无法从原始日志重绘；不修改历史数字，不把中间失败改写为最终成功。

[本轮最新水动力报告](hydrodynamics_coupled_20261102.md) · [三场景最终复验](platform_three_hydro_navigation_20261028_verified.md) · [逐文件删除清单与 SHA256](validation/results_cleanup_20261102.json)

## 最新部件水动力迭代

[网格部件级水动力](component_hydrodynamics_20261102.md)：最终 Mixed 运行 logs/suites/platform_components_20261102，最终四动作探针 logs/component_hydrodynamics_20261102/physx_probe_final.json；2026-11-04 按用户明确授权纳入提交。
