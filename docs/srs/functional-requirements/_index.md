# Functional Requirements Index

**Version:** 1.1 | **Created:** 2026-04-13 | **Last Updated:** 2026-05-12

## Summary

- Total FRs: 18
- Must Have: 18
- Should Have: 0
- Covered CNs: 15 / 15
- Covered CPs: 12 / 12

## FR Catalog

| ID | Title | Priority | Traces to CN | Traces to CP | File |
|----|-------|----------|--------------|--------------|------|
| FR-001 | 政策与流程查询 | Must Have | CN-001 | CP-002 | `FR-001-policy-query.md` |
| FR-002 | 权威答复治理 | Must Have | CN-001 | CP-010 | `FR-002-authoritative-answer-governance.md` |
| FR-003 | 知识与模板维护 | Must Have | CN-002 | CP-010 | `FR-003-knowledge-template-maintenance.md` |
| FR-004 | 党团进度查看 | Must Have | CN-003 | CP-003 | `FR-004-party-youth-progress-view.md` |
| FR-005 | 党团提醒管理 | Must Have | CN-004 | CP-003 | `FR-005-party-youth-reminder-management.md` |
| FR-006 | 常见事务在线提交 | Must Have | CN-005 | CP-005 | `FR-006-common-request-submission.md` |
| FR-007 | 申请审核工作台 | Must Have | CN-006 | CP-005 | `FR-007-application-review-workbench.md` |
| FR-008 | 驳回撤回与重提规则 | Must Have | CN-007 | CP-005 | `FR-008-resubmit-withdraw-rules.md` |
| FR-009 | 文件导入导出 | Must Have | CN-008 | CP-006 | `FR-009-file-import-export.md` |
| FR-010 | 通知标签与目标人群管理 | Must Have | CN-009 | CP-008 | `FR-010-notice-targeting.md` |
| FR-011 | 通知发送与接收记录 | Must Have | CN-010 | CP-008 | `FR-011-notice-delivery-record.md` |
| FR-012 | 角色与字段级权限控制 | Must Have | CN-011 | CP-007 | `FR-012-role-and-field-permissions.md` |
| FR-013 | 审计日志跟踪 | Must Have | CN-011 | CP-004 | `FR-013-audit-log-tracking.md` |
| FR-014 | 学业缺口展示 | Must Have | CN-012 | CP-009 | `FR-014-academic-gap-display.md` |
| FR-015 | 培养方案规则维护 | Must Have | CN-008 | CP-006 | `FR-015-curriculum-rule-maintenance.md` |
| FR-016 | 学院运营统计看板 | Must Have | CN-013 | CP-004 | `FR-016-operational-dashboard.md` |
| FR-017 | 奖励荣誉公示与榜样展示 | Must Have | CN-014 | CP-011 | `FR-017-honor-display.md` |
| FR-018 | 学生画像聚合与全景视图 | Must Have | CN-015 | CP-012 | `FR-018-student-profile.md` |

## CN Coverage Check

| Customer Need | Covered by FRs | Status |
|---------------|----------------|--------|
| CN-001 | FR-001, FR-002 | Covered |
| CN-002 | FR-003 | Covered |
| CN-003 | FR-004 | Covered |
| CN-004 | FR-005 | Covered |
| CN-005 | FR-006 | Covered |
| CN-006 | FR-007 | Covered |
| CN-007 | FR-008 | Covered |
| CN-008 | FR-009, FR-015 | Covered |
| CN-009 | FR-010 | Covered |
| CN-010 | FR-011 | Covered |
| CN-011 | FR-012, FR-013 | Covered |
| CN-012 | FR-014 | Covered |
| CN-013 | FR-016 | Covered |
| CN-014 | FR-017 | Covered |
| CN-015 | FR-018 | Covered |

## Notes

- `FR-014` 与 `FR-015` 虽然依赖结构化培养方案与规则数据质量，但仍属于一期正式需求范围，需要通过真实数据或甲方确认的样例数据完成交付。
- 全部 FR 共同组成一期正式范围；其中“知识、流程、审批、通知、审计”五个闭环是技术拆解主线，而非范围删减。
- `S12/S13` 增量不新增 FR ID，而是把默认导入、候选批次、受控抓取、进度中心、结构化官方来源优先和 SMS/mock 兜底等边界吸收到现有 FR-002 / FR-003 / FR-004 / FR-007 / FR-009 / FR-010 / FR-011 / FR-014 / FR-015 的验收条目中。
