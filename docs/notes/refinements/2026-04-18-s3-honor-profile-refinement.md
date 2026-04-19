# S3 荣誉与画像闭环可执行任务树

- 日期：`2026-04-18`
- 关联主计划：`S3A.1, S3A.2, S3A.3, S3A.4, S3A.5, S3B.1, S3B.2, S3B.3, S3B.4, S3B.5`
- 当前状态：`SUPERSEDED`
- 替代关系：当前完成态已由 [2026-04-19-s3-current-state-closure-refinement.md](D:/Codes/super-ruc/docs/notes/refinements/2026-04-19-s3-current-state-closure-refinement.md) 覆盖；本文件保留为 `S3` 初版任务拆分记录。
- 说明：本文件只细化 `S3 荣誉与画像闭环`，不替代 `docs/notes/current-implementation-plan.md` 的主计划地位。

## 范围

- 将 `S3A 荣誉展示（FR-017）` 与 `S3B 学生画像（FR-018）` 拆成可认领、可并行、可回写状态的叶子任务。
- 每个叶子任务固定给出：子任务编号、推荐分支名、负责人、具体文件范围、测试/验证项、依赖顺序、风险/阻塞、验收条件。
- 默认负责人采用角色占位：`Backend-1`、`Web-1`、`Miniapp-1`、`Docs-1`、`QA-1`；若为单人执行，则按依赖顺序串行认领。

## 非范围

- `S1.4` 的全局 `profile / honor` 契约统一本身；本文件仅在依赖中引用，不在此替代。
- `S4A ~ S4C` 的字段级权限矩阵、全局审计归档、性能与数据库兼容专项。
- `S5A / S5B` 的正式交付排版、导出与全量文档收口。
- 与 `S3` 无直接关系的 `notice / workflow / report` 任务。

## 依赖总顺序

1. 先冻结 `honor / profile` 在 `S3` 范围内的查询字段、状态口径与前端入参，避免 UI 与接口并行漂移。
2. 先做后端 contract / 状态 / 导出 / 只读边界，再并行推进 `web` 与 `miniapp`。
3. 文档与验收口径任务放在功能链路稳定后执行，避免重复改写。
4. 所有 `S3B` 写操作关闭条件以“非在读严格只读”为最终门槛；所有 `S3A` 展示任务以“历史荣誉与当前荣誉分层清楚”为最终门槛。

## 任务清单

### S3A 荣誉展示（FR-017）

