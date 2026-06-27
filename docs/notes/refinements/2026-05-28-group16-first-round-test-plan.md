# 第 12 组测试第 16 组第一阶段执行细化

- 日期：`2026-05-28`
- 状态：`[x]`
- 关联主计划条目：`S29.6, S29.7, S29.8`
- 测试方：`第12组`
- 被测方：`第16组`
- 密码处理：不落盘、不回显、不写入计划文件

## 已完成资料

- [x] `S29.6` 新增第 16 组第一阶段专用测试包：`docs/testing/group16-first-round-test-packet.md`
- [x] `S29.7` 新增安全登记脚本：`scripts/testing/register-peer-review-target.ps1`
- [x] `S29.8` 复核默认初始密码不可用，正式登记改为页面输入或脚本交互输入密码，不在仓库保存密钥

## 执行口径

- 第 16 组在 `2026-05-28` 名额快照中为 `official_count = 0`、`slots_left = 3`、`coef = 1.3`，适合作为第一位正式测试对象。
- 优先通过平台页面手动登记；如需脚本登记，运行 `scripts/testing/register-peer-review-target.ps1 -TesteeId 16 -Phase 1`，由用户在终端交互输入密码。
- 若只复核名额，运行 `scripts/testing/register-peer-review-target.ps1 -TesteeId 16 -Phase 1 -DryRun`。
- 登记后按 `docs/testing/group16-first-round-test-packet.md` 执行启动验证、文档一致性、核心正向流程、Logic bug 专项与崩溃类 bug 专项。

## 边界说明

- 自动尝试官方指导书默认密码 `12345678` 失败，平台返回“用户名或密码错误”；后续不得在命令行参数或仓库文件中写入用户密码。
- 本细化仅完成第 16 组测试实施资料和安全登记工具；实际登记是否成功以平台“我的测试对象”页面或脚本返回为准。

## 验证记录

- `scripts/testing/register-peer-review-target.ps1 -TesteeId 16 -Phase 1 -DryRun` 已通过，输出第 16 组 `official_count=0`、`slots_left=3`、`coef=1.3`，未执行登录或登记。
- 已扫描 `docs/` 与 `scripts/testing/`，未发现用户提供密码片段落盘。
- `git diff --check` 无格式错误，仅提示主计划文件后续 Git 触碰时会进行 CRLF/LF 规范化。
- 已解析第 16 组说明文档 `C:\Users\24391\Downloads\a83c2e68371e43ccbecfaf4f48bfbb6e.zip`，抽取出使用说明、运行环境、账号与功能范围，并形成 `docs/testing/group16-usage-summary.md`。
- 已对第 16 组后端接口做最小烟测，`/api/health`、`/api/test/db`、`/api/auth/login`、`/api/student/info`、`/api/student/party/progress`、`/api/student/notice/list`、`/api/student/certificate/history` 与 `/api/student/ai/ask` 均可返回数据。
- 已整理 2 条可提交 Logic bug 草稿：中文字段乱码和请假日期顺序未校验。
- 目前仍未完成平台页面截图、录屏和正式登记录入，故尚不能声称已完成第 16 组整组互测。

## 当前结论

- 第 16 组已进入“资料解析 + 接口级烟测 + bug 草稿整理”阶段，但尚未完成平台正式登记、页面级复现证据收集与最终提交。
