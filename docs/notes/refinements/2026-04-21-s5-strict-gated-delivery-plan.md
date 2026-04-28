# S5 严格 gated 交付执行细化

- 日期：`2026-04-21`
- 关联主计划：`S5A.1, S5A.2, S5A.3, S5A.4, S5B.1, S5B.2, S5B.3, S5B.4`
- 当前状态：`CLOSED`
- 执行模式：`严格 gated`

## 背景

- `S5` 的上游文档缺口可以在当前工作区直接关闭。
- `S4A.3 / S4B.1 / S4B.3 / S4C.1 ~ S4C.3` 仍未正式关闭，其中 `S4C` 受可用数据库环境阻塞。
- 因此，本次 `S5` 只能把“文档追踪链、严格 gated 验收复核、v1.6 出件预检链”做到可验证状态，不能把正式交付与最终验收伪装为完成。

## 严格 gated 规则

1. 允许关闭不依赖数据库环境的上游文档项与脚本准备项。
2. `S5A.4` 必须重跑，但只能将有 `S1 ~ S4` 权威证据支持的条目改为 `✅`。
3. `S5B.3`、`S5B.4` 在 `S4` 验证门未关闭前不得标记为完成。
4. 不覆盖已有 `v1.5` 正式交付件；`v1.6` 仅准备新链路和入口。

## 当前执行状态

### S5A 追踪矩阵与上游文档闭合

- [x] `S5A.1` 在 `docs/srs/01-customer-problems.md` 补齐 `CP-011 / CP-012`
- [x] `S5A.2` 在 `docs/srs/03-customer-needs.md` 补齐 `CN-014 / CN-015`
- [x] `S5A.3` 在 `docs/srs/traceability-matrix.md` 关闭“待上游补充”残留，并将剩余 `S4` 问题转写为交付门而非追踪矩阵缺口
- [-] `S5A.4` 重跑 `docs/notes/v15-acceptance-walkthrough.md`

`S5A.4` 当前结论：

- 已收口为 `✅`：`FR-008 / FR-010 / FR-011 / FR-014 / FR-016 / FR-018`，以及 `fix.md` 条目 `①`
- 保留 `⚠️`：`FR-012 / FR-013 / NFR-001 / NFR-003`
- 保留 `[!]`：`ICR-004 Kingbase`

### S5B SRS v1.6 正式交付件

- [-] `S5B.1` 已准备 `scripts/srs/build_srs_v16_from_v15.py` 与 `scripts/srs/v1_6/` 包装脚本，形成 `v1.6` 基线与版式更新入口
- [-] `S5B.2` 已将 `v1.6` 出件链切换到受控 Mermaid 图源和独立 `tmp/docs/v1_6/` 工作目录，避免污染 `v1.5`
- [!] `S5B.3` 正式导出 `docx / emf / pdf` 仍受严格 gated 规则限制，当前不执行正式出件
- [!] `S5B.4` 最终可读性与一致性检查依赖正式导出物，当前不能签收

## 本轮落地资产

- 上游文档：
  - `docs/srs/01-customer-problems.md`
  - `docs/srs/03-customer-needs.md`
  - `docs/srs/traceability-matrix.md`
- 严格 gated 验收复核：
  - `docs/notes/v15-acceptance-walkthrough.md`
- `v1.6` 预检链：
  - `scripts/srs/build_srs_v16_from_v15.py`
  - `scripts/srs/v1_6/common.py`
  - `scripts/srs/v1_6/update_v16_docx_split_svg.py`
  - `scripts/srs/v1_6/build_v16_emf_variant.py`
  - `scripts/srs/v1_6/build_v16_inkscape_emf_variant.py`
  - `scripts/srs/README.md`

## 阻塞与下一步

- `[!]` 本地测试库 `localhost:54322/sip_db_test` 仍拒连，无法完成 `S4` 依赖的 DB 回归补证。
- `[!]` 当前未提供可用 Kingbase 零库环境，无法关闭 `S4C.1 ~ S4C.3`。
- 下一步必须在数据库环境恢复后执行：
  1. 回跑 `S4A.3` 权限与敏感路径回归
  2. 执行 `0009_s4b_targeted_indexes.py` 迁移并记录性能基线
  3. 在 Kingbase 零库执行迁移、CRUD、导入与关键查询回归
  4. 解除 gate 后再运行 `v1.6` 正式导出与最终质检

## 关闭回写（2026-04-22）

- `S4` 数据库 gate 已在隔离 `54323` Kingbase 实例上关闭；`& '.\backend\scripts\dev\run_s4_kingbase_gate.ps1' all -SkipSync -DbMode pg` 已通过 `migrate / seed / tests / benchmark` 全链。
- `docs/notes/v15-acceptance-walkthrough.md` 已从 `2026-04-21` 严格 gated 复核版更新为 `2026-04-22` 收口版，`FR-012 / FR-013 / NFR-001 / NFR-003 / ICR-004` 已改写为 `✅`。
- `& '.\scripts\srs\v1_6\run_v16_delivery_gate.ps1' -Force` 已在提权环境下全链通过，`v1.6`、`v1.6-emf`、`v1.6-emf-inkscape` 三组 `docx / pdf` 共 `6` 个正式交付件已生成。
- 本文件保留为历史 strict-gated 阶段记录；最终收口证据统一见 `docs/notes/refinements/2026-04-22-s4-s5-kingbase-final-closeout-plan.md`。
