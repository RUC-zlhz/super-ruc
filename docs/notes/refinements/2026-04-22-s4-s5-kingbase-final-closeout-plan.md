# S4 / S5 Kingbase 最终收口执行细化

- 日期：`2026-04-22`
- 关联主计划：`S4A.3, S4B.1, S4B.3, S4C.1, S4C.2, S4C.3, S5A.4, S5B.1, S5B.2, S5B.3, S5B.4`
- 当前状态：`CLOSED`
- 执行模式：`严格 gated`

## 范围

- 为 `S4` 剩余数据库验证与 `S5` 正式交付建立同一条执行主链。
- 将本机隔离 Kingbase 实例、迁移 / 回归 / benchmark / 文档出件固定为可复用脚本和可回写证据。
- 保持 `main` 为当前唯一开发主线；新增脚本、验证与文档回写均以当前工作区事实为准。

## 非范围

- 不回退 `S0 ~ S3` 已完成结论。
- 不修改现有 `54321` Kingbase 服务的数据目录、端口、鉴权或业务库。
- 不在 `S4` gate 未关闭前伪造 `S5B.3 / S5B.4` 完成。

## 执行波次

### Wave 0：计划与入口固化

- [x] `W0.1` 读取权威主计划、`S4` / `S5` 细化和当前工作区事实。
- [x] `W0.2` 新增本细化文件，并在主计划登记为当前 `S4 -> S5` 收口入口。

### Wave 1：隔离 Kingbase 运行时

- [x] `W1.1` 新增 `backend/scripts/dev/bootstrap_local_kingbase.ps1`
  - 目标：基于本机 `D:\Database\Kingbase\ES\V9\KESRealPro\V009R001C002B0014\Server\bin` 创建隔离实例。
  - 固定口径：独立数据目录、独立日志目录、端口 `54323`、数据库 `sip_db` / `sip_db_test`。
  - 命令面：`init / start / stop / reset / status`。
- [x] `W1.2` 新增 `backend/scripts/dev/run_s4_kingbase_gate.ps1`
  - 目标：统一执行 `uv sync --extra dev`、`alembic upgrade head`、`seed_initial.py`、集成测试、benchmark。
  - 固定环境：`UV_CACHE_DIR`、`DATABASE_URL`、`KINGBASE_DATABASE_URL`、`TEST_DATABASE_BOOTSTRAP_URL`。
  - 命令面：`migrate / seed / tests / benchmark / all`。

### Wave 2：S4 数据库 gate

- [x] `W2.1` 在隔离零库执行 `uv run alembic upgrade head`，关闭 `S4C.1.2`。
- [x] `W2.2` 回跑 `S4A.3` 权限与审计回归，覆盖画像 / 通知 / 事务 / 导入导出 / 审计访问控制。
- [x] `W2.3` 在 Kingbase 上完成 `S4B.1.2` 索引迁移验证。
- [x] `W2.4` 在 Kingbase 上回跑核心 CRUD、导入与关键查询，关闭 `S4C.2.*`。
- [x] `W2.5` 执行 `tests/performance/test_student_import_benchmark.py`，回写 `S4B.3.2` 耗时结果与是否达标结论。
- [x] `W2.6` 将 `S4C.3.1` 兼容结果、残留风险和证据回写到主计划与 `S4` 细化。

### Wave 3：S5 严格 gated 收口

- [x] `W3.1` 依据 Kingbase 真实验证结果重跑 `docs/notes/v15-acceptance-walkthrough.md`，只把有证据支撑的 `⚠️ / [!]` 改为 `✅`。
- [x] `W3.2` 新增 `scripts/srs/v1_6/run_v16_delivery_gate.ps1`，串起 `v1.6` 四步出件链。
- [x] `W3.3` 在 `S4` 全绿后正式导出 `v1.6` 的 `docx / emf / pdf` 交付件。
- [x] `W3.4` 对 `v1.6` 六类导出件做最终可读性与一致性检查，并回写 `S5B.4`。

## 最终结果

- [x] 已基于 `backend/scripts/dev/bootstrap_local_kingbase.ps1` 建立隔离 `54323` Kingbase 实例；`initdb --dbmode` 已固定为当前本机可用的 `pg`。
- [x] 已执行 `& '.\backend\scripts\dev\run_s4_kingbase_gate.ps1' all -SkipSync -DbMode pg`，依次通过 `migrate / seed / tests / benchmark`；其中 `S4` 集成 gate 为 `44 passed, 1 warning`，导入 benchmark 中位数为 `median_total_seconds=0.445476`、`median_commit_seconds=0.337598`、`median_validate_seconds=0.107221`。
- [x] 已在提权环境下执行 `& '.\scripts\srs\v1_6\run_v16_delivery_gate.ps1' -Force` 全链通过，输出 `v1.6`、`v1.6-emf`、`v1.6-emf-inkscape` 三组 `docx / pdf` 共 `6` 个正式交付件。
- [x] 已补一致性检查：三份 `v1.6` PDF 均为 `36` 页 A4；普通版 `docx` 内嵌 `13` 个 `.png` 与 `13` 个 `.svg`，两份 EMF 变体 `docx` 均内嵌 `13` 个 `.emf`；导出结束后未残留 `WINWORD / POWERPNT / inkscape` 进程。

## 验收条件

- 存在可重复执行的本机隔离 Kingbase 启停与 gate 脚本。
- `S4A.3 / S4B.1 / S4B.3 / S4C.1 ~ S4C.3` 均有命令、环境、结果三位一体证据。
- `S5A.4` 与 `S5B.*` 的状态回写与主计划保持一致，不出现“文档全绿但 gate 未关闭”的错位。

## 变更记录

- `2026-04-22`：创建文件，作为 `S4 -> S5` 最终收口执行入口，固定隔离 Kingbase、数据库 gate 与正式交付的统一顺序。
- `2026-04-22`：完成 `W1.1 ~ W2.6`；本机隔离 Kingbase gate 已实跑通过，`S4A.3 / S4B.1 / S4B.3 / S4C.*` 形成真实数据库证据并回写主计划与 `S4` 细化文件。
- `2026-04-22`：完成 `W3.1 ~ W3.4`；`docs/notes/v15-acceptance-walkthrough.md` 已更新为全量 `✅` 收口版，`v1.6` 六类交付件已正式导出并通过页数 / 嵌入资源一致性检查。
