# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | REGION_SEARCH |  |
| 1.5 | 决策 | scan | scan_initial |
| 16.3 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 16.4 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 18.1 | 决策 | explore | transit_to_unsearched_region |
| 55.9 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 56.0 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 57.5 | 决策 | explore | search_unseen_area |
| 72.7 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 72.8 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached |
| 73.9 | 决策 | scan | scan_required |
| 95.3 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 95.4 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 96.9 | 决策 | explore | search_unseen_area |
| 122.3 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 122.5 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 123.9 | 决策 | scan | scan_required_before_explore |
| 146.7 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 146.8 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 148.5 | 决策 | explore | transit_to_unsearched_region |
| 185.7 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 185.8 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 187.5 | 决策 | explore | transit_to_unsearched_region |
| 213.3 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 213.4 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached |
| 214.9 | 决策 | explore | search_unseen_area |
| 242.7 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 243.0 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:ABORTED:target_observed_while_exploring |
| 244.9 | 决策 | approach | target_visible |
| 279.9 | 工具结果 | approach / FAILED | entry_alignment_timeout |
| 280.0 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:ABORTED:target_observed_while_exploring; approach:FAILED:entry_alignment_timeout |
| 281.7 | 决策 | approach | target_visible |
| 316.8 | 工具结果 | approach / FAILED | entry_alignment_timeout |
| 316.8 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:ABORTED:target_observed_while_exploring; approach:FAILED:entry_alignment_timeout; approach:FAILED:entry_alignment_timeout |
| 318.3 | 决策 | approach | target_visible |
| 353.3 | 工具结果 | approach / FAILED | entry_alignment_timeout |
| 353.4 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:ABORTED:target_observed_while_exploring; approach:FAILED:entry_alignment_timeout; approach:FAILED:entry_alignment_timeout; approach:FAILED:entry_alignment_timeout |
| 355.1 | 决策 | approach | target_visible |
| 390.1 | 工具结果 | approach / FAILED | entry_alignment_timeout |
| 390.2 | API 请求 | VERIFY | explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:ABORTED:target_observed_while_exploring; approach:FAILED:entry_alignment_timeout; approach:FAILED:entry_alignment_timeout; approach:FAILED:entry_alignment_timeout; approach:FAILED:entry_alignment_timeout |
| 392.1 | 决策 | approach | target_visible |
| 420.3 | 工具结果 | approach / FAILED | task_timeout |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