| 状态 | 子任务编号 | 推荐分支名 | 负责人 | 具体文件范围 | 测试 / 验证项 | 依赖顺序 | 风险 / 阻塞 | 验收条件 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [ ] | `S3A.1.a` 荣誉类别与筛选契约冻结 | `codex/s3a-category-contract` | `Backend-1` | `backend/app/honor/router.py`、`backend/app/honor/service.py`、`backend/app/honor/repository.py`、`backend/app/honor/schemas.py` | 补后端集成测试：类别筛选、学年筛选、状态筛选组合查询；校验查询参数与返回字段稳定 | 起点任务；后续 `S3A.1.b`、`S3A.1.c`、`S3A.3.a` 依赖本项 | 类别编码命名与学年口径如果未冻结，UI 会反复返工 | 管理侧与学生侧都能基于同一契约按类别 / 学年取数，`S3A` 查询入参不再漂移 |
| [ ] | `S3A.1.b` 管理端类别维护与筛选接通 | `codex/s3a-web-category-filter` | `Web-1` | `web/src/api/honor.ts`、`web/src/views/honor/HonorList.vue` | 页面联调：类别维护、类别筛选、学年筛选、状态筛选同时可用；构建验证 | 依赖 `S3A.1.a` | 管理端列表与编辑表单信息密度高，易出现筛选栏拥挤或表单回填遗漏 | 管理端可新增 / 维护类别，并在列表页按类别、学年筛选荣誉记录 |
| [ ] | `S3A.1.c` 学生端榜单类别 / 学年筛选接通 | `codex/s3a-miniapp-category-filter` | `Miniapp-1` | `miniapp/src/api/honor.ts`、`miniapp/src/pages/honor/index.vue` | 小程序手测：类别切换、学年筛选、筛选后分页 / 加载更多；构建验证 | 依赖 `S3A.1.a` | 移动端筛选控件空间有限，容易牺牲可读性 | 学生端榜单可稳定按类别、学年切换，且不破坏现有竖版阅读体验 |
| [ ] | `S3A.2.a` 荣誉批量导入后端实现 | `codex/s3a-import-backend` | `Backend-1` | `backend/app/honor/router.py`、`backend/app/honor/service.py`、`backend/app/honor/repository.py`、`backend/app/honor/schemas.py`、`backend/tests/integration/test_honor_flow.py`（新建） | 补后端集成测试：批量导入成功、失败回滚、身份核验失败、重复记录处理 | 可与 `S3A.1.b / S3A.1.c` 并行，但上线前需先于 `S3A.2.b` 完成 | 导入模板字段、重复判定规则、异常行反馈口径如果不提前统一，会阻塞前端入口 | 管理端可一次性导入荣誉记录，且导入后数据可被筛选、查看、归档 |
| [ ] | `S3A.2.b` 管理端批量导入入口与结果反馈 | `codex/s3a-web-import` | `Web-1` | `web/src/api/honor.ts`、`web/src/views/honor/HonorList.vue` | 页面联调：上传、失败提示、成功后列表刷新；构建验证 | 依赖 `S3A.2.a` | 导入反馈过于粗糙会导致人工排查成本高 | 管理端存在可用的荣誉导入入口，导入结果对操作者清晰可见 |
| [ ] | `S3A.3.a` 归档 / 撤销 / 历史展示状态收口 | `codex/s3a-history-status` | `Backend-1` | `backend/app/honor/models.py`、`backend/app/honor/router.py`、`backend/app/honor/service.py`、`backend/app/honor/repository.py`、`backend/tests/integration/test_honor_flow.py`（新建） | 补后端集成测试：归档、撤销、历史列表查询、当前榜单不主动展示历史记录 | 依赖 `S3A.1.a`；先于 `S3A.3.b`、`S3A.3.c` | `归档` 与 `撤销` 业务语义若混用，列表展示与审计口径会冲突 | 后端可稳定区分当前荣誉、历史荣誉、撤销荣誉，并支持前端按状态取数 |
| [ ] | `S3A.3.b` 管理端历史荣誉与状态操作收口 | `codex/s3a-web-history` | `Web-1` | `web/src/api/honor.ts`、`web/src/views/honor/HonorList.vue` | 页面联调：归档、撤销、历史列表过滤、状态标签与原因展示；构建验证 | 依赖 `S3A.3.a` | 状态操作入口过散会增加误操作风险 | 管理端可显式执行归档 / 撤销，并能在列表中区分历史荣誉 |
| [ ] | `S3A.3.c` 学生端历史荣誉查看收口 | `codex/s3a-miniapp-history` | `Miniapp-1` | `miniapp/src/api/honor.ts`、`miniapp/src/pages/honor/index.vue` | 小程序手测：历史入口、历史标识、详情返回榜单；构建验证 | 依赖 `S3A.3.a` | 当前荣誉与历史荣誉边界如果不明显，会影响公示口径 | 学生端可进入历史荣誉视图，历史条目有清晰只读标识，默认不与当前榜单混淆 |
| [ ] | `S3A.4.a` 维护人与更新时间出参收口 | `codex/s3a-maintenance-meta` | `Backend-1` | `backend/app/honor/schemas.py`、`backend/app/honor/service.py`、`backend/app/honor/router.py`、`backend/tests/integration/test_honor_flow.py`（新建） | 补后端集成测试：新增 / 更新 / 归档后返回维护人与更新时间字段稳定 | 依赖 `S3A.2.a`、`S3A.3.a` | 仅返回用户 ID 会降低可读性，显示名映射方式需提前约定 | 荣誉记录在管理侧可回看维护人和最后更新时间，满足留痕要求 |
| [ ] | `S3A.4.b` 管理端留痕信息展示 | `codex/s3a-web-maintenance-meta` | `Web-1` | `web/src/api/honor.ts`、`web/src/views/honor/HonorList.vue` | 页面联调：列表 / 详情可见维护人与更新时间；构建验证 | 依赖 `S3A.4.a` | 信息放置位置不当会挤压主内容 | 管理端可直接查看荣誉记录的维护人与最近更新时间 |
| [ ] | `S3A.5.a` 代表用例与验收口径对齐 | `codex/s3a-doc-acceptance` | `Docs-1` | `docs/source/additional-request.txt`、`docs/notes/current-implementation-plan.md`、`docs/notes/refinements/2026-04-18-s3-honor-profile-refinement.md` | 逐项核对 `S3A` 任务与主计划出口条件；形成可复用验收清单 | 在 `S3A.1` ~ `S3A.4` 完成后执行 | 本次会话限制仅允许改本 refinement；主计划登记与后续文档回写需单独执行 | `S3A` 的代表用例、状态口径、历史展示口径与主计划一致，后续执行人员可直接按本任务树验收 |

