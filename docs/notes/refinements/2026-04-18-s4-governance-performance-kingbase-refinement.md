# S4 权限、审计、性能与 Kingbase 兼容执行细化

- 日期：`2026-04-18`
- 关联主计划：`S4A.1, S4A.2, S4A.3, S4B.1, S4B.2, S4B.3, S4C.1, S4C.2, S4C.3`
- 当前状态：`ACTIVE`

> 说明：本文件只负责把主计划中的 S4 拆成可执行任务树。负责人采用“角色占位”，后续执行时需映射到具体成员。受当前会话边界限制，本次仅落盘本细化文件；主计划登记动作需在允许修改 `docs/notes/current-implementation-plan.md` 的后续会话补做。

## 范围

- 将 `S4A/S4B/S4C` 细化到可直接分支执行的子任务层级。
- 为每个子任务明确推荐分支名、负责人、具体文件范围、测试/验证项、依赖顺序、风险/阻塞与验收条件。
- 给出可并行与必须串行的边界，避免多人在同一写集上冲突。

## 非范围

- 不直接实施 S4 代码改动。
- 不回写 `S0 ~ S3`、`S5` 条目。
- 不在本文件中冻结学院最终业务口径；若字段矩阵或 Kingbase 环境条件后续变化，只允许追加更新，不覆盖旧记录。
- 不在本次会话中修改 `docs/notes/current-implementation-plan.md`。

## 并行执行约束

- `S4A.1.x` 与 `S4A.2.x` 可以并行，但不得同时改同一业务模块的 `router/service` 文件；推荐分别使用独立 worktree。
- `S4B.1.x` 与 `S4C.1.x` 不得并行修改同一个 `backend/alembic/versions/*.py` 迁移文件。
- `S4B.3.x` 必须在 `S4B.1.2` 之后执行，否则性能基线会被后续索引变更污染。
- `S4C.1.2` 之前不得合并任何未完成的数据库兼容修补分支；先做兼容盘点，再跑零库迁移。

## 任务清单

### S4A 权限与审计（FR-012 / FR-013 / NFR-001 / NFR-002）

#### S4A.1 明确并落地字段级权限矩阵

- [ ] `S4A.1.1` 冻结字段级权限矩阵基线
  - 推荐分支名：`codex/s4a-field-policy-baseline`
  - 负责人：`治理负责人 + 后端权限负责人`
  - 具体文件范围：`backend/app/audit/models.py`、`backend/app/audit/router.py`、`web/src/views/system/UserManage.vue`、`web/src/utils/permission.ts`
  - 测试/验证项：完成五级角色的字段策略样例；至少覆盖“隐藏 / 脱敏 / 完整可见 / 禁止导出”四类结果；管理端可查询当前策略快照
  - 依赖顺序：无；完成后解锁 `S4A.1.2`、`S4A.3.1`
  - 风险/阻塞：学院最终字段矩阵可能未冻结；角色边界若变化会导致策略表返工
  - 验收条件：形成可直接映射到 `role_field_policies` 的矩阵清单，并能在管理端展示

- [ ] `S4A.1.2` 将字段级权限落到敏感读取与导出链路
  - 推荐分支名：`codex/s4a-sensitive-path-enforcement`
  - 负责人：`后端权限负责人`
  - 具体文件范围：`backend/app/core/dependencies.py`、`backend/app/profile/router.py`、`backend/app/profile/service.py`、`backend/app/exchange/router.py`、`backend/app/notice/router.py`、`backend/app/workflow/router.py`
  - 测试/验证项：学生侧仅能读取本人且脱敏后的画像；未授权角色无法触发学院级导出；通知、事务、画像敏感接口对非授权角色返回 `401/403`
  - 依赖顺序：前置 `S4A.1.1`；可与 `S4A.2.1` 并行；后置 `S4A.3.1`
  - 风险/阻塞：权限逻辑分散在多个模块，容易出现“某条链路补了、另一条链路漏了”的情况
  - 验收条件：敏感字段读取、管理导出、敏感详情访问全部以统一权限口径执行

