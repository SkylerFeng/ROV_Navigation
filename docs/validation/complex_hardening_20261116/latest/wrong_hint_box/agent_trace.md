# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | REGION_SEARCH |  |
| 1.9 | 决策 | scan | scan_required |
| 16.9 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 17.0 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 18.9 | 决策 | explore | search_unseen_area |
| 40.2 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 40.3 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 41.9 | 决策 | scan | scan_required |
| 64.6 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 64.7 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 66.8 | 决策 | explore | search_unseen_area |
| 96.9 | 工具结果 | explore / FAILED | no_progress_choose_another_viewpoint |
| 97.0 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint |
| 99.0 | 决策 | explore | search_unseen_area |
| 128.7 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 128.8 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached |
| 131.1 | 决策 | scan | scan_required_before_explore |
| 151.7 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 151.8 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 154.3 | 决策 | explore | search_unseen_area |
| 187.3 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 187.4 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 189.7 | 决策 | scan | scan_required_before_explore |
| 212.3 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 212.4 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 214.9 | 决策 | explore | transit_to_unsearched_region |
| 247.5 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 247.6 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 250.3 | 决策 | explore | transit_to_unsearched_region |
| 271.9 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 272.0 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached |
| 274.5 | 决策 | explore | transit_to_unsearched_region |
| 294.7 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 294.8 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached |
| 297.3 | 决策 | explore | transit_to_unsearched_region |
| 309.9 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 310.0 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached |
| 312.3 | 决策 | scan | scan_required_before_explore |
| 328.5 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 328.6 | API 请求 | ALTERNATIVE_SEARCH | explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 331.1 | 决策 | explore | search_unseen_area |
| 363.7 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 363.8 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 365.9 | 决策 | scan | scan_uncompleted |
| 376.7 | 工具结果 | scan / SUCCEEDED | target_observed |
| 376.8 | API 请求 | VERIFY | explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:target_observed |
| 379.3 | 决策 | explore | search_unseen_area |
| 410.4 | 工具结果 | explore / FAILED | no_progress_choose_another_viewpoint |
| 411.5 | API 请求 | VERIFY | explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:target_observed; explore:FAILED:no_progress_choose_another_viewpoint |
| 413.9 | 决策 | explore | search_unseen_area |
| 421.4 | 工具结果 | explore / FAILED | task_timeout |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
