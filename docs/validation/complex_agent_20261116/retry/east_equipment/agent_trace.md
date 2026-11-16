# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | REGION_SEARCH |  |
| 1.7 | 决策 | scan | scan_required |
| 16.6 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 16.7 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 18.5 | 决策 | explore | search_unseen_area |
| 38.7 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 38.8 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 40.3 | 决策 | scan | scan_required |
| 60.3 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 60.4 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 62.7 | 决策 | explore | search_unseen_area |
| 104.1 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 104.2 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 106.7 | 决策 | scan | scan_required |
| 128.0 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 128.1 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 131.1 | 决策 | explore | search_unseen_area |
| 165.1 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 167.1 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:ABORTED:target_observed_while_exploring |
| 170.3 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:ABORTED:target_observed_while_exploring |
| 173.5 | 决策 | approach | target_visible |
| 193.0 | 工具结果 | approach / SUCCEEDED | visual_identity_range_heading_and_hold_verified |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
