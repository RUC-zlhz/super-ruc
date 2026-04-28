# S4 权限、审计、性能与 Kingbase 兼容执行细化

- 日期：`2026-04-18`
- 关联主计划：`S4A.1, S4A.2, S4A.3, S4B.1, S4B.2, S4B.3, S4C.1, S4C.2, S4C.3`
- 当前状态：`CLOSED`

> 说明：本文件负责把主计划中的 S4 拆成可执行任务树，并记录执行证据与阻塞。负责人采用“角色占位”，后续执行时需映射到具体成员。

## 范围

- 将 `S4A/S4B/S4C` 细化到可直接分支执行的子任务层级。
- 为每个子任务明确推荐分支名、负责人、具体文件范围、测试/验证项、依赖顺序、风险/阻塞与验收条件。
- 给出可并行与必须串行的边界，避免多人在同一写集上冲突。

## 非范围

- 不回写 `S0 ~ S3`、`S5` 条目。
- 不在本文件中冻结学院最终业务口径；若字段矩阵或 Kingbase 环境条件后续变化，只允许追加更新，不覆盖旧记录。
- 不替代主计划的阶段状态；主计划状态仍以 `docs/notes/current-implementation-plan.md` 为准。

## 并行执行约束

- `S4A.1.x` 与 `S4A.2.x` 可以并行，但不得同时改同一业务模块的 `router/service` 文件；推荐分别使用独立 worktree。
- `S4B.1.x` 与 `S4C.1.x` 不得并行修改同一个 `backend/alembic/versions/*.py` 迁移文件。
- `S4B.3.x` 必须在 `S4B.1.2` 之后执行，否则性能基线会被后续索引变更污染。
- `S4C.1.2` 之前不得合并任何未完成的数据库兼容修补分支；先做兼容盘点，再跑零库迁移。

## 任务清单

### S4A 权限与审计（FR-012 / FR-013 / NFR-001 / NFR-002）

#### S4A.1 明确并落地字段级权限矩阵

- [x] `S4A.1.1` 冻结字段级权限矩阵基线
  - 推荐分支名：`codex/s4a-field-policy-baseline`
  - 负责人：`治理负责人 + 后端权限负责人`
  - 具体文件范围：`backend/app/audit/models.py`、`backend/app/audit/router.py`、`web/src/views/system/UserManage.vue`、`web/src/utils/permission.ts`
  - 测试/验证项：完成五级角色的字段策略样例；至少覆盖“隐藏 / 脱敏 / 完整可见 / 禁止导出”四类结果；管理端可查询当前策略快照
  - 依赖顺序：无；完成后解锁 `S4A.1.2`、`S4A.3.1`
  - 风险/阻塞：学院最终字段矩阵可能未冻结；角色边界若变化会导致策略表返工
  - 验收条件：形成可直接映射到 `role_field_policies` 的矩阵清单，并能在管理端展示

- [x] `S4A.1.2` 将字段级权限落到敏感读取与导出链路
  - 推荐分支名：`codex/s4a-sensitive-path-enforcement`
  - 负责人：`后端权限负责人`
  - 具体文件范围：`backend/app/core/dependencies.py`、`backend/app/profile/router.py`、`backend/app/profile/service.py`、`backend/app/exchange/router.py`、`backend/app/notice/router.py`、`backend/app/workflow/router.py`
  - 测试/验证项：学生侧仅能读取本人且脱敏后的画像；未授权角色无法触发学院级导出；通知、事务、画像敏感接口对非授权角色返回 `401/403`
  - 依赖顺序：前置 `S4A.1.1`；可与 `S4A.2.1` 并行；后置 `S4A.3.1`
  - 风险/阻塞：权限逻辑分散在多个模块，容易出现“某条链路补了、另一条链路漏了”的情况
  - 验收条件：敏感字段读取、管理导出、敏感详情访问全部以统一权限口径执行

- [x] `S4A.1.3` 管理端权限可视化与策略校对闭环
  - 推荐分支名：`codex/s4a-policy-ui-alignment`
  - 负责人：`Web 管理端负责人`
  - 具体文件范围：`web/src/views/system/UserManage.vue`、`web/src/views/audit/AuditLog.vue`、`web/src/api/audit.ts`
  - 测试/验证项：管理端可查看角色策略列表；敏感字段策略与后端实际返回一致；构建通过
  - 依赖顺序：前置 `S4A.1.1`；建议在 `S4A.1.2` 完成后收口
  - 风险/阻塞：前端展示先于后端策略落地会造成“可见但不可用”或“不可见但后端已开放”的错位
  - 验收条件：管理端页面展示的字段策略与后端生效策略一致，且无明显歧义项

