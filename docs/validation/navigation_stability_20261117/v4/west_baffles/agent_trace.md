# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | REGION_SEARCH |  |
| 1.5 | 决策 | scan | scan_required_before_search |
| 16.3 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 16.4 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 18.5 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 20.3 | 决策 | explore | search_unseen_area |
| 32.7 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 32.8 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 34.1 | 决策 | scan | scan_required_before_identify |
| 49.5 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 49.6 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 51.1 | 决策 | explore | search_unseen_area |
| 126.1 | 工具结果 | explore / TIMEOUT | action_timeout |
| 126.2 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout |
| 127.7 | 决策 | explore | search_unseen_area |
| 149.3 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 149.4 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:SUCCEEDED:exploration_waypoint_reached |
| 150.7 | 决策 | scan | scan_required_before_approach |
| 168.9 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 169.0 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 170.7 | 决策 | explore | search_unseen_area |
| 245.7 | 工具结果 | explore / TIMEOUT | action_timeout |
| 245.8 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout |
| 247.5 | 决策 | explore | search_unseen_area |
| 321.1 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 321.5 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:ABORTED:target_observed_while_exploring |
| 323.3 | 决策 | approach | target_visible |
| 343.8 | 工具结果 | approach / FAILED | local_recovery_started |
| 360.2 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:ABORTED:target_observed_while_exploring; approach:FAILED:local_recovery_started |
| 361.9 | 决策 | explore | search_unseen_area |
| 371.9 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 372.3 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:ABORTED:target_observed_while_exploring; approach:FAILED:local_recovery_started; explore:ABORTED:target_observed_while_exploring |
| 385.3 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:ABORTED:target_observed_while_exploring; approach:FAILED:local_recovery_started; explore:ABORTED:target_observed_while_exploring |
| 387.1 | 决策 | explore | search_unseen_area |
| 420.3 | 工具结果 | explore / FAILED | task_timeout |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
