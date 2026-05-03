## NFR-002: 审计留存与可追溯性

## Requirement

**ID:** NFR-002  
**Title:** 审计留存与可追溯性  
**Category:** Reliability  
**Priority:** Must Have  
**Status:** Draft

### Statement

The platform shall retain searchable administrator and approval audit records for at least one academic semester and preserve the sequence of critical actions without silent loss. Records exceeding the retention window shall be periodically purged or cold-archived into a history store (例如通过定时冷数据迁移脚本) to prevent unbounded growth of the primary log table.

## Traceability

| Traces To | ID | Description |
|-----------|-----|-------------|
| Customer Need | CN-007 | 需要平台管理驳回、撤回、重提、重批与留痕规则 |
| Applies To FRs | FR-008, FR-012, FR-013, FR-016, FR-017, FR-018 | 流转规则、权限、日志、统计、荣誉与画像 |

## Measurement Criteria

- **Target:** 关键操作日志保留不少于 1 学期且支持查询
- **Minimum Acceptable:** 关键审批与导出动作无不可解释的日志缺失
- **Measurement Method:** 日志抽样审计、保留期配置检查、恢复与查询演练

## Acceptance Criteria

- [ ] 学期内的关键审批、配置和导出操作均可被查询。
- [ ] 日志查询结果包含事件先后顺序所需信息。
- [ ] 日志保留策略不会在约定周期内提前清除关键记录。
- [ ] 架构设计上提供定时任务（例如定期冷数据迁移脚本），将超出保留期的日志从高频查询表迁移至历史库，保证生产主表不无限膨胀。

## Implementation Notes

<!-- Engineers add notes here during implementation -->

---
*Created: 2026-04-13*  
*Last Updated: 2026-04-17*