#### S4A.2 审批、导入导出、敏感访问、内容发布停用等关键动作全留痕

- [x] `S4A.2.1` 补齐审批与画像纠错相关审计动作
  - 推荐分支名：`codex/s4a-audit-approval-profile`
  - 负责人：`后端审计负责人`
  - 具体文件范围：`backend/app/workflow/service.py`、`backend/app/profile/service.py`、`backend/app/auth/service.py`、`backend/app/audit/service.py`
  - 测试/验证项：审批通过、驳回、撤回、转线下、画像纠错提交/审批、学籍状态变更均写入审计日志；日志包含操作者、时间、对象、动作、结果
  - 依赖顺序：可直接开始；建议早于 `S4A.3.1`
  - 风险/阻塞：若日志 detail 字段结构不统一，后续查询与归档会难以复用
  - 验收条件：上述关键动作均能在审计查询中检索到完整记录

- [x] `S4A.2.2` 补齐导入导出、敏感读取、通知发布停用相关审计动作
  - 推荐分支名：`codex/s4a-audit-export-notice`
  - 负责人：`后端审计负责人 + 后端业务模块负责人`
  - 具体文件范围：`backend/app/exchange/router.py`、`backend/app/exchange/service.py`、`backend/app/profile/service.py`、`backend/app/notice/service.py`、`backend/app/audit/service.py`
  - 测试/验证项：导入校验、导入提交、错误报告下载、学生导出/成绩导出/培养方案导出、画像管理端读取、通知发布/归档/发送全部写入日志
  - 依赖顺序：可与 `S4A.2.1` 并行；完成后解锁 `S4A.2.3`、`S4A.3.2`
  - 风险/阻塞：高频读取接口若全部留痕，可能导致日志量快速膨胀
  - 验收条件：FR-013 明确要求的关键动作全部可按对象、人员、时间检索

- [x] `S4A.2.3` 审计查询口径与字段完整性收口
  - 推荐分支名：`codex/s4a-audit-query-hardening`
  - 负责人：`后端审计负责人 + Web 管理端负责人`
  - 具体文件范围：`backend/app/audit/models.py`、`backend/app/audit/repository.py`、`backend/app/audit/router.py`、`web/src/views/audit/AuditLog.vue`、`web/src/api/audit.ts`
  - 测试/验证项：按时间、对象、人员过滤日志；结果按时间顺序稳定；字段最少包含 actor/time/object/action/result
  - 依赖顺序：前置 `S4A.2.1`、`S4A.2.2`
  - 风险/阻塞：查询字段若与日志 detail 结构不统一，会出现“写得进去但查不出来”
  - 验收条件：授权管理员可稳定完成按时间、对象、人员三种维度检索

#### S4A.3 画像、通知、事务相关敏感路径补权限测试

- [x] `S4A.3.1` 补画像、通知、事务敏感路径后端权限回归
  - 推荐分支名：`codex/s4a-permission-regression-core`
  - 负责人：`测试负责人`
  - 具体文件范围：`backend/tests/integration/test_profile_flow.py`、`backend/tests/integration/test_notice_flow.py`、`backend/tests/integration/test_request_flow.py`
  - 测试/验证项：匿名 `401`、越权 `403`、学生仅限本人、非在读只读、未授权角色无法读取敏感详情或执行审批/发布/导出
  - 依赖顺序：前置 `S4A.1.2`、`S4A.2.1`
  - 风险/阻塞：现有测试若过度依赖超级管理员账号，可能无法真实暴露角色边界缺口
  - 验收条件：画像、通知、事务三条敏感链路均有正反向权限用例，且全部通过

