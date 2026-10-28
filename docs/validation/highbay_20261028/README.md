# HighBay 验证数据（2026-10-28）

`stage_audit.json` 核对真实 HighBay 引用、原始碰撞三角网格、配置水面与资产 SHA256。
`failed_iterations.json` 和 `failed_paths.json` 保留出生点穿模、自由终点过冲、角点越界等失败，不能只根据到达字段判断通过。
`local_checks.json` 与两份回归日志记录本机检查。

最终试验的子目录保存未修改的 `run.json`、`controls.json`、`metrics.json`、`manifest.json`、`scene_evidence.json`；HighBay 试验另附 `geometry_audit.json`。位置/姿态/水动力数据均来自采样，约每 0.2 s 一次，不是插值或虚构轨迹。`manifest.json` 中的 Git 提交是试验前基线，实际受测代码由源码快照 SHA256 标识；最终核心源码匹配另见 `verification.json`。

`run.json` 内含当时完整实验配置与采样。可直接用仓库 `scripts/hydrodynamics_metrics.py` 的 `dynamics_metrics(run, controls)` 重新计算水动力指标；几何审计需要外部 USD 原始资产，完整核验还需要本机 logs 中的源码快照和 PhysX 日志。此目录不打包外部资产、编译产物、完整大日志或重复的源码快照。

已知水域是手动配置的测试范围，原始 HighBay 扫描不含水；本轮使用简化水动力、理想深度与真值定位，不能据此声称真实水下导航已验证。

交付前仅删除了 `pool_highbay.usda` 和 `pool_highbay_open.usda` 的末尾空行；归档 manifest 和静态审计保留试验时的原始文件 SHA256，场景内容和物理参数未变。
