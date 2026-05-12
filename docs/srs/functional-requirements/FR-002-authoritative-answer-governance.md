## FR-002: 权威答复治理

## Requirement

**ID:** FR-002  
**Title:** 权威答复治理  
**Priority:** Must Have  
**Status:** Draft

### Statement

The platform shall display the source name, official-source flag or official link, version, and last-updated information for each published knowledge answer and provide a manual-consultation fallback for ambiguous or sensitive cases. When multiple candidates are equally relevant, official sources shall be preferred.

## Traceability

| Traces To | ID | Description |
|-----------|-----|-------------|
| Customer Need | CN-001 | 学生需要平台提供基于官方来源的政策、资格、材料与流程说明 |
| Customer Problem | CP-010 | 官方内容缺少持续治理 |

## Acceptance Criteria

- 每条知识内容均显示来源名称或官方链接。
- 每条知识内容均显示版本或最近更新时间。
- 对标记为模糊、特殊或高风险的内容，页面提供转人工咨询入口或提示。
- 同等相关度的候选中优先展示官方来源，并可回链到对应的 `source_url`。

## Notes

- 本需求约束内容展示边界，不定义具体问答算法。

---
*Created: 2026-04-13*  
*Last Updated: 2026-05-12*
*Author: Codex*
