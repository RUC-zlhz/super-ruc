# 第 14 组 Web 互测执行细化

- 日期：`2026-05-28`
- 状态：`[x]`
- 关联主计划条目：`S29.17`
- 测试方：`第12组`
- 被测方：`第14组`
- 测试入口：`http://10.10.0.14/`

## 已完成

- [x] 基于补充 Markdown 和前端分包提取第 14 组 Web 接口清单。
- [x] 使用五类 `demo.* / demo1234` 账号完成登录烟测。
- [x] 执行学生端、管理端和权限边界低风险接口级烟测。
- [x] 定向复现操作日志列表、筛选和导出接口 `400` 问题。
- [x] 新增测试结果：`docs/testing/group14-web-test-results-2026-05-28.md`。
- [x] 新增 `BUG-G14-002` 草稿并提供平台提交精简版：`docs/testing/group14-bug-report-drafts.md`。

## 结论

- 第 14 组 Web 项目基础入口、健康检查、五类账号登录、学生端主要只读接口、管理端多数只读接口和主要权限拒绝均可用。
- `BUG-G14-002` 可稳定复现：管理员和教师访问 `/api/logs?page=1&pageSize=10`、`/api/logs?page=1&pageSize=10&action=LOGIN`、`/api/logs/export` 均返回 `400 Bad Request`，导致操作日志列表、筛选、分页与导出功能不可用。
- 本轮未执行批量导入、删除、撤销、发布等高影响写操作，避免污染第 14 组测试环境。

## 证据

- `tmp/docs/group14/web-test-results/smoke-results.json`
- `tmp/docs/group14/web-test-results/permission-matrix.json`
- `tmp/docs/group14/web-test-results/logs-bug-repro.json`
- `tmp/docs/group14/web14/AdminDashboardPage-Do-HOzQP.js`