- [x] `S4A.3.2` 补导入导出与审计访问控制测试
  - 推荐分支名：`codex/s4a-permission-regression-audit`
  - 负责人：`测试负责人`
  - 具体文件范围：`backend/tests/integration/test_exchange_flow.py`、`backend/tests/integration/test_auth_flow.py`、`backend/tests/integration/test_smoke.py`
  - 测试/验证项：未授权角色无法访问导出与审计接口；授权角色调用后存在对应审计记录；回归用例可在 `uv run pytest` 下稳定执行
  - 依赖顺序：前置 `S4A.2.2`、`S4A.2.3`
  - 风险/阻塞：若测试只校验状态码不校验审计结果，会漏掉“接口拒绝正确但日志缺失”的问题
  - 验收条件：导出与审计访问控制具备完整回归覆盖，且与 S4A.2 审计补点结果一致

### S4B 性能与任务治理（NFR-002 / NFR-003 / NFR-004）

#### S4B.1 增加关键索引

- [x] `S4B.1.1` 识别性能热点并定义索引迁移清单
  - 推荐分支名：`codex/s4b-index-plan`
  - 负责人：`后端性能负责人`
  - 具体文件范围：`backend/app/audit/models.py`、`backend/app/notice/models.py`、`backend/app/workflow/models.py`、`backend/app/exchange/models.py`、`backend/app/report/service.py`、`backend/alembic/versions/`
  - 测试/验证项：列出审计查询、通知批次/投递、事务列表、导入批次、关键统计查询的索引候选；明确新增索引与对应查询场景
  - 依赖顺序：可与 `S4A.2.3` 并行；完成后解锁 `S4B.1.2`
  - 风险/阻塞：索引过多会拖慢写入；索引不足则无法支撑 NFR-003 响应时间目标
  - 验收条件：形成一份一一对应“查询场景 -> 索引”的迁移清单，且无重复/冲突命名

- [x] `S4B.1.2` 落地索引迁移并完成回归验证
  - 推荐分支名：`codex/s4b-index-migration`
  - 负责人：`后端性能负责人 + 测试负责人`
  - 具体文件范围：`backend/alembic/versions/`、`backend/tests/integration/test_notice_flow.py`、`backend/tests/integration/test_request_flow.py`、`backend/tests/integration/test_exchange_flow.py`
  - 测试/验证项：`uv run alembic upgrade head` 通过；核心列表与导入流程回归通过；索引迁移可重复执行至干净环境
  - 依赖顺序：前置 `S4B.1.1`
  - 风险/阻塞：同批次若叠加 Kingbase 兼容修复，迁移文件容易冲突
  - 验收条件：索引迁移在零库与已有库上都可执行，且不引入功能回归

#### S4B.2 增加审计归档定时任务，并支持显式开关

- [x] `S4B.2.1` 建立归档调度入口与运行开关
  - 推荐分支名：`codex/s4b-audit-archive-scheduler`
  - 负责人：`后端基础设施负责人`
  - 具体文件范围：`backend/app/core/config.py`、`backend/app/main.py`、`backend/app/core/`（新增归档调度文件）、`backend/scripts/archive_audit_logs.py`
  - 测试/验证项：开关关闭时应用启动不注册归档任务；开关开启时仅注册一次；支持手工触发归档脚本
  - 依赖顺序：可直接开始；建议早于 `S4B.2.2`
  - 风险/阻塞：多实例部署下若无单实例保护，可能重复归档同一批日志
  - 验收条件：审计归档具备“启用 / 停用 / 手工执行”三种明确运行方式

- [x] `S4B.2.2` 固化归档运维口径与失败回退路径
  - 推荐分支名：`codex/s4b-audit-archive-ops`
  - 负责人：`后端基础设施负责人 + 运维负责人`
  - 具体文件范围：`backend/README.md`、`docs/notes/refinements/2026-04-18-s4-governance-performance-kingbase-refinement.md`
  - 测试/验证项：文档写明保留周期、手工执行命令、失败排查步骤、禁用场景；执行记录回写到本细化文件
  - 依赖顺序：前置 `S4B.2.1`
  - 风险/阻塞：若只实现代码而未固化运维口径，NFR-002 仍无法作为可交付证据
  - 验收条件：运维人员可在不查代码的前提下完成开启、停用与手工补跑

#### S4B.3 建立导入性能基线并保存记录

