# 配置接口整理（2026-11-10）

## 改动

新增 config/README.md 作为调参入口，scripts/semantic_config.py 统一加载、校验和合并语义配置。现有脚本路径、USD 路径、默认任务和水动力参数保持兼容；没有整体移动源码目录或删除历史文件。

- task.json 改为可读格式；支持 --task-config 部分覆盖。
- providers.json 改为可读格式；支持 --providers-config，保留环境变量模型/地址覆盖。
- 新增 runtime.json：集中扫描、探索候选、姿态保持、完成验证、调用预算和 HTTP 参数；默认数值来自旧实现。
- 新增 profiles/short_scan.json：180°扫描的可选试验配置，默认仍为原来的近整圈扫描。
- 启动器新增 --env-file、--model、--overrides、--view、--check-config；批量对照透传相关配置。
- 每次运行写 effective_config.json 与 config 快照，语义、tracker、仿真/规划读取本次快照；manifest 保存配置及所选权重校验和，密钥不写入。
- task.max_observation_age_s 原先在若干位置被固定 2 s 替代，现在统一用于候选生成、规则策略、动作校验；默认仍为 2 s。
- depth_m 只接受当前实际支持的世界 Z=1.0 m，防止看似调参成功但规划器与控制器仍使用固定高度。
- .env.example 提供本地密钥模板；不会自动创建或覆盖用户 .env.semantic。

## 验证

单元回归见 validation/configuration_refactor_20261110/regression_tests.txt，覆盖部分覆盖继承、未知参数/错误类型/非有限值拒绝、固定高度限制、密钥不泄漏、check-config 不启动进程、动作时效一致性、tracker 参数传递及本地 Qwen/DeepSeek HTTP 合约。

真实 Isaac 基础场景使用 short_scan.json、rule、domain 142 运行：SUCCEEDED，16.4 s，路径约 0.341 m，1 次 EGO 更新，接触记录 0，离线核验通过。最终配置与 audit 保存在 validation/configuration_refactor_20261110；完整日志为 logs/config_refactor_20261110_basic。

该场景在扫描期间提前发现目标，因此此实验验证配置传递和导航兼容性，不证明 180°扫描在遮挡场景优于近整圈扫描。尚未重跑复杂场景，也未请求真实云端 API。原有重复选择受阻候选、探索任务频繁打断等行为未在本次整理中修复。

原有未提交的分析脚本修复、场景/材质和早期实验文件保留；未提交或推送 GitHub。
