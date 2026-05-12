## FR-010: 通知标签与目标人群管理

## Requirement

**ID:** FR-010  
**Title:** 通知标签与目标人群管理  
**Priority:** Must Have  
**Status:** Draft

### Statement

The platform shall allow authorized operators to create notices, assign tags, define target audiences by profile attributes such as grade, major, class, role, or graduation status, and register public URL/RSS notice sources for manual fetch.

## Traceability

| Traces To | ID | Description |
|-----------|-----|-------------|
| Customer Need | CN-009 | 管理员需要平台管理带标签的通知任务与目标人群规则 |
| Customer Problem | CP-008 | 通知触达不精准且来源分散 |

## Acceptance Criteria

- 管理员可创建通知内容并选择一个或多个业务标签。
- 管理员可按画像条件筛选目标人群。
- 系统在发送前展示目标范围或人数供管理员确认。
- 管理员可新增公开 URL/RSS 形式的通知来源并手工触发抓取；抓取结果先形成草稿通知和抓取历史，不自动发布或群发。

## Notes

- 画像条件以学院实际掌握的结构化数据为准。
- 公众号通知默认手工录入；自动抓取仅限公开 URL/RSS，不绕过登录、验证码或反爬限制。

---
*Created: 2026-04-13*  
*Last Updated: 2026-05-12*
*Author: Codex*