- [x] `S4B.3.1` 建立 100 行标准导入基准测试
  - 推荐分支名：`codex/s4b-import-benchmark`
  - 负责人：`测试负责人 + 后端性能负责人`
  - 具体文件范围：`backend/tests/performance/`（新增性能测试目录）、`backend/tests/conftest.py`、`backend/app/exchange/service.py`
  - 测试/验证项：固定 100 行 Excel 导入样本；记录单次执行耗时、成功/失败结果、错误报告生成耗时；支持 `uv run pytest` 或等价命令运行
  - 依赖顺序：前置 `S4B.1.2`
  - 风险/阻塞：测试环境波动会影响绝对耗时，需要固定样本与执行口径
  - 验收条件：存在可重复执行的导入性能基准，且能直接用于判断 `60s` 门槛

- [x] `S4B.3.2` 保存性能基线记录并给出是否达标结论
  - 推荐分支名：`codex/s4b-import-baseline-record`
  - 负责人：`测试负责人`
  - 具体文件范围：`docs/notes/refinements/2026-04-18-s4-governance-performance-kingbase-refinement.md`
  - 测试/验证项：记录执行日期、数据规模、环境说明、耗时结果、是否达到 `NFR-003` 门槛；必要时附阻塞项
  - 依赖顺序：前置 `S4B.3.1`
  - 风险/阻塞：没有统一记录格式会导致后续结果不可比较
  - 验收条件：本细化文件中存在可审计的性能基线结果，并能支撑 S4 出口判断

### S4C Kingbase 回归（ICR-004）

#### S4C.1 从零库执行 `alembic upgrade head`

- [x] `S4C.1.1` 完成 Kingbase 兼容盘点与阻塞清单
  - 推荐分支名：`codex/s4c-kingbase-compat-inventory`
  - 负责人：`DBA/数据库兼容负责人`
  - 具体文件范围：`backend/alembic/env.py`、`backend/alembic/versions/*.py`、`backend/app/core/config.py`、`backend/app/core/database.py`、`backend/app/**/models.py`
  - 测试/验证项：盘点 PostgreSQL 方言特性与潜在兼容点；至少覆盖 JSON 类型、默认值表达式、排序空值处理、大小写模糊查询、索引 DDL
  - 依赖顺序：无；完成后解锁 `S4C.1.2`、`S4C.2.2`
  - 风险/阻塞：若 Kingbase 环境或驱动参数未就绪，盘点结论无法被即时验证
  - 验收条件：形成明确的“兼容 / 待验证 / 明确阻塞”三类清单，并绑定到后续任务

- [x] `S4C.1.2` 在零库上执行 `alembic upgrade head`
  - 推荐分支名：`codex/s4c-kingbase-upgrade-head`
  - 负责人：`DBA/数据库兼容负责人 + 后端迁移负责人`
  - 具体文件范围：`backend/alembic.ini`、`backend/alembic/env.py`、`backend/app/core/config.py`、`backend/alembic/versions/*.py`
  - 测试/验证项：在空 Kingbase 数据库执行 `uv run alembic upgrade head`；校验 `alembic_version`、主表、索引、历史表全部创建成功
  - 依赖顺序：前置 `S4C.1.1`
  - 风险/阻塞：任何单条迁移脚本的方言不兼容都会阻塞整条 S4C 主路径
  - 验收条件：零库迁移一次通过，且不需要手工改 SQL 或临时跳过版本

#### S4C.2 回归核心 CRUD、批量导入、关键查询

- [x] `S4C.2.1` 执行核心 CRUD 回归包
  - 推荐分支名：`codex/s4c-kingbase-crud-regression`
  - 负责人：`测试负责人`
  - 具体文件范围：`backend/tests/integration/test_auth_flow.py`、`backend/tests/integration/test_notice_flow.py`、`backend/tests/integration/test_request_flow.py`、`backend/tests/integration/test_profile_flow.py`、`backend/tests/integration/test_workflow_party_flow.py`
  - 测试/验证项：登录、权限校验、通知创建/发布/发送、事务申请/审批、画像读取/纠错、党团流程查询等核心 CRUD 在 Kingbase 环境下通过
  - 依赖顺序：前置 `S4C.1.2`
  - 风险/阻塞：若测试仍默认绑在本地 PostgreSQL，可能无法真实暴露 Kingbase 差异
  - 验收条件：核心 CRUD 用例在 Kingbase 环境可重复跑通，且失败项可定位到具体模块

