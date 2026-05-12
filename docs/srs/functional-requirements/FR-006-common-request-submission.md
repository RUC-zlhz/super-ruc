## FR-006: 常见事务在线提交

## Requirement

**ID:** FR-006  
**Title:** 常见事务在线提交  
**Priority:** Must Have  
**Status:** Draft

### Statement

The platform shall allow students to create and submit common affairs requests, including leave, stamping, proof, registration, and material submission, with required form fields and optional or mandatory attachments by request type. For stamping scenarios, a file to be stamped is required; for proof scenarios, students may upload an attachment or provide a textual justification. If the approver determines during initial review that the matter involves sensitive or classified content, they may mark the request "转线下办理" (handle offline); the system shall then halt online document generation, preserve the approval history in the audit log, and push a system notice to the student containing follow-up guidance and the responsible teacher's contact. Proof requests shall only support the current built-in PDF preview path, not a separate standard-template binding engine in this phase.

## Traceability

| Traces To | ID | Description |
|-----------|-----|-------------|
| Customer Need | CN-005 | 学生需要平台创建常见事务申请并附带所需信息或附件 |
| Customer Problem | CP-005 | 常见事项仍依赖碎片化线下审批 |

## Acceptance Criteria

- 学生可选择至少一种常见事务类型并填写对应表单。
- 系统可按事务类型要求上传附件或填写文字说明。
- 提交成功后系统生成唯一申请记录供后续跟踪。
- 审批老师勾选"转线下办理"时，系统终止线上文件生成，保留审批历史，并向学生推送包含后续指导与老师联系方式的系统提示。

## Notes

- 是否具有校级正式效力由业务类型决定，本需求仅覆盖学院平台受理能力。

---
*Created: 2026-04-13*  
*Last Updated: 2026-05-12*
*Author: Codex*
