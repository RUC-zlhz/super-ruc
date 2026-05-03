# S8 全量需求 Gap 闭环推进

- 创建日期：`2026-05-04`
- 关联主计划：`S8.1 ~ S8.4`
- 状态：`[x]`
- 输入依据：`S8 Gap 并行闭环修复计划`、`docs/notes/requirements-gap-matrix-2026-05-02.md`

## 目标

在 `S7` 已关闭高优先级缺口后，继续关闭复核确认的 P1/P2 gap：小程序知识库自助闭环、转线下通知推送、短信收件句柄与脱敏、学期看板口径、管理端默认在读列表口径、文档追踪漂移与后端 lint 基线。

## 并行分工与完成状态

- [x] `S8.1` Miniapp 知识库闭环：`miniapp/src/api/knowledge.ts` 与 `miniapp/src/pages/knowledge/index.vue` 已补分类列表、分类/标签搜索参数、显式 AI match、详情模板列表、模板下载/打开、人工咨询提示。
- [x] `S8.2` Workflow / Notice 闭环：`backend/app/workflow/service.py` 已在转线下时生成学生站内通知；`backend/app/notice/service.py` 已改为短信 raw phone 解密发送、脱敏手机号留痕、无手机号 `NO_PHONE / SKIPPED`。
- [x] `S8.3` Report / Profile 口径闭环：`/admin/report/overview` 已支持 `term_code`；Web 看板已补学期筛选；`/admin/profile/students` 默认仅返回在读，支持 `include_non_active` 与 `enrollment_status` 显式查询历史/非在读。
- [x] `S8.4` Docs + Validation baseline：已同步 NFR `Applies To FRs`、上下文图 M6/M7、S6.21 细化登记、S7 前快照说明、S8 主计划登记；`backend/pyproject.toml` 增加针对现有开发密钥/大写兼容属性的 lint 豁免，避免安全误报掩盖真实回归。

## 验证要求

- [x] `backend`：`uv run --no-sync ruff check app tests`
- [x] Miniapp：`& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json`
- [x] Web：`& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json`
- [x] Web build：`pnpm -C web build`
- [x] Miniapp build：`pnpm -C miniapp build:mp-weixin`
- [x] Targeted backend tests：隔离 Kingbase `127.0.0.1:54323` 下执行 `uv run --no-sync pytest tests/integration/test_request_flow.py tests/integration/test_notice_flow.py tests/integration/test_report_contract_flow.py tests/integration/test_profile_flow.py tests/integration/test_knowledge_flow.py -q -o cache_dir=.tmp/pytest-cache-s8 --basetemp=.tmp/pytest-tmp-s8`，结果 `34 passed in 24.78s`
- [ ] Optional final gate：`backend/scripts/dev/run_s4_kingbase_gate.ps1 all -SkipSync` 本轮未重复执行全量 gate；本轮已用同一隔离 Kingbase 运行 S8 定向集成回归

## 风险与约束

- `FR-014` PDF 成绩单仍按 `S7` 最小闭环保留为上传记录、解析候选、人工核验与不写正式成绩，不在本轮升级为自动入库。
- `FR-009` 文件交换范围不在本轮扩大；如需补完整 Word/PDF 导入导出治理，另开 `S9`。
- `term_code` 对运营看板的最小口径是通过请求、通知、流程时间字段映射学期日期范围；没有 `term_code` 字段的业务表不做结构性迁移。

## 变更记录

- `2026-05-04`：创建本细化文件，并完成 `S8.1 ~ S8.4` 代码与文档回写。
- `2026-05-04`：静态验证已通过 `backend ruff`、`web vue-tsc`、`miniapp vue-tsc`；`web build`、`miniapp mp-weixin` 出包与 S8 定向后端集成测试均已通过。
- `2026-05-04`：按仓库 Windows 稳定性规则将 `pytest` 的 `cache_dir` 与 `basetemp` 固定到 `backend/.tmp`；定向测试运行时另外使用 run-specific cache/temp 与 `LOCAL_OBJECT_STORAGE_ROOT=backend/.tmp/local-object-storage-s8`，避免写入受限的历史临时目录。