- [ ] `S4A.1.3` 管理端权限可视化与策略校对闭环
  - 推荐分支名：`codex/s4a-policy-ui-alignment`
  - 负责人：`Web 管理端负责人`
  - 具体文件范围：`web/src/views/system/UserManage.vue`、`web/src/views/audit/AuditLog.vue`、`web/src/api/audit.ts`
  - 测试/验证项：管理端可查看角色策略列表；敏感字段策略与后端实际返回一致；构建通过
  - 依赖顺序：前置 `S4A.1.1`；建议在 `S4A.1.2` 完成后收口
  - 风险/阻塞：前端展示先于后端策略落地会造成“可见但不可用”或“不可见但后端已开放”的错位
  - 验收条件：管理端页面展示的字段策略与后端生效策略一致，且无明显歧义项

#### S4A.2 审批、导入导出、敏感访问、内容发布停用等关键动作全留痕

- [ ] `S4A.2.1` 补齐审批与画像纠错相关审计动作
  - 推荐分支名：`codex/s4a-audit-approval-profile`
  - 负责人：`后端审计负责人`
  - 具体文件范围：`backend/app/workflow/service.py`、`backend/app/profile/service.py`、`backend/app/auth/service.py`、`backend/app/audit/service.py`
  - 测试/验证项：审批通过、驳回、撤回、转线下、画像纠错提交/审批、学籍状态变更均写入审计日志；日志包含操作者、时间、对象、动作、结果
  - 依赖顺序：可直接开始；建议早于 `S4A.3.1`
  - 风险/阻塞：若日志 detail 字段结构不统一，后续查询与归档会难以复用
  - 验收条件：上述关键动作均能在审计查询中检索到完整记录

- [ ] `S4A.2.2` 补齐导入导出、敏感读取、通知发布停用相关审计动作
  - 推荐分支名：`codex/s4a-audit-export-notice`
  - 负责人：`后端审计负责人 + 后端业务模块负责人`
  - 具体文件范围：`backend/app/exchange/router.py`、`backend/app/exchange/service.py`、`backend/app/profile/service.py`、`backend/app/notice/service.py`、`backend/app/audit/service.py`
  - 测试/验证项：导入校验、导入提交、错误报告下载、学生导出/成绩导出/培养方案导出、画像管理端读取、通知发布/归档/发送全部写入日志
  - 依赖顺序：可与 `S4A.2.1` 并行；完成后解锁 `S4A.2.3`、`S4A.3.2`
  - 风险/阻塞：高频读取接口若全部留痕，可能导致日志量快速膨胀
  - 验收条件：FR-013 明确要求的关键动作全部可按对象、人员、时间检索

- [ ] `S4A.2.3` 审计查询口径与字段完整性收口
  - 推荐分支名：`codex/s4a-audit-query-hardening`
  - 负责人：`后端审计负责人 + Web 管理端负责人`
  - 具体文件范围：`backend/app/audit/models.py`、`backend/app/audit/repository.py`、`backend/app/audit/router.py`、`web/src/views/audit/AuditLog.vue`、`web/src/api/audit.ts`
  - 测试/验证项：按时间、对象、人员过滤日志；结果按时间顺序稳定；字段最少包含 actor/time/object/action/result
  - 依赖顺序：前置 `S4A.2.1`、`S4A.2.2`
  - 风险/阻塞：查询字段若与日志 detail 结构不统一，会出现“写得进去但查不出来”
  - 验收条件：授权管理员可稳定完成按时间、对象、人员三种维度检索

#### S4A.3 画像、通知、事务相关敏感路径补权限测试

