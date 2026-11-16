# 实际运行阶段记录

时间为仿真秒，不直接等同于录屏时间。保留失败与恢复，不代表所有阶段成功。

| 仿真秒 | 事件 | 动作/状态 | 原因 |
|---:|---|---|---|
| 1.7 | decision | scan | scan_required |
| 19.1 | decision | explore | search_unseen_area |
| 31.2 | recovery_started |  | approach_became_invalid |
| 39.9 | decision | approach | target_visible |
| 49.3 | result | SUCCEEDED | visual_identity_range_heading_and_hold_verified |
