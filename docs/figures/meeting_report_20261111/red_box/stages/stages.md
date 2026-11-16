# 实际运行阶段记录

时间为仿真秒，不直接等同于录屏时间。保留失败与恢复，不代表所有阶段成功。

| 仿真秒 | 事件 | 动作/状态 | 原因 |
|---:|---|---|---|
| 1.9 | decision | scan | scan_required |
| 19.3 | decision | explore | search_unseen_area |
| 31.5 | decision | scan | scan_required |
| 54.3 | decision | explore | search_unseen_area |
| 84.3 | decision | approach | target_visible |
| 109.0 | verification_failed |  |  |
| 109.0 | recovery_started |  | verification_failed |
| 129.7 | decision | explore | search_unseen_area |
| 141.7 | recovery_started |  | approach_became_invalid |
| 150.9 | decision | approach | target_visible |
| 191.3 | verification_failed |  |  |
| 194.3 | decision | approach | target_visible |
| 223.9 | result | SUCCEEDED | visual_identity_range_heading_and_hold_verified |