### S3B 学生画像（FR-018）

| 状态 | 子任务编号 | 推荐分支名 | 负责人 | 具体文件范围 | 测试 / 验证项 | 依赖顺序 | 风险 / 阻塞 | 验收条件 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [ ] | `S3B.1.a` 管理端画像元数据出参收口 | `codex/s3b-meta-contract` | `Backend-1` | `backend/app/profile/schemas.py`、`backend/app/profile/service.py`、`backend/app/profile/router.py`、`backend/tests/integration/test_profile_flow.py` | 补后端集成测试：管理端可见来源 / 录入人 / 最后更新时间；学生自查看不到管理元数据 | 起点任务；后续 `S3B.1.b`、`S3B.3.a` 依赖本项 | 录入人展示名映射若未统一，前端只能拿到不可读 ID | 管理端画像详情返回来源、录入人、最后更新时间，且不污染学生侧视图 |
| [ ] | `S3B.1.b` 管理端画像元数据展示 | `codex/s3b-web-meta-display` | `Web-1` | `web/src/api/profile.ts`、`web/src/views/profile/StudentProfile.vue` | 页面联调：每条成长事实展示来源 / 录入人 / 最后更新时间；构建验证 | 依赖 `S3B.1.a` | 元数据展示位置不当会影响表格可读性 | 管理端可直接查看每条画像事实的来源、录入人与最后更新时间 |
| [ ] | `S3B.2.a` 导出画像快照后端实现 | `codex/s3b-snapshot-backend` | `Backend-1` | `backend/app/profile/router.py`、`backend/app/profile/service.py`、`backend/app/profile/schemas.py`、`backend/tests/integration/test_profile_flow.py` | 补后端集成测试：授权导出成功、越权导出被拒绝、导出动作留痕 | 依赖 `S3B.1.a` | 快照导出格式未冻结时，前端按钮与验收样例无法稳定 | 授权管理角色可导出单个学生画像快照，且导出行为可审计 |
| [ ] | `S3B.2.b` 管理端导出画像快照入口 | `codex/s3b-web-snapshot` | `Web-1` | `web/src/api/profile.ts`、`web/src/views/profile/StudentProfile.vue` | 页面联调：导出按钮、导出成功反馈、失败提示；构建验证 | 依赖 `S3B.2.a` | 若缺少统一文件命名或下载格式，用户侧体验不稳定 | 管理端页面存在可用的“导出画像快照”入口，并可拿到可交付文件 |
| [ ] | `S3B.3.a` 本人可见与管理元数据隔离回归 | `codex/s3b-self-view-hardening` | `Backend-1` | `backend/app/profile/schemas.py`、`backend/app/profile/service.py`、`backend/app/profile/router.py`、`backend/tests/integration/test_profile_flow.py` | 补后端集成测试：本人仅可看本人、管理元数据不外泄、敏感字段默认隐藏 | 依赖 `S3B.1.a`；可与 `S3B.2.a` 并行 | 共享 schema 容易把管理字段误透传到学生端 | 学生端接口只返回本人可见字段，不暴露来源系统、录入人等管理信息 |
| [ ] | `S3B.3.b` 小程序本人画像展示收口 | `codex/s3b-miniapp-self-view` | `Miniapp-1` | `miniapp/src/api/profile.ts`、`miniapp/src/pages/profile/index.vue` | 小程序手测：本人画像查看、元数据隐藏、异常态提示；构建验证 | 依赖 `S3B.3.a` | 学生端若继续假设管理字段存在，会导致渲染分支混乱 | 小程序仅展示本人画像与本人可见成长记录，不出现管理元数据 |
| [ ] | `S3B.4.a` 纠错申诉与成长补录后端闭环 | `codex/s3b-correction-growth-backend` | `Backend-1` | `backend/app/profile/router.py`、`backend/app/profile/service.py`、`backend/app/profile/repository.py`、`backend/app/profile/schemas.py`、`backend/tests/integration/test_profile_flow.py` | 补后端集成测试：提交申诉、审批通过 / 驳回、补录入库、补录审核、回写画像 | 依赖 `S3B.1.a`；先于 `S3B.4.b`、`S3B.4.c` | “成长补录”由学生发起还是老师补录后审核，若不先定口径会影响接口形态 | 系统可完成“提出纠错 / 成长补录 -> 审核 -> 回写画像或保留驳回原因”的完整链路 |
| [ ] | `S3B.4.b` 管理端纠错处理与成长补录工作台 | `codex/s3b-web-correction-growth` | `Web-1` | `web/src/api/profile.ts`、`web/src/views/profile/StudentProfile.vue` | 页面联调：查看待处理项、审批纠错、录入 / 审核成长记录；构建验证 | 依赖 `S3B.4.a` | 若继续把审批入口分散在不同页面，会影响闭环效率 | 管理端可在画像相关页面完成纠错处理和成长补录闭环 |
| [ ] | `S3B.4.c` 学生端纠错 / 补录入口收口 | `codex/s3b-miniapp-appeal-growth` | `Miniapp-1` | `miniapp/src/api/profile.ts`、`miniapp/src/pages/profile/index.vue` | 小程序手测：提交纠错、查看处理状态、成长补录入口与禁用态；构建验证 | 依赖 `S3B.4.a` | 单页承载申诉与补录，表单复杂度可能过高 | 学生端能发起纠错申诉并看到处理状态；若开放成长补录，则入口与状态反馈完整可用 |
| [ ] | `S3B.5.a` 非在读严格只读与越权留痕后端收口 | `codex/s3b-readonly-audit` | `Backend-1` | `backend/app/profile/router.py`、`backend/app/profile/service.py`、`backend/tests/integration/test_profile_flow.py` | 补后端集成测试：非在读账号写操作一律拒绝、只读查询保留、越权访问记录日志 | 依赖 `S3B.3.a`、`S3B.4.a` | 非在读状态枚举与授权范围如果未统一，拒绝逻辑容易漏口 | 非在读学生只能只读查看本人画像；越权访问和被拒绝写操作都有留痕 |
| [ ] | `S3B.5.b` 管理端非在读只读视觉收口 | `codex/s3b-web-readonly` | `Web-1` | `web/src/views/profile/StudentProfile.vue`、`web/src/api/profile.ts` | 页面联调：非在读提示、编辑按钮禁用 / 隐藏、只读标签与颜色区分；构建验证 | 依赖 `S3B.5.a` | 只做后端拒绝、不做前端视觉降级，会造成误操作体验 | 管理端在查看非在读学生时有明确只读提示，且不会暴露可写入口 |
| [ ] | `S3B.5.c` 学生端非在读只读文案回归 | `codex/s3b-miniapp-readonly` | `Miniapp-1` | `miniapp/src/api/profile.ts`、`miniapp/src/pages/profile/index.vue` | 小程序手测：非在读文案、申诉 / 补录按钮禁用、只读状态一致；构建验证 | 依赖 `S3B.5.a` | 前后端状态文案不一致会导致用户误解 | 学生端在非在读状态下仅保留只读查看，不能继续提交纠错或补录 |

