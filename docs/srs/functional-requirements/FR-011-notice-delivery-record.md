## FR-011: 通知发送与接收记录

## Requirement

**ID:** FR-011  
**Title:** 通知发送与接收记录  
**Priority:** Must Have  
**Status:** Draft

### Statement

The platform shall deliver targeted notices through in-platform messaging, email and SMS channels, and record the delivery status for each notice batch. SMS delivery in this phase shall use a mock/local provider with retry and receipt tracking rather than a real carrier integration.

## Traceability

| Traces To | ID | Description |
|-----------|-----|-------------|
| Customer Need | CN-010 | 学生需要平台提供与本人画像匹配的通知与办理提醒，并及时获知 |
| Customer Problem | CP-008 | 通知触达不精准且来源分散 |

## Acceptance Criteria

- 目标学生可在平台内查看与本人相关的通知。
- 已启用的邮件与短信渠道可对相同目标范围发送通知副本。
- 管理端可查看每个通知批次的发送时间、目标范围和发送状态。
- 短信通道可通过 mock/local provider 发送、重试并记录回执；系统保留每次投递 attempt 与 receipt 状态，供管理员复核。

## Notes

- 短信渠道可由预算和部署配置控制启用，但必须纳入系统规格、批次记录与发送结果留痕设计。
- 一期实现只承诺 mock/local provider、重试、attempt 和 receipt 留痕，不承诺真实运营商接入。

---
*Created: 2026-04-13*  
*Last Updated: 2026-05-12*
*Author: Codex*
