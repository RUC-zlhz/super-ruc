# v1.5 验收走查清单

**生成时间**: 2026-04-18
**覆盖范围**: FR-001~018、NFR-001~005、`docs/notes/fix.md` 四条 v1.5 补充点
**来源**: 对 `backend/app/`、`web/src/views/`、`miniapp/src/pages/` 的静态代码审计
**说明**: ✅ 完整 / ⚠️ 部分或空壳 / ❌ 缺失；端到端联调未跑，性能项未测。

---

## 一、FR-001 ~ FR-018 状态矩阵

| FR | 标题 | 后端（路由 + 服务） | 管理端（web） | 学生端（miniapp） | 综合 | 关键差距 |
|----|------|---------------------|---------------|-------------------|------|---------|
| FR-001 | 政策与流程查询 | ✅ `GET /knowledge/search` + `/{id}` (knowledge/router.py:65) | — | ✅ `knowledge/index.vue` | ✅ | — |
| FR-002 | 权威答复治理 | ✅ `POST /knowledge/ai-match`，AI_QA_ENABLED 开关 + 关键词降级 (knowledge/service.py:132) | ✅ 审核/下架动作嵌入 `knowledge/EntryList.vue` | ✅ | ✅ | 审核/下架没有独立入口，功能在列表内 |
| FR-003 | 知识与模板维护 | ✅ entries/templates/sources CRUD | ⚠️ 模板管理未独立（`EntryList.vue` 内混合） | — | ⚠️ | 管理端建议补"模板管理"独立 tab |
| FR-004 | 党团进度查看 | ✅ `GET /workflow/my`、`/{workflow_id}` (workflow/router.py:65) | — | ✅ `workflow/index.vue` + `detail.vue` | ✅ | — |
| FR-005 | 党团提醒管理 + 理论自测 | ✅ 提醒 ✅；理论自测：`quiz_models` + `quiz_service`（三题型判分）+ `quiz_router`（admin CRUD + 学生抽题/提交） | ✅ `PartyStageList.vue` 三 tab；`QuizBank.vue` 题库 CRUD（含 SINGLE/MULTI/JUDGE 表单） | ✅ `pages/workflow/quiz.vue`（抽题 → 答题 → 结果），`workflow/index.vue` 入口卡片 | ✅ | 集成测试 `test_quiz_flow.py` 覆盖三题型判分 + 大小写/顺序归一 + 软删 + 权限 |
| FR-006 | 事务在线提交 + PDF 预览 | ✅ `POST /requests` + `pdf_generator.py` | — | ✅ `request/create.vue` + `detail.vue`（含"转线下"卡片展示） | ✅ | — |
| FR-007 | 申请审核工作台 | ✅ `/admin/requests/{id}/approve|reject` + 转线下 `/offline` | ✅ `ApprovalDetail.vue` 含受理/通过/驳回/**转线下**按钮 | — | ✅ | — |
| FR-008 | 驳回撤回重提 | ✅ 状态机 `state_machine.py:43` | ⚠️ 驳回入口齐，重提流程仅在 miniapp | ✅ miniapp 可基于保留表单再提交 | ⚠️ | 管理端缺"允许再编辑"显式入口；建议补明确文案 |
| FR-009 | 文件导入导出 + 整批回滚 + **错误 Excel** | ✅ `exchange/service.py:177` 原子提交；`build_error_report` 生成带"错误原因"列 Excel (service.py:417) | ✅ `ImportCenter.vue` 有下载错误报告按钮（L69, L88） | — | ✅ | 端到端未联调，但代码路径齐 |
| FR-010 | 通知标签 + 目标人群 | ✅ `POST /admin/notices/preview-target` | ❌ `NoticeList.vue` 抽屉只有 title/body/source_type，**无标签选择、无目标人群圈选 UI**（L56-72） | — | ❌ | **管理端 UI 缺标签 + 目标人群表单**；后端已就绪 |
| FR-011 | 通知发送与接收记录 | ✅ 三层 dispatch/batch/delivery (notice/router.py:171) | ❌ 列表仅 `published_at`，**无投递统计视图** | ✅ `notice/index.vue` 全部/未读/已读 | ❌ | **管理端缺"发送记录"详情页** |
| FR-012 | 角色与字段级权限 | ✅ `require_role` + `get_current_user` (core/dependencies.py:73) | ✅ `system/UserManage.vue` 含 role_policies 表 | — | ✅ | P1 矩阵未冻结（业务决策）— 代码已支持 |
| FR-013 | 审计日志 | ✅ `audit/service.py:log_action` + `audit_log_history` 归档 | ✅ `AuditLog.vue` 查询 + 归档入口 | — | ✅ | — |
| FR-014 | 学业缺口（弱结论） | ✅ `GET /students/{id}/academic-gap` | ❌ 管理端 `CurriculumRules.vue` 只含规则维护，无"学生缺口查询/汇总视图" | ✅ `academic/index.vue` 含边界提示（L3-6, L58-61） | ⚠️ | 管理端建议补学生缺口查询面板（按班 / 按年级） |
| FR-015 | 培养方案规则维护 | ✅ CRUD | ✅ `CurriculumRules.vue` 三 tab（方案 / 开课 / 等价） | — | ✅ | 等待甲方 Excel 样例（Q-08）以完成 `validators/curriculum.py` 校验 |
| FR-016 | 运营统计看板 | ✅ `GET /admin/report/overview` | ⚠️ `OperationDashboard.vue` 4 个 metric 卡 + 占位说明"数据接入后在此展示" | — | ⚠️ | **管理端看板基本是占位**，需对接真实聚合数据 + 图表 |
| FR-017 | 奖励荣誉公示 | ✅ `honor/router.py` 完整 CRUD + consent_flag | ✅ `HonorList.vue` 多字段表单 | ✅ `honor/index.vue` 级别 / 学年 / 历史筛选 | ✅ | — |
| FR-018 | 学生画像 + 账号生命周期 | ✅ enrollment_status 全局拦截 `require_active_enrollment` (core/dependencies.py:93)；**但 `profile/router.py:66` 的纠错申诉未接入该依赖** | ⚠️ `StudentProfile.vue` 显示状态标签，**无非在读只读视觉锁定** | ✅ miniapp `profile/index.vue:162` 有 `enrollmentReadonly` computed，申诉入口受控 | ⚠️ | **P0 修复**：后端 profile corrections 路由漏拦截；管理端缺非在读视觉区分 |

### 小结（FR 层）
- 完整 ✅：FR-001 / 002 / 004 / 005 / 006 / 007 / 009 / 012 / 013 / 015 / 017（共 11）
- 部分 ⚠️：FR-003 / 008 / 014 / 016 / 018（共 5）
- 缺失 ❌：FR-010（通知标签目标人群 UI）/ FR-011（发送记录详情页）（共 2 处关键缺口）

---

## 二、NFR-001 ~ NFR-005

| NFR | 位置 | 状态 | 备注 |
|-----|------|------|------|
| NFR-001 敏感字段加密 | `core/security.py:65` Fernet；`auth/models.py` phone_enc / id_card_enc | ✅ | 需再巡检其他模块是否也遵守 `_enc` 约定 |
| NFR-002 审计留存 + 冷备份 | `scripts/archive_audit_logs.py` + `audit_log_history` | ✅ | ⚠️ 未见定时任务配置（crontab 或 APScheduler），需在部署文档固化 |
| NFR-003 常见操作响应时间 | — | ⚠️ | 无索引清单 / 缓存层；导入 100k 行无性能基准；需补 `audit_logs.occurred_at`、`requests.status`、`notices.status` 等索引与基准测试 |
| NFR-004 事务一致性 | `exchange/service.py:commit_batch` | ✅ | 错误回滚 + 错误 Excel 齐备，集成测试 `test_exchange_flow.py:122` 覆盖 |
| NFR-005 易用性 | 后端 `ApiResponse` 统一错误码 | ✅ | 前端是否对所有错误码都做友好提示需人工过一轮 |

---

## 三、`fix.md` v1.5 四条补充点

| # | 条目 | 状态 | 位置 |
|---|------|------|------|
| ① | 账号生命周期（enrollment_status 全局拦截） | ⚠️ | ✅ `0007_v15_lifecycle` 建表 + `require_active_enrollment` 依赖；❌ `profile/router.py:66-76` 纠错申诉未用 `ActiveStudentDep`；⚠️ 管理端 profile 页面缺视觉降级 |
| ② | 审计冷备份 | ✅ | `scripts/archive_audit_logs.py:24` 完整；`audit_log_history` 表 + 归档 UI 入口齐 |
| ③ | 涉密转线下（OFFLINE_HANDLED） | ✅ | 状态机 `state_machine.py:68`；router `/requests/{id}/offline`；联系方式载入 `decision_comment`；miniapp `request/detail.vue:22-28` 显示联系方式卡片 |
| ④ | 行级错误报告 Excel | ✅ | 后端 `exchange/service.py:417-467` `build_error_report`；管理端 `ImportCenter.vue:69-90` 下载按钮；集成测试覆盖 |

---

## 四、修复优先级建议

### P0（直接影响 v1.5 验收）
1. ~~**FR-005 理论自测**~~ ✅ 已完成（2026-04-18）：`quiz_models` + `quiz_service` + `quiz_router`；管理端 `QuizBank.vue`；学生端 `pages/workflow/quiz.vue`；`test_quiz_flow.py` 5 例全绿
2. **FR-010 管理端 UI**：`NoticeList.vue` 抽屉补标签选择 + 目标人群圈选（按年级 / 专业 / 班级 / 角色）
3. **FR-011 管理端发送记录页**：按 delivery_batch / delivery_record 做投递统计与按人员明细
4. **FR-018 账号生命周期漏口**：`profile/router.py:66` 纠错申诉路由接 `ActiveStudentDep`

### P1（验收会被追问）
5. **FR-016 运营看板**：占位替换为真实聚合数据 + 图表
6. **FR-018 管理端**：`StudentProfile.vue` 对非在读状态做整页只读视觉降级
7. **FR-014 管理端**：`CurriculumRules.vue` 外补学生缺口查询面板
8. **NFR-002**：部署文档固化归档定时任务
9. **NFR-003**：补关键表索引 + 导入性能基准

### P2（完善）
10. **FR-003 模板管理 tab** 独立
11. **FR-008 管理端重提文案**
12. **traceability-matrix.md** 已同步为 FR-001~018 / CN-001~015 / CP-001~012

---

## 五、未能静态判定的项（需人工/联调）

- 端到端可用性：所有 FR 路径实跑一遍（登录 → 查询 → 申请 → 审批 → 通知 → 画像）
- 微信小程序联调：等正式 AppID 替换测试值
- 培养方案 Excel：待甲方样例（Q-08）
- NFR-003 性能：100 人导入 60s、常见查询延迟
- 字段级权限矩阵最终口径（Q-P1）