- [ ] `S4A.3.1` 补画像、通知、事务敏感路径后端权限回归
  - 推荐分支名：`codex/s4a-permission-regression-core`
  - 负责人：`测试负责人`
  - 具体文件范围：`backend/tests/integration/test_profile_flow.py`、`backend/tests/integration/test_notice_flow.py`、`backend/tests/integration/test_request_flow.py`
  - 测试/验证项：匿名 `401`、越权 `403`、学生仅限本人、非在读只读、未授权角色无法读取敏感详情或执行审批/发布/导出
  - 依赖顺序：前置 `S4A.1.2`、`S4A.2.1`
  - 风险/阻塞：现有测试若过度依赖超级管理员账号，可能无法真实暴露角色边界缺口
  - 验收条件：画像、通知、事务三条敏感链路均有正反向权限用例，且全部通过

- [ ] `S4A.3.2` 补导入导出与审计访问控制测试
  - 推荐分支名：`codex/s4a-permission-regression-audit`
  - 负责人：`测试负责人`
  - 具体文件范围：`backend/tests/integration/test_exchange_flow.py`、`backend/tests/integration/test_auth_flow.py`、`backend/tests/integration/test_smoke.py`
  - 测试/验证项：未授权角色无法访问导出与审计接口；授权角色调用后存在对应审计记录；回归用例可在 `uv run pytest` 下稳定执行
  - 依赖顺序：前置 `S4A.2.2`、`S4A.2.3`
  - 风险/阻塞：若测试只校验状态码不校验审计结果，会漏掉“接口拒绝正确但日志缺失”的问题
  - 验收条件：导出与审计访问控制具备完整回归覆盖，且与 S4A.2 审计补点结果一致

### S4B 性能与任务治理（NFR-002 / NFR-003 / NFR-004）

#### S4B.1 增加关键索引

- [ ] `S4B.1.1` 识别性能热点并定义索引迁移清单
  - 推荐分支名：`codex/s4b-index-plan`
  - 负责人：`后端性能负责人`
  - 具体文件范围：`backend/app/audit/models.py`、`backend/app/notice/models.py`、`backend/app/workflow/models.py`、`backend/app/exchange/models.py`、`backend/app/report/service.py`、`backend/alembic/versions/`
  - 测试/验证项：列出审计查询、通知批次/投递、事务列表、导入批次、关键统计查询的索引候选；明确新增索引与对应查询场景
  - 依赖顺序：可与 `S4A.2.3` 并行；完成后解锁 `S4B.1.2`
  - 风险/阻塞：索引过多会拖慢写入；索引不足则无法支撑 NFR-003 响应时间目标
  - 验收条件：形成一份一一对应“查询场景 -> 索引”的迁移清单，且无重复/冲突命名

- [ ] `S4B.1.2` 落地索引迁移并完成回归验证
  - 推荐分支名：`codex/s4b-index-migration`
  - 负责人：`后端性能负责人 + 测试负责人`
  - 具体文件范围：`backend/alembic/versions/`、`backend/tests/integration/test_notice_flow.py`、`backend/tests/integration/test_request_flow.py`、`backend/tests/integration/test_exchange_flow.py`
  - 测试/验证项：`uv run alembic upgrade head` 通过；核心列表与导入流程回归通过；索引迁移可重复执行至干净环境
  - 依赖顺序：前置 `S4B.1.1`
  - 风险/阻塞：同批次若叠加 Kingbase 兼容修复，迁移文件容易冲突
  - 验收条件：索引迁移在零库与已有库上都可执行，且不引入功能回归

#### S4B.2 增加审计归档定时任务，并支持显式开关

- [ ] `S4B.2.1` 建立归档调度入口与运行开关
  - 推荐分支名：`codex/s4b-audit-archive-scheduler`
  - 负责人：`后端基础设施负责人`
  - 具体文件范围：`backend/app/core/config.py`、`backend/app/main.py`、`backend/app/core/`（新增归档调度文件）、`backend/scripts/archive_audit_logs.py`
  - 测试/验证项：开关关闭时应用启动不注册归档任务；开关开启时仅注册一次；支持手工触发归档脚本
  - 依赖顺序：可直接开始；建议早于 `S4B.2.2`
  - 风险/阻塞：多实例部署下若无单实例保护，可能重复归档同一批日志
  - 验收条件：审计归档具备“启用 / 停用 / 手工执行”三种明确运行方式

