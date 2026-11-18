# 被主动中止的诊断轮

原始日志：`logs/stability_20261117/v2/west_baffles`。0.1 m 语义格可生成挡板后方的目标，但 ROV 实测起点进入保守方形膨胀带后，EGO 持续 GEN_NEW_TRAJ/零速保持，高层连续发送其他远目标仍无解。

为开展起点恢复修复，主动中止语义进程。semantic/result.json 的原因是 interrupted。Isaac 未正常输出 sim/run.json，无法完成标准离线碰撞审核；不计为成功，不伪造补齐物理结果。
