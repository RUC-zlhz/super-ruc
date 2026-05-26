# S47 多角色联通完成度审计与补测

- 日期：`2026-05-26`
- 主计划关联：`S47`
- 当前状态：`[x]` 已完成
- 输入依据：`docs/notes/refinements/2026-05-26-s45-full-stack-test-bug-audit.md`、`docs/notes/refinements/2026-05-26-s46-s45-bug-fix-closure.md`

## 范围

- [x] `S47.1` 审计 S45/S46 剩余验证缺口，明确哪些属于当前本机可测，哪些依赖真实外部环境。
- [x] `S47.2` 新增 DB 驱动的教师/学生多角色联通 smoke 测试，覆盖通知、申请审批、画像、学业看板与荣誉的跨角色可达性。
- [x] `S47.3` 回跑新增定向测试与必要全量 gate，若暴露缺陷则按崩溃类 / Logic bug 分级并优先修复。
- [x] `S47.4` 回写主计划和本细化文件，形成完成度审计结论。

## 当前审计结论

- S45 明确留下的本机可测缺口是“教师、辅导员、班主任、党团教师、学生账号各一组，做一次教师-学生联通 E2E：通知、申请、党团流程、画像/荣誉、学业看板”。
- 真实微信开发者工具 + 真实 code 登录依赖外部微信环境，本机只能覆盖 mock 微信登录、后端契约和小程序构建产物，不能伪造为真实微信通过。
- S46 已修复并验证 S45 登记的可代码闭环缺陷；S47 不重复修复同一问题，重点补强跨模块联通证据。

## 验证记录

- 新增测试：`backend/tests/integration/test_s47_cross_role_linkage_smoke.py`。
- 定向 DB 集成：
  - `uv run --extra dev pytest tests/integration/test_s47_cross_role_linkage_smoke.py -q -o cache_dir=../.tmp/pytest-cache-s47-linkage --basetemp=../.tmp/pytest-tmp-s47-linkage`
  - 结果：`1 passed in 66.77s`。
- 后端静态与编译：
  - `uv run --extra dev ruff check app tests unit_tests scripts`：通过。
  - `uv run --extra dev python -m compileall -q app tests unit_tests scripts`：通过。
- 后端全量 DB 集成：
  - `uv run --extra dev pytest tests/integration -q -o cache_dir=../.tmp/pytest-cache-s47-full --basetemp=../.tmp/pytest-tmp-s47-full`
  - 结果：`124 passed, 3 warnings in 215.90s`。
- 双端构建：
  - `pnpm -C web build`：通过。
  - `.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json`：通过。
  - `pnpm -C miniapp build:mp-weixin`：通过。

## 缺陷分级

- 本轮未新增有效崩溃类 bug。
- 本轮未新增有效 Logic bug。
- 首次运行 S47 测试时，荣誉测试数据使用了不符合当前契约的 `COLLEGE` 级别；业务规则只支持 `NATIONAL / PROVINCIAL / MINISTERIAL / SCHOOL`，因此该失败是测试数据假设错误，已修正为 `SCHOOL`，不计入产品缺陷。

## 完成结论

- 当前本机可自动化覆盖的 DB 集成、教师学生多角色联通、Web 构建和 Miniapp 微信出包均已通过。
- 真实微信开发者工具 + 真实 code 登录仍需外部微信环境，不属于本机可伪造通过项。
