# S9 并行 ABC 优化

- 创建日期：`2026-05-06`
- 关联主计划：`S9.1 ~ S9.4, S9.DB`
- 状态：`[x]`
- 输入依据：用户确认“并行 abc”，即同时推进低风险体验增量、性能/数据库小步优化、体验优先补强。

## 目标

在 `S6 ~ S8` 已闭合基础上，同时推进 Web 管理端可信展示、小程序微信端关键路径、后端契约/权限收口与数据库索引小步优化。所有改动必须建立在现有实现上，不覆盖既有设计与排版。

## 并行分工与完成状态

- [x] `S9.1` Web 管理端可信展示：运营看板去除硬编码折线、固定风险等级、固定置信度、假课程与假动作；通知、知识库、党团流程等右侧面板改为显式选择驱动，筛选/翻页后不再默认吃第一条记录。
- [x] `S9.2` Miniapp 微信端体验：学生端首页增加最近成功数据缓存、分区刷新、同步时间/缓存提示；首页服务入口支持直达事务类型；申请、流程、通知、学业等关键页增加页内错误态与重试。
- [x] `S9.3` Backend 契约/权限收口：`term_code` 非法值不再静默退化为全量；成绩单 PDF 上传对象存储失败映射为稳定业务错误；`CLASS_CADRE` 作为历史别名收口到 canonical `CLASS_MONITOR`，权限判断以 `CLASS_MONITOR` 为准。
- [x] `S9.4` DB 小步优化：新增 `audit_log_history` 的 `entity_code + occurred_at` 与 `actor_user_id + occurred_at` 复合索引迁移，并同步 ORM 模型索引声明。
- [x] `S9.DB` 后端定向集成测试：已恢复隔离 Kingbase `127.0.0.1:54323/sip_db_test`，并补跑 `test_report_contract_flow.py` 与 `test_audit_flow.py` 定向集成测试通过。

## 验证结果

- [x] Web：`& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json`
- [x] Miniapp：`& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json`
- [x] Backend lint：`UV_CACHE_DIR=D:\Codes\super-ruc\backend\.uv-cache-local; uv run --no-sync ruff check app tests`
- [x] Backend py_compile：`uv run --no-sync python -m py_compile ...`
- [x] Web build：`pnpm -C web build`
- [x] Miniapp build：`pnpm -C miniapp build:mp-weixin`
- [x] Diff whitespace：`git diff --check`
- [x] Backend targeted tests：`uv run --no-sync pytest tests\integration\test_report_contract_flow.py tests\integration\test_audit_flow.py -q --basetemp=.tmp\pytest-s9-db`，结果 `8 passed in 7.80s`。

## 风险与约束

- `S9.DB` 已补跑关闭；本轮先执行 `backend/scripts/dev/bootstrap_local_kingbase.ps1 start` 恢复隔离 Kingbase，再以 `127.0.0.1:54323/sip_db_test` 执行定向测试。
- 本轮未执行大规模 `academic-gap` 算法重构，也未把读路径 benchmark 纳入 gate；数据库优化仅限审计历史表索引和角色码迁移。
- 小程序缓存只作为最近成功数据兜底，页面必须显示缓存/同步提示，不得把旧数据伪装成实时结果。

## 变更记录

- `2026-05-06`：创建本细化文件，登记 Web / Miniapp / Backend / DB 并行优化范围与验证状态。
- `2026-05-09`：恢复隔离 Kingbase 后补跑 S9.DB 定向集成测试，`test_report_contract_flow.py` 与 `test_audit_flow.py` 合计 `8 passed in 7.80s`，关闭数据库测试阻塞。