## 建议并行切分

- 并行组 A：`S3A.1.a` 与 `S3B.1.a` 同时启动，先冻结 `honor / profile` 的 `S3` 范围 contract。
- 并行组 B：后端能力项 `S3A.2.a`、`S3A.3.a`、`S3A.4.a`、`S3B.2.a`、`S3B.4.a`、`S3B.5.a` 可由不同后端分支并行，但合并前必须回归 `S3A.1.a`、`S3B.1.a`。
- 并行组 C：对应 UI 项 `S3A.1.b / S3A.1.c`、`S3A.2.b`、`S3A.3.b / S3A.3.c`、`S3B.1.b`、`S3B.2.b`、`S3B.3.b`、`S3B.4.b / S3B.4.c`、`S3B.5.b / S3B.5.c` 在后端接口稳定后并行推进。
- 收口组 D：`S3A.5.a` 最后执行，用于把功能完成状态映射回主计划出口条件。

## 阶段验收条件

- `S3A` 阶段验收：
  - 管理端可完成荣誉类别维护、批量导入、归档 / 撤销、历史荣誉回看。
  - 学生端可按类别 / 学年浏览荣誉榜单，并清晰区分当前荣誉与历史荣誉。
  - 荣誉记录留痕信息可在管理侧回看，且 `S3A` 代表用例与主计划出口条件一致。
