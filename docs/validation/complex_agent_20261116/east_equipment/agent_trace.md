# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | REGION_SEARCH |  |
| 1.8 | 决策 | scan | scan_required |
| 16.7 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 16.8 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 18.7 | 决策 | explore | search_unseen_area |
| 39.0 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 39.1 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 40.7 | 决策 | scan | scan_required |
| 60.7 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 60.8 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 63.3 | 决策 | explore | search_unseen_area |
| 104.8 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 104.9 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 107.7 | 决策 | scan | scan_uncompleted |
| 129.2 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 129.3 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 132.5 | 决策 | explore | search_unseen_area |
| 164.3 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 166.4 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:ABORTED:target_observed_while_exploring |
| 169.9 | 决策 | explore | search_unseen_area |
| 173.9 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 176.0 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring |
| 179.5 | 决策 | explore | search_unseen_area |
| 183.5 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 185.6 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring |
| 188.9 | 决策 | explore | search_unseen_area |
| 192.9 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 195.0 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring |
| 198.5 | 决策 | explore | search_unseen_area |
| 202.5 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 204.7 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring |
| 208.3 | 决策 | explore | search_unseen_area |
| 212.3 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 214.4 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring |
| 217.9 | 决策 | explore | search_unseen_area |
| 221.9 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 224.0 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring |
| 227.5 | 决策 | explore | search_unseen_area |
| 231.9 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 234.0 | API 请求 | VERIFY | explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring |
| 237.5 | 决策 | explore | search_unseen_area |
| 241.5 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 243.6 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring |
| 247.0 | 决策 | explore | search_unseen_area |
| 251.0 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 253.1 | API 请求 | VERIFY | explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring |
| 256.6 | 决策 | explore | search_unseen_area |
| 260.6 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 262.6 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring |
| 266.2 | 决策 | explore | search_unseen_area |
| 270.2 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 272.4 | API 请求 | VERIFY | explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring |
| 276.1 | 决策 | explore | search_unseen_area |
| 280.1 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 282.3 | API 请求 | VERIFY | explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring |
| 286.0 | 决策 | explore | search_unseen_area |
| 288.0 | 工具结果 | explore / FAILED | sensor_stale_replan |
| 288.1 | API 请求 | VERIFY | explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:FAILED:sensor_stale_replan |
| 291.5 | 决策 | scan | scan_required |
| 293.9 | 工具结果 | scan / SUCCEEDED | target_observed |
| 294.0 | API 请求 | VERIFY | explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:ABORTED:target_observed_while_exploring; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:target_observed |
| 297.5 | 决策 | approach | target_visible |
| 308.3 | 工具结果 | approach / SUCCEEDED | visual_identity_range_heading_and_hold_verified |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