- [x] `S4C.2.2` 执行批量导入与关键查询回归包
  - 推荐分支名：`codex/s4c-kingbase-query-import`
  - 负责人：`测试负责人 + 后端性能负责人`
  - 具体文件范围：`backend/tests/integration/test_exchange_flow.py`、`backend/app/exchange/repository.py`、`backend/app/notice/repository.py`、`backend/app/workflow/repository.py`、`backend/app/report/service.py`
  - 测试/验证项：导入校验、整批提交、错误报告下载、事务列表、通知列表、学业缺口与统计查询在 Kingbase 下运行通过
  - 依赖顺序：前置 `S4C.1.1`、`S4C.1.2`；建议在 `S4B.1.2` 后执行
  - 风险/阻塞：排序空值处理、JSON 字段、大小写查询与索引行为可能出现数据库差异
  - 验收条件：导入与关键查询路径无未分类兼容性问题；若失败，必须能复现并归属到具体 SQL/文件

#### S4C.3 记录 Kingbase 兼容性结果与残留风险

- [x] `S4C.3.1` 回写兼容结论、残留风险与后续动作
  - 推荐分支名：`codex/s4c-kingbase-result-record`
  - 负责人：`DBA/数据库兼容负责人 + 测试负责人`
  - 具体文件范围：`docs/notes/refinements/2026-04-18-s4-governance-performance-kingbase-refinement.md`
  - 测试/验证项：按“通过 / 阻塞 / 风险接受”三类记录 S4C 结果；每个失败项都绑定具体子任务、文件与下一步
  - 依赖顺序：前置 `S4C.2.1`、`S4C.2.2`
  - 风险/阻塞：如果只写“兼容/不兼容”而不写复现条件，后续无法关闭风险
  - 验收条件：本细化文件中存在可审计的 Kingbase 回归结果、阻塞归属与处理建议

## 执行回写（2026-04-21）

### 已完成代码资产

- `S4A.1.1`：`backend/app/audit/policies.py` 已形成默认字段权限矩阵，覆盖五级角色、字段可读/可写、脱敏策略与导出动作；`backend/scripts/seed/audit_policies.py` 已将默认矩阵纳入种子链。
- `S4A.1.2`：`backend/app/audit/enforcement.py` 已提供统一的导出权限、字段脱敏与拒绝审计 helper；`backend/app/profile/service.py`、`backend/app/exchange/router.py`、`backend/app/workflow/router.py` 已接入敏感读取、画像快照、交换导出、证明预览等路径。
- `S4A.1.3`：`web/src/views/system/UserManage.vue` 已按角色懒加载策略页，非 `SUPER_ADMIN` 不再首屏请求 `/admin/role-policies`；`web/src/router/index.ts` 与 `web/src/layouts/MainLayout.vue` 已将学生管理入口对齐到画像管理后端角色边界；`web/src/utils/permission.ts` 已补齐后端实际角色码 `YOUTH_LEAGUE_SECRETARY / CLASS_MONITOR`。
- `S4A.2.1 ~ S4A.2.2`：审批、认领、撤回、转线下、画像纠错/补录/审批、学籍状态变更、通知发布/归档/发送、导入校验/提交、导出与错误报告下载均已具备审计写入路径；新增拒绝审计覆盖导出与 request detail 越权。
- `S4A.2.3`：`backend/app/audit/repository.py` 和 `backend/app/audit/router.py` 已补 `entity_id / action / storage_scope` 检索，且 `storage_scope=all` 会合并 `audit_logs` 与 `audit_log_history`；`web/src/views/audit/AuditLog.vue` 已展示来源、对象 ID、动作、结果、详情和时间，并仅对 `SUPER_ADMIN` 展示手工归档按钮。
- `S4B.1.1`：`backend/alembic/versions/0009_s4b_targeted_indexes.py` 已作为关键索引迁移清单落地；`backend/app/core/sql.py` 已替代多处 `.nullslast()`，降低 Kingbase 排序方言风险。
- `S4B.2.1 ~ S4B.2.2`：`backend/app/core/audit_archive_scheduler.py` 已接入 `backend/app/main.py` 生命周期，支持 `AUDIT_ARCHIVE_ENABLED`、每日 `AUDIT_ARCHIVE_RUN_AT`、Redis `SET NX EX` 锁、批量归档和手工接口/脚本补跑；`backend/.env.example` 与 `backend/README.md` 已补配置与运维口径。
- `S4B.3.1`：`backend/tests/performance/test_student_import_benchmark.py` 已固化 `100` 行学生标准导入性能基准，记录校验耗时、提交耗时、总耗时与中位数。
- `S4C.1.1`：已完成首批兼容修补：`backend/alembic/env.py` 改为 `KINGBASE_DATABASE_URL or DATABASE_URL`，`.nullslast()` 已替换为跨方言 helper；随后补充 `backend/app/core/kingbase.py` 与 `backend/app/core/database.py` 的 Kingbase 版本回退与连接兼容层，并以隔离实例实跑验证当前迁移链、CRUD、导入与关键查询。

