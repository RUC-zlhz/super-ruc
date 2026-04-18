# v1.5 → v1.6 功能补全计划

**生成时间**: 2026-04-18
**输入来源**: `docs/notes/v15-acceptance-walkthrough.md`
**目标**: 闭合 SRS v1.5 全部 FR / NFR，完成文档链条修复后导出 SRS v1.6
**里程碑**: M1（P0，1~2 周）→ M2（P1，1 周）→ M3（完善 + 文档，2~3 天）

---

## 已锁定决策

| # | 议题 | 决策 |
|---|------|------|
| 1 | FR-005 理论自测范围 | 支持**单选 / 多选 / 判断**三种题型；题库 CRUD 与答题链路全部交付；**不造真实题目**（由甲方/团建老师后续导入） |
| 2 | FR-016 图表库 | **ECharts + vue-echarts**（覆盖堆叠柱 / 环图 / 折线 / 仪表盘，主题丰富，Vue 3 生态稳） |
| 3 | FR-014 管理端 mock | 接受：甲方 Excel 样例到位前，先用 `scripts/seed_initial.py` 种子数据驱动开发 |
| 4 | SRS 版本 | M3 结束后导出 **v1.6**（文件名沿用 v1.5-emf-inkscape 的排版规则） |

---

## M1 — P0 验收阻塞项（预计 1~2 周）

### ① FR-005 理论自测（3~4 天，最大件）

**后端**
- `backend/alembic/versions/0008_quiz.py`
  - `quiz_questions`: id / topic（党团/通用…）/ qtype（SINGLE/MULTI/JUDGE）/ stem / options_json / correct_key / explanation / is_active / created_at
  - `quiz_records`: id / student_id / question_id / answer / is_correct / score / submitted_at
  - 索引：`quiz_questions(topic, is_active)`、`quiz_records(student_id, submitted_at)`
- `backend/app/workflow/quiz_models.py`（新文件，避免 `models.py` 膨胀）
- `backend/app/workflow/quiz_service.py`：`grade(qtype, correct_key, answer)` 支持三种题型
- `backend/app/workflow/router.py` 补端点：
  - `GET /admin/quiz-bank` · `POST /admin/quiz-bank` · `PATCH /admin/quiz-bank/{id}` · `DELETE /admin/quiz-bank/{id}`
  - `GET /quiz/questions?topic=&limit=` 学生抽题
  - `POST /quiz/submit` 提交（body: `[{question_id, answer}]`）→ 返回每题对错 + 总分
- 测试：`backend/tests/integration/test_quiz_flow.py` — 三种题型各一条 + 重复提交 + 无效选项

**前端**
- 管理端：`web/src/views/workflow/QuizBank.vue` — 题库表格 + 新增/编辑抽屉（题型切换控件联动选项编辑）
  - 入口：并入 `PartyStageList.vue` 作为第 4 个 tab，或新独立路由 `/workflow/quiz-bank`
- 学生端：`miniapp/src/pages/workflow/quiz.vue` — 抽题 → 答题（按 qtype 渲染 radio/checkbox/是否）→ 提交 → 结果页
- `miniapp/src/pages.json` 注册；`miniapp/src/api/workflow.ts` 补 `fetchQuizQuestions/submitQuiz`
- 入口：党团进度页右上角"去自测"

**依赖**: 无

---

### ② FR-010 通知管理 UI 补标签 + 目标人群（1.5 天）

- `web/src/views/notice/NoticeList.vue` 抽屉改造：
  - `<a-select mode="tags" :options="tagOptions">` 读取 `notice_tags` 表
  - 目标人群构造器（四段）：年级 multi / 专业 multi / 班级 multi / 角色 multi → 序列化为 `audience_rule` JSON
  - "预览命中人数"按钮：调 `POST /admin/notices/preview-target` 返回 `{ hit_count, sample_users[] }`
