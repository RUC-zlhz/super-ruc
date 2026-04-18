## FR-013: 审计日志跟踪

## Requirement

**ID:** FR-013  
**Title:** 审计日志跟踪  
**Priority:** Must Have  
**Status:** Draft

### Statement

The platform shall record administrator operations, approval actions, content changes, and export events with actor, time, object, and action details.

## Traceability

| Traces To | ID | Description |
|-----------|-----|-------------|
| Customer Need | CN-011 | 班主任、辅导员和超级管理员需要平台控制敏感字段可见性、导出权限与访问审计 |
| Customer Problem | CP-004 | 学院缺少客观留痕与工作记录 |

## Acceptance Criteria

- [ ] 审批、配置变更、内容发布停用和导出动作均被记录。
- [ ] 每条日志至少包含操作者、操作时间、操作对象和操作类型。
- [ ] 授权管理员可按时间、对象或人员查询日志记录。

## Notes

- 审计日志是平台级横切能力，不仅服务审批场景。

---
*Created: 2026-04-13*  
*Last Updated: 2026-04-13*  
*Author: Codex*
