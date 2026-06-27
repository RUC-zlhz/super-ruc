# 第 14 组本地小程序下载与配置细化

- 日期：`2026-05-28`
- 状态：`[x]`
- 关联主计划条目：`S29.15`
- 测试方：`第12组`
- 被测方：`第14组`
- 前置条目：`S29.14`
- 密码处理：第 12 组平台密码不得写入仓库、命令参数或日志；当前脚本仅从剪贴板读取密码

## 已完成

- [x] 确认第 14 组平台资料接口 `/api/documents/group/14` 需要登录，未认证时返回 `401 Not authenticated`。
- [x] 确认互评平台前端接口包括 `/api/auth/login`、`/api/documents/group/{id}`、`/api/testing-relations/my` 与 `/api/testing-relations`。
- [x] 新增安全下载与配置脚本：`scripts/testing/setup-group14-miniapp-from-platform.ps1`。
- [x] 新增本地配置说明：`docs/testing/group14-local-miniapp-setup.md`。
- [x] 检查脚本语法，当前 Windows PowerShell 解析通过。
- [x] 使用第 12 组平台密码登录成功，并确认第 14 组已在“我的测试对象”中。
- [x] 下载第 14 组平台资料，确认仅有 1 个 `usage` PDF，未提供小程序源码包。
- [x] 本地扫描 `tmp/group14-miniapp` 未发现小程序或前端项目标记文件。
- [x] 新增候选 bug 草稿：`docs/testing/group14-bug-report-drafts.md`。
- [x] 读取用户补充 Markdown：`http://183.174.61.212:8001/uploads/784ad38352564ddcb562ebdd2c9f4ae7.md`，确认其提供 Web 互测入口和 `demo.*` 账号，但仍不是小程序源码包。
- [x] 新增 Web 测试摘要：`docs/testing/group14-web-test-summary.md`。

## 结论

- 第 14 组互评平台资料目前只提供 PDF 使用说明，未提供可导入微信开发者工具的小程序源码包或项目目录。
- 用户补充的 Markdown 可用于 Web 互测，`http://10.10.0.14/` 与五类 `demo.*` 账号已通过接口级登录烟测；但该 Markdown 仍未提供小程序源码包。
- 因此 Web 互测可以继续，小程序本地配置仍无法完成；该结论不是本地环境问题，而是缺少微信小程序源码或导入目录。
- 已按指导书“文档缺失导致项目无法运行可记录为崩溃类 bug”的口径，整理 `BUG-G14-001` 候选草稿。

## 后续人工动作

- [ ] 补充平台第 14 组资料页截图，证明资料列表仅有 PDF。
- [ ] 将 `BUG-G14-001` 按平台模板提交，或先联系第 14 组确认是否漏传源码包。
- [ ] 若第 14 组补传源码包，再重新运行 `scripts/testing/setup-group14-miniapp-from-platform.ps1` 下载并配置。