- `web/src/api/notice.ts`：补 `previewAudience(rule)`、`listTags()`
- 预期验收：创建一条通知可选 ≥2 tag、圈选范围、点预览显示命中数、保存后列表可见

**依赖**: 后端已有；只需确认 `preview-target` 返回结构

---

### ③ FR-011 通知发送记录页（1 天）

- `web/src/views/notice/DeliveryRecord.vue` 新建：
  - 顶部通知选择（下拉）+ 渠道筛选（IN_APP / EMAIL / SMS）
  - `delivery_batch` 主表：发起时间 / 渠道 / 总量 / 成功数 / 失败数 / 状态
  - 行展开进入 `delivery_record` 明细：user_id / 姓名 / 状态 / delivered_at / error_message
- `web/src/router/index.ts` 注册路由 `/notice/delivery-record`
- `NoticeList.vue` 每行补"查看投递"按钮
- 后端：复用 `/admin/notices/{id}/delivery`，如返回结构不含 batch 明细，在 `notice/service.py` 补 `list_delivery_batches()`

**依赖**: 核对后端返回结构

---

### ④ FR-018 账号生命周期漏口修复（30 分钟，✅ 已在本次修复）

- `backend/app/profile/router.py`：学生侧写操作 `POST /me/corrections` 改用 `ActiveStudentDep`
- `backend/tests/integration/test_profile_flow.py` 追加：`enrollment_status=GRADUATED` 账号提交申诉 → 预期 403

**依赖**: 无

---

## M2 — P1 看板与权限视觉（预计 1 周）

### ⑤ FR-016 运营看板数据对接（2 天）

- 后端 `app/report/service.py:build_overview` 返回：
  - 请求总量 + 按状态分桶（PENDING/APPROVED/REJECTED/OFFLINE_HANDLED）
  - 审批时效 p50/p95
  - 通知 30 天触达率（按渠道）
  - 党团阶段分布
  - 学业缺口学生数（弱提示口径）
- 前端：`pnpm -C web add echarts vue-echarts`
- `web/src/views/dashboard/OperationDashboard.vue` 替换占位：
  - 4 张 metric 卡（总申请 / 今日通过 / 今日新通知 / 归档账号）
  - 堆叠柱：近 30 天申请量按状态
  - 环图：党团阶段分布
  - 折线：通知触达率趋势
- `web/src/api/report.ts` 补对接

**依赖**: echarts 选型已定

---

### ⑥ FR-018 管理端非在读视觉（0.5 天）

- `web/src/views/profile/StudentProfile.vue`：
  - 顶部 `<a-alert type="warning" v-if="!isActive">历史归档学生，仅供查阅</a-alert>`
  - 所有编辑按钮 / 新增 fact / 审批申诉按钮 `v-if="isActive"`
  - `enrollment_status` 徽章改配色（ACTIVE 绿 / SUSPENDED 橙 / GRADUATED 灰 / TRANSFERRED 红）

**依赖**: 无

---

### ⑦ FR-014 管理端缺口查询面板（1.5 天）

- `web/src/views/academic/GapQuery.vue` 新建：
  - 顶部筛选：年级 / 专业 / 班级
  - 学生表格：姓名 / 学号 / 已修学分 / 缺口模块数 / 风险等级（弱提示配色）
  - 行点击打开抽屉，详情复用现有学生缺口接口
- 后端 `GET /admin/report/academic-gap` 返回按范围聚合的轻量列表
- 数据来源：种子数据 mock（接受决策 #3）

**依赖**: 无（mock 驱动）

---

### ⑧ NFR-002 归档定时任务（0.5 天）

- 方案：应用内 APScheduler（避免额外容器）
- `backend/app/core/scheduler.py` 新文件：启动时注册每日 02:00 跑 `archive_audit_logs.run()`
- `backend/app/main.py` lifespan 挂载
- `backend/README.md` 部署章节补说明 + 手动触发命令

**依赖**: 无

---

### ⑨ NFR-003 索引 + 性能基准（1 天）