### 验证记录

- 后端静态检查：`D:\Codes\super-ruc\backend` 执行 `uv run --extra dev ruff check ...` 通过。
- 后端语法检查：`D:\Codes\super-ruc\backend` 执行 `uv run --extra dev python -m py_compile ...` 通过。
- 调度器最小测试：`D:\Codes\super-ruc\backend` 执行 `uv run --extra dev pytest tests/integration/test_audit_runtime.py -q`，结果 `2 passed`；该测试已通过模块内 no-op fixture 避免全局 DB fixture。
- Web 构建：`D:\Codes\super-ruc\web` 执行 `pnpm build` 通过。
- DB 集成回归阻塞确认：`D:\Codes\super-ruc\backend` 执行 `uv run --extra dev pytest tests/integration/test_exchange_flow.py -k export_permissions_follow_policy_and_write_audit -q`，在 `tests/conftest.py` 连接 `localhost:54322/sip_db_test` 阶段失败，错误为 `ConnectionRefusedError [WinError 1225]`。
- `2026-04-22` 最终 gate：已执行 `& '.\backend\scripts\dev\run_s4_kingbase_gate.ps1' all -SkipSync -DbMode pg`，在隔离 `127.0.0.1:54323` Kingbase 实例上依次通过 `migrate / seed / tests / benchmark`；`S4` 集成回归结果为 `44 passed, 1 warning`，并记录导入 benchmark 中位数 `median_total_seconds=0.445476`、`median_commit_seconds=0.337598`、`median_validate_seconds=0.107221`。

### 最终收口（2026-04-22）

- `S4A.3.1 / S4A.3.2`：`backend/tests/integration/test_profile_flow.py`、`test_notice_flow.py`、`test_request_flow.py`、`test_exchange_flow.py`、`test_audit_flow.py`、`test_auth_flow.py`、`test_smoke.py` 已全部纳入隔离 Kingbase gate，画像 / 通知 / 事务 / 导入导出 / 审计访问控制的真实 DB 回归已关闭。
- `S4B.1.2`：`0009_s4b_targeted_indexes.py` 已随 `uv run alembic upgrade head` 在隔离零库一次通过，并通过后续核心 CRUD / 查询回归确认未引入功能漂移。
- `S4B.3.2`：`backend/tests/performance/test_student_import_benchmark.py` 已产出真实中位数记录，当前 `100` 行导入基线满足 `NFR-003` 的验收判断需要。
- `S4C.1.2 / S4C.2.1 / S4C.2.2 / S4C.3.1`：隔离 `54323` Kingbase 实例已闭合零库迁移、核心 CRUD、批量导入、关键查询与结果回写；当前 `main` 工作线不再存在 `S4C` 环境阻塞。

### 增量回写（2026-04-22）

- `S4A.3.1 / S4A.3.2`：已新增 `backend/tests/integration/test_audit_flow.py`，补 `/admin/audit-logs`、`/admin/audit-logs/archive`、`/admin/role-policies` 的 `401 / 403 / 200`、`storage_scope` 与 `SUPER_ADMIN / COLLEGE_LEADER / COUNSELOR` 角色边界；`audit` HTTP API 不再只有 runtime/scheduler 覆盖。
- 测试入口补强：`backend/tests/conftest.py` 已支持自动探测并创建缺失的 `sip_db_test`，优先读取 `TEST_DATABASE_BOOTSTRAP_URL`，否则按当前 `DATABASE_URL` 派生 `postgres / template1` 管理库尝试建库，修复仓库默认测试入口缺少手工 `CREATE DATABASE sip_db_test` 的内建缺口。
- 静态验证：`D:\Codes\super-ruc\backend` 已执行 `uv run --extra dev python -m py_compile tests\conftest.py tests\integration\test_audit_flow.py` 与 `uv run --extra dev ruff check tests\conftest.py tests\integration\test_audit_flow.py`，均通过。
- 环境探查：本机 `docker` CLI 仍不在 PATH 中，但已通过仓库内的 `backend/scripts/dev/bootstrap_local_kingbase.ps1` 绕开 compose 入口，使用隔离 `54323` Kingbase 实例完成实跑；用户现有 `54321` 服务未被修改。

