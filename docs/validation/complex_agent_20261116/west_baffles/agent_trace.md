# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | REGION_SEARCH |  |
| 1.7 | 决策 | scan | initial_scan |
| 16.7 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 16.8 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 19.9 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 22.1 | 决策 | explore | search_unseen_area |
| 32.1 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 32.2 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 34.1 | 决策 | scan | scan_required |
| 54.2 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 54.3 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 56.5 | 决策 | explore | search_unseen_area |
| 84.6 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 84.7 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 86.7 | 决策 | scan | scan_required |
| 87.8 | 工具结果 | scan / SUCCEEDED | target_observed |
| 87.9 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:target_observed |
| 90.5 | 决策 | approach | target_visible |
| 100.4 | 工具结果 | approach / SUCCEEDED | visual_identity_range_heading_and_hold_verified |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
