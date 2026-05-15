# S14 安全、权限与验证闭环修复

- 创建日期：`2026-05-14`
- 关联主计划：`S14.1, S14.2, S14.3, S14.4, S14.5, S14.6, S14.DB, S14.DOC`
- 状态：`[x]`
- 输入依据：2026-05-14 并行审查结论（需求/SRS、后端、Web、小程序、验证链）与本地 gate 复跑记录

## 目标

在 `S12/S13` 已通过构建和定向验证的基础上，修复审查确认的实质缺口：微信学生绑定安全、停用账号与退出失效、Web 前端角色闸门、小程序访客态和缓存隔离、S12 成绩单 PDF 教师核验闭环、S13 官方来源治理、真实 DB/迁移 gate 与规格文档漂移。

## 执行拆分

- [x] `S14.1` 微信绑定与账号安全：绑定不再仅凭学号；同一学生只能绑定一个微信用户；微信登录检查 `users.is_active`；退出登录服务端失效 token 并写入审计。
- [x] `S14.2` Web 前端权限边界：治理页路由与菜单补齐与后端一致的 `roles`，低权限账号在进入页面前被前端拦截。
- [x] `S14.3` 小程序访客态与缓存隔离：学生专属 Tab/页面在访客态先提示绑定；首页缓存按当前用户隔离，账号切换不展示上一位学生数据。
- [x] `S14.4` S12 PDF 教师核验闭环：Web 导入中心提供成绩单 PDF 候选审核、确认提交与结果回看入口。
- [x] `S14.5` S13 官方来源治理：禁止无 `source_url` 的官方来源兜底，来源创建/修改写审计，官方标识变更可追踪。
- [x] `S14.6` 临时 IP 小程序出包治理：固定临时部署出包命令与产物检查，避免直接导入旧 `127.0.0.1:8080` 产物。
- [x] `S14.DB` 真实 DB / 迁移 gate：补 blank DB `alembic upgrade head + seed_initial + Kingbase` 空库链验证，并覆盖默认学生/培养方案 seed/bootstrap。
- [x] `S14.DOC` 规格文档收口：修正 `specs/001-student-service-platform` 对证明模板、S12/S13 边界和验证链的过强或过期承诺。

## 验证要求

- Backend：设置 repo-local `UV_CACHE_DIR` 后执行 `ruff`、`py_compile` 与相关定向集成测试；涉及迁移时必须覆盖空库 `alembic upgrade head`。
- Web：执行 `pnpm -C web build`，并确认路由/菜单角色过滤与后端角色常量一致。
- Miniapp：执行 `pnpm -C miniapp build:mp-weixin`，必要时检查产物 `utils/request.js` 中 API base URL。
- DB：可用时执行隔离 Kingbase gate；如本机 DB 拒连，阻塞项必须明确记录而不能标绿。
- Docs：每次实质工作后回写本细化文件与主计划。

## 本轮验证结果

- Backend 静态校验：`backend` 下设置 `UV_CACHE_DIR=backend\.tmp\uv-cache-s14` 后执行 `uv run --extra dev ruff check app/auth app/core/dependencies.py tests/integration/test_auth_flow.py alembic/versions/0013_s14_auth_token_binding_hardening.py` 通过；同环境执行相关文件 `py_compile` 通过。
- Backend 定向集成：执行 `uv run --no-sync pytest tests\integration\test_auth_flow.py -q -o cache_dir=.tmp/pytest-cache-s14-auth --basetemp=.tmp/pytest-tmp-s14-auth` 未进入业务断言，仍在 `localhost:54322/sip_db_test` 连接阶段报 `ConnectionRefusedError [WinError 1225]`，因此 `S14.1` 不标记完成。
- Web：`pnpm -C web build` 通过，覆盖路由/菜单角色常量和退出登录 API 接入。
- Miniapp：`vue-tsc --noEmit -p miniapp\tsconfig.json` 通过；`pnpm -C miniapp build:mp-weixin` 通过。
- 2026-05-15 复跑收口：修复 refresh token 版本声明、Alembic 长 revision 空库兼容和 S14 gate 参数传递后，`.\backend\scripts\dev\run_s14_blank_db_gate.ps1 -SkipSync` 通过，覆盖隔离 Kingbase `54324` 从零初始化、`alembic upgrade head`、`seed_initial.py` 与 `seed_default_data.py`；同一隔离库执行 `uv run --extra dev pytest tests/integration/test_auth_flow.py tests/integration/test_knowledge_flow.py tests/integration/test_s12_gap_closure.py -q -o cache_dir=.tmp/pytest-cache-s14-final --basetemp=.tmp/pytest-tmp-s14-final`，结果 `27 passed in 26.13s`。
- 2026-05-15 前端复跑：`pnpm -C web build` 与 `pnpm -C miniapp build:mp-weixin` 均通过。

## 风险与约束

- 微信绑定安全优先于兼容旧的“只填学号”绑定入口；若默认学生没有身份证号，可使用姓名作为最低绑定校验因子。
- 退出登录以账号级 token 版本失效为一期闭环；如后续需要多端会话级管理，应新增会话表而不是复用本阶段实现。
- 小程序仍以 `mp-weixin` 为权威验收口径，H5 预览不作为完成态依据。

## 变更记录

- `2026-05-14`：创建本细化文件，登记 S14 范围、P0 优先级和验证口径；本轮先推进 `S14.1 ~ S14.3`。
- `2026-05-14`：完成 Web 前端角色闸门、小程序访客态拦截与首页缓存按用户隔离；后端已实现微信绑定校验、学生绑定唯一约束、停用账号拦截和 logout token 版本失效，但定向集成测试仍受本机 DB 拒连阻塞。
- `2026-05-15`：完成剩余 S14 收口；Web 导入中心补 PDF 教师核验入口，知识来源官方 URL 约束与审计落地，临时 IP 小程序出包脚本补产物检查，空库迁移 gate 和默认数据 seed 通过，规格文档同步修正，S14 状态改为 `[x]`。
