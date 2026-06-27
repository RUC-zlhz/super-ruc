# 测试互评实验执行资料落地

- 日期：`2026-05-28`
- 状态：`[x]`
- 关联主计划条目：`S29.1, S29.2, S29.3, S29.4`
- 依据文件：`C:\Users\24391\xwechat_files\wxid_0358gc3ot2l922_40f6\msg\file\2026-05\测试实验指导书.pdf`

## 范围

本细化文件将《测试实验指导书.pdf》中与测试互评相关的规则落成可执行资料，覆盖第一阶段互测、第二阶段复测、bug 报告质量与本组被测响应要求。

## 已落地资产

- [x] `S29.1` 新增测试执行计划：`docs/testing/peer-review-test-plan.md`
- [x] `S29.2` 新增逐项目测试执行清单：`docs/testing/peer-review-test-case-checklist.md`
- [x] `S29.3` 新增 bug 报告模板：`docs/templates/peer-review-bug-report-template.md`
- [x] `S29.4` 新增第二阶段使用说明模板：`docs/templates/peer-review-usage-guide-template.md`

## 执行口径

- 第一阶段互测窗口按 `2026-05-25 ~ 2026-05-31` 执行，当前日期 `2026-05-28` 已进入第一阶段中段。
- 每阶段最多正式测试 `3` 个其他小组；每个被测小组每阶段最多接受 `3` 个正式测试组。
- 优先登记正式测试数量较少的项目：`1` 个测试组系数 `1.3`，`2` 个测试组系数 `1.1`，`3` 个及以上系数 `1.0`。
- Bug 分类仅使用指导书给出的两类：崩溃类 bug 与 Logic bug。
- 报告质量按问题描述、复现步骤、输入输出、证据和修复建议五项组织。

## 后续人工动作

- [ ] 使用本组真实组号登录平台并确认账号可用。
- [ ] 在平台登记最多 `3` 个正式测试对象，并记录登记人数和得分系数。
- [ ] 按 `docs/testing/peer-review-test-case-checklist.md` 对每个正式测试对象执行测试。
- [ ] 按 `docs/templates/peer-review-bug-report-template.md` 去重整理并提交 bug 报告。
- [ ] 第二阶段前按 `docs/templates/peer-review-usage-guide-template.md` 补齐本组项目使用说明。

## 边界说明

- 本次自动化落地仅完成测试计划资料与模板文件；平台登录、正式登记、实际互测执行需要本组真实组号、平台实时状态与测试对象选择。
- 平台地址按 PDF 页面识别为 `http://183.174.61.212:8001/`；如访问失败，应先回到原 PDF 页面核对地址与端口。