- `backend/alembic/versions/0009_performance_indexes.py`：
  - `audit_logs(occurred_at)` · `audit_logs(entity_code, entity_id)`
  - `requests(status, submitted_at)` · `requests(applicant_id)`
  - `delivery_records(notice_id, user_id)` · `delivery_records(status)`
  - `notices(published_at)`
  - `knowledge_entries(status, category)`
- 基准测试：`backend/tests/performance/test_import_100rows.py`
  - `pnpm`... 用 `pytest-benchmark`；目标：100 行学生导入 < 60s（NFR-003 门槛）
- 结果写入 `docs/notes/perf-baseline-v16.md`

**依赖**: 无

---

## M3 — 完善 & 文档闭环（预计 2~3 天）

### ⑩ FR-003 模板管理独立 tab（0.5 天）
- `web/src/views/knowledge/TemplateList.vue` 从 `EntryList.vue` 拆出；路由 `/knowledge/templates`

### ⑪ FR-008 管理端重提文案（0.5 天）
- `ApprovalDetail.vue` 驳回后自动显示"学生可在 N 日内修改后重新提交（状态可追踪）"
- N 值从 `settings.REJECT_REOPEN_DAYS` 读，默认 7

### ⑫ 上游文档闭环（1 天）
- `docs/srs/01-customer-problems.md` 追加：
  - `CP-011 荣誉信息分散于红头文件与线下通知，无法集中展示与查询`
  - `CP-012 学生成长数据分散于多个线下表格，辅导员 / 领导难以快速获得全貌`
- `docs/srs/03-customer-needs.md` 追加：
  - `CN-014 校级及以上正式荣誉需平台集中公示并支持授权合规`
  - `CN-015 学院需要聚合学籍与成长数据形成可共享的学生画像供管理侧参考`
- `docs/srs/traceability-matrix.md` 把 Completeness Check 的 ⚠️ 改回 ✅

### ⑬ 导出 SRS v1.6（0.5 天）
- 按模板 `docs/templates/软件需求规格说明书模板.docx` 重出
- 文件：`output/doc/软件需求规格说明书-信息学院学生综合服务与党团管理平台-v1.6.docx` + .pdf
- 同时产出 `v1.6-emf.docx` 和 `v1.6-emf-inkscape.docx`（图片替换规则与 v1.5 一致）

---

## 关键路径与顺序

```
M1 并行：①(3~4d) ②(1.5d) ③(1d) ④(30min)
        ↓ 收口
M2 并行：⑤(2d) ⑥(0.5d) ⑦(1.5d) ⑧(0.5d) ⑨(1d)
        ↓ 收口
M3 串行：⑩ → ⑪ → ⑫（文档） → ⑬（SRS 出件）
```

---

## 验收门槛（M3 完成时回跑一遍）

1. `backend/tests/integration/` 全部绿
2. `backend/tests/performance/test_import_100rows.py` < 60s
3. `pnpm -C web build` & `pnpm -C miniapp build:mp-weixin` 均通过
4. 重新跑 `docs/notes/v15-acceptance-walkthrough.md` 验收走查，所有 ❌ / ⚠️ 变 ✅
5. `traceability-matrix.md` Completeness Check 全 ✅
6. `output/doc/…v1.6.docx` 导出且图片全部显示为文本（Word 兼容）

---

## 风险与未决

| 风险 | 缓解 |
|------|------|
| 甲方 Excel 样例（Q-08）迟迟不到，影响 FR-015 校验器 | 先用种子数据 + mock 校验器，交付按"弱提示"兜底；样例到位后 1 天内补真实校验 |
| 微信正式 AppID 未到 | miniapp 继续用测试 AppID，不阻塞 M1-M3；联调走 H5 |
| 字段级权限矩阵（Q-P1）未冻结 | FR-012 架构已支持任意字段配置，等矩阵到位只需 seed 数据变更 |
| ECharts 首次加载体积 | 按需引入（`vue-echarts` + `echarts/core` 按组件注册） |
