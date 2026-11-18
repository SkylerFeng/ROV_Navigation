# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | REGION_SEARCH |  |
| 1.7 | 决策 | scan | scan_required_before_search |
| 16.6 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 16.6 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 18.3 | 决策 | explore | transit_to_unsearched_region |
| 59.9 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 60.0 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 61.5 | 决策 | explore | search_unseen_area |
| 136.5 | 工具结果 | explore / TIMEOUT | action_timeout |
| 136.6 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:TIMEOUT:action_timeout |
| 138.3 | 决策 | explore | search_unseen_area |
| 172.2 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 172.3 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:TIMEOUT:action_timeout; explore:SUCCEEDED:exploration_waypoint_reached |
| 174.1 | 决策 | scan | scan_required |
| 182.9 | 工具结果 | scan / SUCCEEDED | target_observed |
| 183.0 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:TIMEOUT:action_timeout; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:target_observed |
| 184.9 | 决策 | approach | target_visible |
| 197.9 | 工具结果 | approach / SUCCEEDED | visual_identity_range_heading_and_hold_verified |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
