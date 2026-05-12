## FR-003: 知识与模板维护

## Requirement

**ID:** FR-003  
**Title:** 知识与模板维护  
**Priority:** Must Have  
**Status:** Draft

### Statement

The platform shall allow authorized administrators to create, update, publish, deactivate, and version knowledge entries, source records, and template files.

## Traceability

| Traces To | ID | Description |
|-----------|-----|-------------|
| Customer Need | CN-002 | 管理员需要平台创建和更新知识条目、模板文件与来源版本 |
| Customer Problem | CP-010 | 官方内容缺少持续治理 |

## Acceptance Criteria

- 授权管理员可新增、编辑和停用知识条目。
- 授权管理员可上传模板文件并维护名称、分类和适用场景。
- 每次发布或停用都保留版本标识和操作者记录。
- 已发布知识条目关联的模板可在学生侧下载或在知识详情中回链到官方来源，未发布或已停用模板不得对学生侧开放。

## Notes

- “谁上传谁维护”作为运营默认规则，由角色权限约束配合实现。

---
*Created: 2026-04-13*  
*Last Updated: 2026-05-12*
*Author: Codex*
