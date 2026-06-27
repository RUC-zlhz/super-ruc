# 第 12 组测试第 7 组第一阶段执行细化

- 日期：`2026-05-28`
- 状态：`[x]` 已替代
- 关联主计划条目：`S29.13`
- 替代主计划条目：`S29.14`
- 替代文件：`docs/notes/refinements/2026-05-28-group14-first-round-test-plan.md`
- 测试方：`第12组`（沿用当前 S29 互测执行口径）
- 被测方：`第7组`
- 依据文件：`C:\Users\24391\xwechat_files\wxid_0358gc3ot2l922_40f6\msg\file\2026-05\测试实验指导书.pdf`

## 已完成

- [x] 根据用户确认的“已登记第 7 组”状态，新增第 7 组第一阶段专用测试计划：`docs/testing/group7-first-round-test-plan.md`。
- [x] 通过公开名额接口只读核对第 7 组第一阶段状态，不执行登录、不执行登记、不接触密码。
- [x] 将测试顺序收束为文档获取、启动验证、正向流程、Logic 专项、崩溃专项、去重提交六段。
- [x] `2026-05-28` 用户改为测试第 14 组，本细化保留为历史记录并由 `S29.14` 替代。

## 替代说明

- 用户明确表示“不想第七组了，想测试第14组”。
- 后续正式互测执行以 `docs/testing/group14-first-round-test-plan.md` 和 `docs/notes/refinements/2026-05-28-group14-first-round-test-plan.md` 为准。

## 只读核对结果

- 命令：`scripts/testing/register-peer-review-target.ps1 -TesteeId 7 -Phase 1 -DryRun`
- 结果：`official_count = 2`、`slots_left = 1`、`full = false`、`coef = 1.1`
- 说明：正式登记状态仍以平台“我的测试对象”页面为准；用户已确认登记完毕，因此本细化不再重复登记。

## 后续人工动作

- [ ] 从平台已登记对象页面下载或查看第 7 组文档、入口、账号和已知限制。
- [ ] 按 `docs/testing/group7-first-round-test-plan.md` 执行第 7 组启动验证和核心正向流程。
- [ ] 对第 7 组执行 Logic bug 与崩溃类 bug 专项测试。
- [ ] 按 `docs/templates/peer-review-bug-report-template.md` 整理并提交确认后的 bug。

## 边界说明

- 当前尚未读取第 7 组自己的功能文档，因此不得假设其具体业务功能或预期输出。
- 若第 7 组文档缺失导致无法运行或无法测试，可按指导书记录为崩溃类 bug；若文档描述与程序行为不一致，可按 Logic bug 记录。
- 平台资料接口 `/api/documents/all` 未登录时返回 `401 Not authenticated`，因此第 7 组资料入口需由用户在已登录平台页面中查看，或后续通过安全交互方式读取。
