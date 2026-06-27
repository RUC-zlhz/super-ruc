# 第 14 组后续权限与导出深测细化

- 主计划关联：`S29.18`
- 状态：`[x]` 已完成
- 日期：`2026-05-28`
- 目标：在已完成第 14 组 Web 低风险互测基础上，继续检查权限、导出、边界接口和可复现逻辑缺陷。

## 测试范围

- [x] 复核学生账号对审批汇总、审批列表和导出接口的访问范围。
- [x] 横向对比管理员、教师、学生导出内容，判断是否存在越权或信息泄露。
- [x] 继续检查低风险查询类边界参数，不执行删除、撤销、批量导入、发布等高影响操作。
- [x] 将确认缺陷追加到 `docs/testing/group14-bug-report-drafts.md`，并保留证据到 `tmp/docs/group14/web-test-results/`。

## 执行结果

- 学生访问 `/api/students/export`、他人证明和日志导出均被拒绝；学生访问 `/api/approvals/export` 返回 `200`，但导出 CSV 仅包含本人 `李明 / 20230001` 审批记录，暂不作为缺陷。
- 新增 `BUG-G14-003`：政策检索 `GET /api/policies?keyword=%00` 在学生、管理员、领导账号下均稳定返回 `500 Internal Server Error`。
- 新增 `BUG-G14-004`：领导账号可访问 `/api/policies?includeInactive=true` 并导出 `/api/policies/export`，结果包含已停用政策和政策摘要；若第 14 组确认领导具有政策台账权限，则降级为候选。
- 证据已落盘：`tmp/docs/group14/web-test-results/followup-permission-export-results.json`、`tmp/docs/group14/web-test-results/followup-boundary-fuzz-results.json`、`tmp/docs/group14/web-test-results/policy-null-keyword-bug-repro.json`、`tmp/docs/group14/web-test-results/followup-leader-api_policies_export.xlsx`。

## 风险控制

- 不把互评平台密码写入仓库、命令行参数或测试结果文件。
- 对第 14 组远程环境仅做只读或低影响请求；如需写入，会先明确记录残留影响。
- 候选 bug 必须具备可复制复现步骤、实际输出、期望输出和证据路径后再建议提交。