- [ ] `S4B.2.2` 固化归档运维口径与失败回退路径
  - 推荐分支名：`codex/s4b-audit-archive-ops`
  - 负责人：`后端基础设施负责人 + 运维负责人`
  - 具体文件范围：`backend/README.md`、`docs/notes/refinements/2026-04-18-s4-governance-performance-kingbase-refinement.md`
  - 测试/验证项：文档写明保留周期、手工执行命令、失败排查步骤、禁用场景；执行记录回写到本细化文件
  - 依赖顺序：前置 `S4B.2.1`
  - 风险/阻塞：若只实现代码而未固化运维口径，NFR-002 仍无法作为可交付证据
  - 验收条件：运维人员可在不查代码的前提下完成开启、停用与手工补跑

#### S4B.3 建立导入性能基线并保存记录

- [ ] `S4B.3.1` 建立 100 行标准导入基准测试
  - 推荐分支名：`codex/s4b-import-benchmark`
  - 负责人：`测试负责人 + 后端性能负责人`
  - 具体文件范围：`backend/tests/performance/`（新增性能测试目录）、`backend/tests/conftest.py`、`backend/app/exchange/service.py`
  - 测试/验证项：固定 100 行 Excel 导入样本；记录单次执行耗时、成功/失败结果、错误报告生成耗时；支持 `uv run pytest` 或等价命令运行
  - 依赖顺序：前置 `S4B.1.2`
  - 风险/阻塞：测试环境波动会影响绝对耗时，需要固定样本与执行口径
  - 验收条件：存在可重复执行的导入性能基准，且能直接用于判断 `60s` 门槛

- [ ] `S4B.3.2` 保存性能基线记录并给出是否达标结论
  - 推荐分支名：`codex/s4b-import-baseline-record`
  - 负责人：`测试负责人`
  - 具体文件范围：`docs/notes/refinements/2026-04-18-s4-governance-performance-kingbase-refinement.md`
  - 测试/验证项：记录执行日期、数据规模、环境说明、耗时结果、是否达到 `NFR-003` 门槛；必要时附阻塞项
  - 依赖顺序：前置 `S4B.3.1`
  - 风险/阻塞：没有统一记录格式会导致后续结果不可比较
  - 验收条件：本细化文件中存在可审计的性能基线结果，并能支撑 S4 出口判断

### S4C Kingbase 回归（ICR-004）

#### S4C.1 从零库执行 `alembic upgrade head`

- [ ] `S4C.1.1` 完成 Kingbase 兼容盘点与阻塞清单
  - 推荐分支名：`codex/s4c-kingbase-compat-inventory`
  - 负责人：`DBA/数据库兼容负责人`
  - 具体文件范围：`backend/alembic/env.py`、`backend/alembic/versions/*.py`、`backend/app/core/config.py`、`backend/app/core/database.py`、`backend/app/**/models.py`
  - 测试/验证项：盘点 PostgreSQL 方言特性与潜在兼容点；至少覆盖 JSON 类型、默认值表达式、排序空值处理、大小写模糊查询、索引 DDL
  - 依赖顺序：无；完成后解锁 `S4C.1.2`、`S4C.2.2`
  - 风险/阻塞：若 Kingbase 环境或驱动参数未就绪，盘点结论无法被即时验证
  - 验收条件：形成明确的“兼容 / 待验证 / 明确阻塞”三类清单，并绑定到后续任务

- [ ] `S4C.1.2` 在零库上执行 `alembic upgrade head`
  - 推荐分支名：`codex/s4c-kingbase-upgrade-head`
  - 负责人：`DBA/数据库兼容负责人 + 后端迁移负责人`
  - 具体文件范围：`backend/alembic.ini`、`backend/alembic/env.py`、`backend/app/core/config.py`、`backend/alembic/versions/*.py`
  - 测试/验证项：在空 Kingbase 数据库执行 `uv run alembic upgrade head`；校验 `alembic_version`、主表、索引、历史表全部创建成功
  - 依赖顺序：前置 `S4C.1.1`
  - 风险/阻塞：任何单条迁移脚本的方言不兼容都会阻塞整条 S4C 主路径
  - 验收条件：零库迁移一次通过，且不需要手工改 SQL 或临时跳过版本