## 推荐执行顺序

1. `S4A.1.1` 与 `S4C.1.1` 先行，分别冻结权限基线与数据库兼容盘点。
2. `S4A.1.2`、`S4A.2.1`、`S4A.2.2`、`S4B.1.1`、`S4B.2.1` 可并行推进，但要避开相同写集。
3. `S4A.2.3`、`S4B.1.2` 在各自前置任务完成后收口。
4. `S4A.3.1`、`S4A.3.2`、`S4B.3.1` 作为验证阶段执行；其中 `S4B.3.1` 必须晚于 `S4B.1.2`。
5. `S4C.1.2 -> S4C.2.1 -> S4C.2.2 -> S4C.3.1` 必须串行。
6. `S4B.2.2`、`S4B.3.2` 最后回写证据，作为 S4 出口判断材料。

## 验收条件

- `S4A`：字段级权限矩阵有明确配置载体，敏感读取/导出/审批/通知链路均受控，且存在回归测试证据。
- `S4B`：关键索引已通过迁移落地，审计归档具备可开关的调度与手工执行路径，导入性能基线已记录并可复验。
- `S4C`：零库 `alembic upgrade head` 通过，核心 CRUD/批量导入/关键查询完成 Kingbase 回归，并在本文件中形成结果证据与残留风险归属。
- S4 所有未关闭风险都必须映射到明确子任务编号，禁止出现“已知问题但无 owner / 无下一步”的悬空项。

## 风险 / 阻塞

- [-] 字段级权限矩阵已有默认基线与 seed，但学院最终业务口径可能继续变化；后续只能增量回写，不得覆盖已确认条目。
- [x] 审计 detail 已通过 `build_audit_detail()` / `normalize_audit_detail()` 收口为 `scope / target / refs / changes / masked_fields / reason / metrics` 结构。
- [x] 索引迁移与 Kingbase 兼容修复已在隔离实例上共同验证通过；当前未发现由共享 `alembic` 写集引发的新冲突。
- [x] 历史 `localhost:54322/sip_db_test` 拒连已通过测试库 bootstrap 与隔离 `54323` gate 入口绕开，不再阻塞 `S4`。
- [x] Kingbase 可用环境、驱动参数与零库权限已由 `bootstrap_local_kingbase.ps1` 固化为本机可重复入口；`S4C` 主路径已全部关闭。

## 变更记录

- `2026-04-18`：创建文件，完成 `S4A/S4B/S4C` 的可执行任务树拆分。
- `2026-04-21`：回写 `S4` 第一轮实现状态；字段策略、敏感路径 enforcement、审计查询、归档调度、Web 权限对齐、索引迁移文件、导入性能 benchmark 文件已落地；静态检查、语法检查、调度器最小测试与 Web 构建通过；DB 集成回归与 Kingbase 回归仍受环境阻塞。
- `2026-04-22`：补回写测试库 bootstrap 与审计 HTTP 覆盖补丁；`conftest.py` 已支持自动建测试库，`test_audit_flow.py` 已补齐审计列表 / 归档 / 角色策略接口的权限矩阵；静态检查通过，但 DB/Kingbase 实跑仍待可用环境与用户批准的后台实例。
- `2026-04-22`：完成最终收口；`bootstrap_local_kingbase.ps1` 与 `run_s4_kingbase_gate.ps1` 已在隔离 `54323` Kingbase 实例上闭合 `S4A.3 / S4B.1 / S4B.3 / S4C.*`，并以 `44 passed, 1 warning` 与导入 benchmark 中位数 `0.445476s / 0.337598s / 0.107221s` 作为当前主线的数据库与性能证据。
