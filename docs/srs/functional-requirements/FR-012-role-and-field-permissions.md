## FR-012: 角色与字段级权限控制

## Requirement

**ID:** FR-012  
**Title:** 角色与字段级权限控制  
**Priority:** Must Have  
**Status:** Draft

### Statement

The platform shall enforce role-based access and field-level visibility rules for student data, business records, and export actions according to authorized scope.

## Traceability

| Traces To | ID | Description |
|-----------|-----|-------------|
| Customer Need | CN-011 | 班主任、辅导员和超级管理员需要平台控制敏感字段可见性、导出权限与访问审计 |
| Customer Problem | CP-007 | 敏感学生信息存在越权风险 |

## Acceptance Criteria

- [ ] 不同角色登录后只能看到其授权范围内的页面与数据。
- [ ] 敏感字段可按角色显示为隐藏、脱敏或完整可见。
- [ ] 未授权角色无法执行学院级数据导出操作。

## Notes

- 具体字段矩阵由学院后续确认，本需求先固化能力边界。

---
*Created: 2026-04-13*  
*Last Updated: 2026-04-13*  
*Author: Codex*
