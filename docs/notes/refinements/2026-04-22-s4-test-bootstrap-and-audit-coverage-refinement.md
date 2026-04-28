# S4 测试库 bootstrap 与审计 API 覆盖补丁

- 日期：`2026-04-22`
- 关联主计划：`S4A.3.1, S4A.3.2, S4B.1.2, S4B.3.2, S4C.1.2`
- 当前状态：`CLOSED`

## 范围

- 为 `backend/tests/conftest.py` 补测试库自动准备逻辑，降低 `sip_db_test` 缺失导致的固定阻塞。
- 为 `audit` 模块补齐 HTTP 层集成测试覆盖，收口 `/admin/audit-logs`、`/admin/audit-logs/archive`、`/admin/role-policies` 的核心权限矩阵。
- 记录本轮对本机 Docker / Kingbase 回归入口的真实探查结果，给出下一步可执行命令。

## 非范围

- 不在本文件中伪造 `S4B.1.2 / S4B.3.2 / S4C.*` 的已通过结论。
- 不修改用户现有 `54321` Kingbase 服务配置，不对其鉴权、端口或数据目录做侵入式调整。
- 不在 `S4` 验证门未关闭前签收 `S5B.3 / S5B.4`。

## 任务清单

- [x] `S4A.3-bootstrap.1` 为测试库补自动 bootstrap 逻辑
  - 文件：`backend/tests/conftest.py`
  - 结果：支持在 `DATABASE_URL` 指向缺失测试库时，通过 `TEST_DATABASE_BOOTSTRAP_URL` 或派生的 `postgres / template1` 连接自动探测并创建目标数据库。
  - 备注：用于修复“仓库默认测试入口缺少 `sip_db_test` 准备步骤”的仓库内缺口。

- [x] `S4A.3-audit.1` 为审计 HTTP 接口补集成测试
  - 文件：`backend/tests/integration/test_audit_flow.py`
  - 结果：新增 `/admin/audit-logs` 列表与 `storage_scope`、`/admin/audit-logs/archive` 归档、`/admin/role-policies` 角色策略的 `401 / 403 / 200` 断言，并覆盖 `SUPER_ADMIN / COLLEGE_LEADER / COUNSELOR` 的边界。

- [x] `S4A.3-verify.1` 回跑新增审计测试与现有敏感路径回归
  - 目标命令：`uv run --extra dev pytest tests/integration/test_audit_flow.py tests/integration/test_exchange_flow.py tests/integration/test_request_flow.py tests/integration/test_profile_flow.py tests/integration/test_notice_flow.py -q`
  - 当前状态：已在隔离 Kingbase gate 中纳入并通过，相关用例与 `test_auth_flow.py`、`test_smoke.py` 一起组成当前 `S4` 敏感路径回归入口。

- [x] `S4C.1.2-prep.1` 启动隔离的本地 Kingbase 回归实例
  - 探查结果：已基于 `backend/scripts/dev/bootstrap_local_kingbase.ps1` 固化隔离 `54323` 实例，不触碰用户现有 `54321` 服务；`initdb --dbmode` 已验证当前本机可用值为 `pg`。
  - 影响：后续 `alembic upgrade head`、完整 CRUD / 导入回归与性能基线已由 `run_s4_kingbase_gate.ps1` 统一闭合。

## 验收条件

- `backend/tests/conftest.py` 与 `backend/tests/integration/test_audit_flow.py` 通过 `py_compile` 与 `ruff check`。
- 一旦数据库环境恢复，新增 bootstrap 逻辑可让默认 `pytest` 入口不再额外依赖手工 `CREATE DATABASE sip_db_test`。
- `audit` HTTP 接口具备可回归的权限矩阵覆盖，不再只依赖 runtime/scheduler 测试。
- 上述 bootstrap 与审计覆盖已被隔离 Kingbase gate 实际消费，并成为 `S4A.3 / S4B.1 / S4B.3 / S4C.1.2` 的闭环前置资产。

## 风险 / 阻塞

- [!] 本机 `docker` CLI 不在 PATH 中，仓库自带 `deploy/docker-compose.yml` 当前无法直接作为本轮验证入口。
- [x] 仓库自带 compose 仅自动创建 `sip_db`、不会自动创建 `sip_db_test` 的缺口已由 `conftest.py` bootstrap 与隔离 `54323` Kingbase gate 共同绕开。
- [x] 本机现有 `54321` Kingbase 服务未被修改；所有 `S4` 实跑都落在隔离实例上。
- [x] 在提权环境下已允许启动隔离本地实例；`S4C` 不再受“无法启动后台数据库进程”阻塞。

## 变更记录

- `2026-04-22`：创建文件，记录测试库 bootstrap、审计 API 覆盖补丁与本机 Kingbase / Docker 探查结论。
- `2026-04-22`：执行 `uv run --extra dev python -m py_compile tests\conftest.py tests\integration\test_audit_flow.py` 通过。
- `2026-04-22`：执行 `uv run --extra dev ruff check tests\conftest.py tests\integration\test_audit_flow.py` 通过。
- `2026-04-22`：相关 bootstrap 与审计覆盖已纳入 `& '.\backend\scripts\dev\run_s4_kingbase_gate.ps1' all -SkipSync -DbMode pg` 的隔离 Kingbase gate，并与迁移、seed、核心 CRUD、关键查询和 benchmark 一并通过；本文件转为历史补丁记录。