- `S3B` 阶段验收：
  - 管理端可查看画像来源、录入人、最后更新时间，并可导出画像快照。
  - 学生端始终只能查看本人画像，且不暴露管理元数据。
  - 纠错申诉与成长补录存在完整闭环；非在读学生严格只读，越权访问可留痕。
- `S3` 总体验收：
  - `S3A.1 ~ S3A.5`、`S3B.1 ~ S3B.5` 均有对应叶子任务完成证据。
  - `honor / profile` 相关前后端改动可按任务树逐项回填状态，不依赖口头说明。
  - 主计划中的 `S3` 出口条件具备可执行、可验证、可追溯的分解路径。

## 风险 / 阻塞

- [!] `docs/notes/current-implementation-plan.md` 的“细化文件登记”表尚未登记本文件；按目录规则后续必须补回写，但本次任务限制为“只改本文件”，因此暂不在本次处理。
- [ ] `S1.4` 的 `profile / honor` 契约若未先收口，`S3A / S3B` 的 `web` 与 `miniapp` 分支会出现重复改口风险。
- [ ] `S3B.2` 的画像快照导出格式、模板与命名规则若未冻结，会阻塞前后端联调与验收。
- [ ] `S3B.4` 的“成长补录”发起方、审批角色与回写策略若未冻结，会影响接口与页面设计边界。
- [ ] `S3B.5` 的“非在读”状态集合若跨模块定义不一致，会造成只读拦截漏口。
- [ ] 若多人并行开发，必须坚持“一叶子任务一分支”，并在合并前先回归本文件依赖顺序。

## 变更记录

- `2026-04-18`：创建文件，按主计划 `S3A / S3B` 输出可执行任务树；本次仅落盘 refinement 文件，未回写主计划登记表。
- `2026-04-19`：标记为被 `2026-04-19-s3-current-state-closure-refinement.md` 覆盖，后续 `S3` 完成态以新文件与主计划为准。