#### S4C.2 回归核心 CRUD、批量导入、关键查询

- [ ] `S4C.2.1` 执行核心 CRUD 回归包
  - 推荐分支名：`codex/s4c-kingbase-crud-regression`
  - 负责人：`测试负责人`
  - 具体文件范围：`backend/tests/integration/test_auth_flow.py`、`backend/tests/integration/test_notice_flow.py`、`backend/tests/integration/test_request_flow.py`、`backend/tests/integration/test_profile_flow.py`、`backend/tests/integration/test_workflow_party_flow.py`
  - 测试/验证项：登录、权限校验、通知创建/发布/发送、事务申请/审批、画像读取/纠错、党团流程查询等核心 CRUD 在 Kingbase 环境下通过
  - 依赖顺序：前置 `S4C.1.2`
  - 风险/阻塞：若测试仍默认绑在本地 PostgreSQL，可能无法真实暴露 Kingbase 差异
  - 验收条件：核心 CRUD 用例在 Kingbase 环境可重复跑通，且失败项可定位到具体模块

- [ ] `S4C.2.2` 执行批量导入与关键查询回归包
  - 推荐分支名：`codex/s4c-kingbase-query-import`
  - 负责人：`测试负责人 + 后端性能负责人`
  - 具体文件范围：`backend/tests/integration/test_exchange_flow.py`、`backend/app/exchange/repository.py`、`backend/app/notice/repository.py`、`backend/app/workflow/repository.py`、`backend/app/report/service.py`
  - 测试/验证项：导入校验、整批提交、错误报告下载、事务列表、通知列表、学业缺口与统计查询在 Kingbase 下运行通过
  - 依赖顺序：前置 `S4C.1.1`、`S4C.1.2`；建议在 `S4B.1.2` 后执行
  - 风险/阻塞：排序空值处理、JSON 字段、大小写查询与索引行为可能出现数据库差异
  - 验收条件：导入与关键查询路径无未分类兼容性问题；若失败，必须能复现并归属到具体 SQL/文件

#### S4C.3 记录 Kingbase 兼容性结果与残留风险

- [ ] `S4C.3.1` 回写兼容结论、残留风险与后续动作
  - 推荐分支名：`codex/s4c-kingbase-result-record`
  - 负责人：`DBA/数据库兼容负责人 + 测试负责人`
  - 具体文件范围：`docs/notes/refinements/2026-04-18-s4-governance-performance-kingbase-refinement.md`
  - 测试/验证项：按“通过 / 阻塞 / 风险接受”三类记录 S4C 结果；每个失败项都绑定具体子任务、文件与下一步
  - 依赖顺序：前置 `S4C.2.1`、`S4C.2.2`
  - 风险/阻塞：如果只写“兼容/不兼容”而不写复现条件，后续无法关闭风险
  - 验收条件：本细化文件中存在可审计的 Kingbase 回归结果、阻塞归属与处理建议

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

- [ ] 字段级权限矩阵最终业务口径可能继续变化；执行时只能增量回写，不得覆盖已确认条目。
- [ ] 审计留痕若缺少统一 detail 结构，会直接影响查询、归档与性能治理。
- [ ] 索引迁移与 Kingbase 兼容修复共享 `alembic` 写集，必须严格串行。
- [ ] Kingbase 可用环境、驱动参数与零库权限若未准备完成，会阻塞 `S4C.1.2` 之后的全部任务。
- [!] 按细化规则，本文件应登记到 `docs/notes/current-implementation-plan.md`；但本次会话明确限制只能修改本文件，因此该动作待后续允许时补做。

## 变更记录

- `2026-04-18`：创建文件，完成 `S4A/S4B/S4C` 的可执行任务树拆分。
