# S7 全量需求 Gap 闭环修复

- 创建日期：`2026-05-02`
- 关联主计划：`S7.1 ~ S7.6`
- 状态：`[x]`
- 输入依据：`docs/notes/requirements-gap-matrix-2026-05-02.md`

## 目标

围绕 2026-05-02 全量需求缺口矩阵中确认的高优先级 gap，按六条互不重叠写入边界并行修复，恢复静态验证可信度，并补齐 `FR-008 / FR-014 / FR-018` 的关键闭环。

## 并行分工

- [x] `S7.1` Web 静态检查修复：收口 `web/src/views/system/UserManage.vue` 中权限策略面板的无效模板引用。
- [x] `S7.2` Miniapp 运行配置收口：收口 API 基址、AppID 口径与 tabBar 图标生成脚本。
- [x] `S7.3` 文档漂移清理：补齐 `FR-017 / FR-018` 到规格文档，清理 S4/S5 旧阻塞口径。
- [x] `S7.4` `FR-008` 受控重批 / 重开：补后端状态迁移、审计留痕、管理端触发入口与回归测试。
- [x] `S7.5` `FR-014` 成绩单 PDF 上传解析最小闭环：补学生端入口、后端上传/解析或人工核验兜底、失败不污染正式成绩的测试。
- [x] `S7.6` `FR-018` 敏感字段完整查看申请：补申请、审批、审计留痕和双端入口。
- [x] `S7.DB` 后端定向集成测试实跑：已通过隔离 `54323` Kingbase 实例闭环，`uv run pytest` 集成回归 `52 passed`，导入 benchmark 已完成。

## 验证要求

- Web：`& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json`
- Miniapp：`& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json`
- Backend lint：`uv run --no-sync ruff check app tests`（在 `backend/` 下，先设置可写 `UV_CACHE_DIR`）
- Backend 定向测试：按修改范围优先跑 `test_request_flow.py`、`test_report_contract_flow.py`、`test_exchange_flow.py`、`test_profile_flow.py`

## 风险与约束

- `FR-014 / FR-018 / FR-008` 都涉及后端状态和审计边界，必须保守实现，不能绕过现有权限体系。
- PDF 成绩单解析若无法可靠结构化，允许先实现“上传记录 + 人工核验提示 + 不写正式成绩”的最小闭环，并在文档中明确边界。
- 多 worker 并行时不得交叉修改未分配文件；若发现必须跨边界修改，先在主线程收敛。

## 变更记录

- `2026-05-02`：创建本细化文件，登记六路并行修复计划。
- `2026-05-03`：六路实现已落地。验证通过项包括 `web vue-tsc`、`miniapp vue-tsc`、`pnpm -C web build`、`pnpm -C miniapp build:mp-weixin`、本轮后端改动文件定向 `ruff check`、`py_compile` 与 `git diff --check`。
- `2026-05-03`：通过 `backend/scripts/dev/bootstrap_local_kingbase.ps1 start` 拉起隔离 `54323` Kingbase 实例，并实跑 `backend/scripts/dev/run_s4_kingbase_gate.ps1 all -SkipSync`；`uv run pytest` 集成回归 `52 passed`，导入 benchmark `student_import_standard_100_rows` 中位数为 `0.088482s / 0.066155s / 0.022327s`，`S7.DB` 闭环完成。
