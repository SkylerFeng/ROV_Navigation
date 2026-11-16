# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | REGION_SEARCH |  |
| 1.8 | 决策 | scan | scan_required |
| 16.8 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 16.9 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 19.5 | 决策 | explore | search_unseen_area |
| 33.1 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 33.2 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 35.6 | 决策 | scan | scan_required_before_approach |
| 48.5 | 工具结果 | scan / SUCCEEDED | target_observed |
| 48.6 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:target_observed |
| 51.3 | 决策 | approach | target_visible |
| 65.0 | 工具结果 | approach / SUCCEEDED | visual_identity_range_heading_and_hold_verified |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
