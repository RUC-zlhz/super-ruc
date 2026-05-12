## FR-009: 文件导入导出

## Requirement

**ID:** FR-009  
**Title:** 文件导入导出  
**Priority:** Must Have  
**Status:** Draft

### Statement

The platform shall allow authorized administrators to import and export student master data, templates, notices, and business records using supported Excel, Word, and PDF files with validation feedback. On import failures the system shall atomically roll back the batch (zero pollution of production tables) and return a downloadable error report (either a dedicated report file or the original Excel appended with an "错误原因" column) that pinpoints each failure to the row and field level. Transcript PDF handling shall stop at candidate parsing plus teacher verification before formal grade records are written.

## Traceability

| Traces To | ID | Description |
|-----------|-----|-------------|
| Customer Need | CN-008 | 数据管理员需要平台创建和更新学生主数据、模板文件与业务台账，并通过文件交换保持一致 |
| Customer Problem | CP-006 | 无法依赖校级接口导致数据交换效率低 |

## Acceptance Criteria

- 授权管理员可导入结构化数据文件并获得成功、失败或警告结果。
- 授权管理员可导出申请记录、台账或统计结果到受支持文件格式。
- 导入失败时系统指出至少到记录级或字段级的问题原因。
- 失败批次触发整批回滚（主库零污染），并提供可下载的行级错误报告（错误原因列精确到行号与字段），使管理员无需人工逐行比对即可修改重提。
- 授权管理员可从仓库登记的默认学生花名册与默认培养方案源执行一键导入；默认学生导入只写核心字段，不从学号或预计毕业年份推断专业、年级、班级。
- 学生上传成绩单 PDF 后仅生成待人工核验批次；教师核验提交后才写入正式成绩记录。

## Notes

- 学生角色默认不具备学院级数据导出权限。
- 默认学生与默认培养方案导入只消费仓库登记数据源，不从学号或预计毕业年份推断专业、年级、班级。

---
*Created: 2026-04-13*  
*Last Updated: 2026-05-12*
*Author: Codex*
