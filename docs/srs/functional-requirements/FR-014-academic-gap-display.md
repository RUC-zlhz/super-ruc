## FR-014: 学业缺口展示

## Requirement

**ID:** FR-014  
**Title:** 学业缺口展示  
**Priority:** Must Have  
**Status:** Draft

### Statement

The platform shall display unmet curriculum modules, related risk hints, and course-type recommendation hints for a student based on uploaded transcript data, maintained training-plan rules and available term course data without asserting final graduation eligibility.

## Traceability

| Traces To | ID | Description |
|-----------|-----|-------------|
| Customer Need | CN-012 | 学生需要平台提供学业完成缺口与风险提示，并仅基于可核验的数据做展示 |
| Customer Problem | CP-009 | 学业风险识别滞后且误导成本高 |

## Acceptance Criteria

- [ ] 学生上传或导入成绩数据后可查看未满足的培养方案模块。
- [ ] 页面明确标识结果为风险提示而非毕业结论。
- [ ] 若规则或数据不足，系统提示需要人工核验。
- [ ] 当学期开课信息可用时，页面可展示课程类型级建议，但不得展示动态选课人数或毕业结论。

## Notes

- 该需求必须纳入一期规格与交付范围，但仍需坚持“弱结论、强边界”的业务原则。

---
*Created: 2026-04-13*  
*Last Updated: 2026-04-13*  
*Author: Codex*
