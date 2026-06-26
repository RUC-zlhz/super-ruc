# S75 UI/UX 与前后端性能优化

- 归属主计划：`docs/notes/current-implementation-plan.md`
- 状态：`[-]` 进行中（Tier A 本轮落地，Tier B 排期）
- 首次落盘：`2026-06-26`
- 范围：`三端综合按优先级`（web 管理端 + miniapp 学生端 + backend），侧重 `UI/UX 视觉与交互` + `前端运行性能` + `后端接口性能`
- 约束：不得破坏已验收的 `S1 ~ S74` 行为；改动以「行为保持 + 性能/体验增益」为准；遵守 C-03/C-05/C-06/C-07。

## 审计结论（grounded，已对照代码核实）

### 后端
- `app/workflow/service.py:list_admin_workflows` 在分页结果上对每条 `await db.get(Student, ...)` —— 审批工作台列表的 **N+1**（每页 N 条 → N 次额外查询）。
- `app/exchange/service.py:_apply_transcript` 对每行 `await repo.get_student_by_no(...)` —— 成绩单导入的 **N+1**（大批次导入逐行查学生主档）。
- 热点只读路径（knowledge 检索、report overview）暂无 Redis 缓存层（已具备 redis 依赖与连接）。
- 索引：hot filter 列（如 workflow/notice/audit 的状态、时间、scope 列）待系统性核对。

### 前端 web（Vue3 + antdv）
- 路由已懒加载、已 role 守卫，结构良好；但：
  - 无全局加载反馈（请求/路由切换无顶部进度条）。
  - `vite.config` `build` 无 `manualChunks`，vendor 未拆分 → 首屏与缓存命中欠佳。
  - 大表视图（NoticeList 2357 行、UserManage 1747、AuditLog 651 等）无虚拟滚动，长列表渲染压力大。
  - `utils/request.ts` 无 GET 去重 / 路由切换取消。
  - 空态 / 错误态 / 骨架屏无统一组件，各页自行处理。

### 前端 miniapp（微信小程序，权威验收口径 `build:mp-weixin`）
- 列表分页、首屏数据、交互反馈、分包待逐页核对（按 C-08 范围以小程序规范为准）。

## 分层 backlog（按价值/风险排序）

### Tier A — 本轮落地（高价值、低风险、行为保持）
- [x] `S75.1` 后端 N+1 消除：`list_admin_workflows` 学生信息批量加载（repo 新增 `get_students_by_ids`）
- [x] `S75.2` 后端 N+1 消除：`_apply_transcript` 学生主档批量预取（repo 新增 `get_students_by_nos`），保持 C-06 整批原子语义
- [x] `S75.3` 前端全局加载反馈：依赖无关的顶部进度条，联动 axios 拦截器与路由守卫（UX）
- [x] `S75.4` 前端构建分包：`vite` `manualChunks` 拆分 `vue` / `antdv` / `vendor`，改善缓存与首屏

### Tier B — 后续排期
- [x] `S75.5` web 长列表虚拟化：**评估后判定不需要**（所有数据型表格均服务端分页 20~50 行/页；少数 `:pagination=false` 表渲染有界小列表；无逐键 live-search）。强行加 antdv 虚拟滚动需固定行高 + 固定 `:scroll.y`，会破坏现有 `x:'max-content'` 响应式列、回归已调好版式，零收益，故不做。
- [x] `S75.6` web GET 请求去重与路由切换取消（`request.ts`）
- [x] `S75.7` web 统一空态 / 错误态 / 骨架屏组件（`AsyncBoundary` 基元已交付；不强制改造已调好的页面，按需逐页接入）
- [ ] `S75.8` miniapp 首屏与列表分页、交互反馈、分包优化
- [x] `S75.9` 后端热点只读缓存：report overview 加 Redis 缓存（TTL 60s，按 viewer 隔离键，故障降级，测试默认关）
- [x] `S75.10` 后端索引审计：现有 schema 已高度索引，唯一真实缺口 `student_workflows.status` 已补单列索引（model + 迁移 `0021`）

## 验证口径
- 后端：`uv run ruff check`、离线 import smoke；DB 集成回归待本机 Docker / `localhost:54322` 测试库恢复后补跑（与 S74 同一阻塞）。
- web：`pnpm -C web build`（含 `vue-tsc` 类型检查）。
- miniapp：`pnpm -C miniapp build:mp-weixin`。

## 证据

### Tier A（2026-06-26 落地）
- `S75.1`：`app/workflow/repository.py` 新增 `get_students_by_ids`；`list_admin_workflows` 改为每页一次 `IN` 批量取学生，删除循环内 `await db.get(Student, ...)`。审批工作台列表由 `1 + N` 次查询降为 `2` 次（list + students batch；count 另算）。
- `S75.2`：`app/exchange/repository.py` 新增 `get_students_by_nos`；`_apply_transcript` 改为整批一次预取学生主档 dict 后查表，保留「学号不存在即 `BizError` 40044」与 C-06 整批原子提交语义（仅替换读取，不动写入/事务）。
- `S75.3`：新增 `web/src/utils/progress.ts`（无第三方依赖的引用计数顶部进度条），由 `web/src/utils/request.ts` 的 axios 请求/响应/错误三处拦截驱动，覆盖所有接口加载的感知反馈。
- `S75.4`：`web/vite.config.ts` 增加 `build.rollupOptions.output.manualChunks`，拆出 `antdv` / `vue` / `vendor` 三个第三方 chunk。

### 验证
- 后端：`uv run ruff check app/workflow/repository.py app/workflow/service.py app/exchange/repository.py app/exchange/service.py` → `All checks passed`；`uv run python -c "import app.main"` → OK。
- 后端 DB 集成回归：本机 Docker / `localhost:54322` 测试库未运行，**待恢复后补跑**（与 S74 同一阻塞）。改动为「读取批量化 + 行为保持」，无写入/事务语义变化。
- web：`pnpm -C web build` 通过（27.20s）；产物已分出 `antdv-*.js`（981 kB / gzip 285 kB）、`vue-*.js`（107 kB / gzip 42 kB）、`vendor-*.js`（153 kB / gzip 54 kB）独立 chunk，业务代码变更不再使第三方 chunk 缓存失效。

### Tier B 第二批（2026-06-26 续）
- `S75.6`：`web/src/utils/request.ts` 重写——
  - GET 去重：相同 `url + params` 的并发只读请求复用同一在途 promise（`inflightGet` map，底层 raw promise settle 时清理，取消也不残留）。
  - 路由切换取消：仅对 GET 附 `AbortController` 并跟踪，`router.beforeEach` 调 `cancelPendingRequests()` 取消上一页未返回的只读请求；变更类请求（POST/PUT/PATCH/DELETE）不纳入自动取消，写操作不被打断。
  - 取消静默：被取消的请求落到永不 settle 的 `NEVER`，卸载中的组件 `await` 静默挂起，不跑成功分支、不冒 `unhandledrejection`、不弹错误 toast。
  - `web/src/router/index.ts` `beforeEach` 顶部接入 `cancelPendingRequests()`。
- `S75.7`：新增 `web/src/components/AsyncBoundary.vue`——统一「加载/骨架/空态/错误态(可重试)」基元，面向详情/卡片/自定义列表等非 `a-table` 内容区。
  - 设计判断：现有页面（如 `StudentProfile.vue` 区分「部分更新告警 vs 整体失败」）的状态处理往往比通用 wrapper 更细，强行替换会丢失细节并造成回归；故本基元**只新增、不强制改造已调好的页面**，供新页面与按需接入使用。`vue-tsc` 已对其类型检查通过，未被引用故 tree-shake 出包，零运行时成本。

### 验证（第二批）
- web：`pnpm -C web build` 通过（vue-tsc 类型检查 + vite 构建，13.69s）；`vue`/`vendor`/`antdv` 三个第三方 chunk 哈希与上一次构建一致（仅入口 `index` chunk 变化），确认分包确定性与改动局部性。

### Tier B 第三批（2026-06-26 续，本机 Docker 已启）
- 已自行启动 Docker Desktop 并 `docker compose -f deploy/docker-compose.yml up -d`，恢复 `localhost:54322` 测试库，解除 S74/S75 的 DB 集成阻塞。
- `S75.1` / `S75.2` 真实 DB 验证：定向 `pytest test_workflow_party_flow + test_request_flow + test_exchange_flow` → `42 passed, 1 failed`；唯一失败 `test_manual_workflow_reminder_can_force_current_node_before_due` 经 `git stash` 全工作树后在干净 HEAD 上**复现同样失败**，确认为既有缺陷（测试用错 `GET /api/v1/notices`，正确学生端收件箱路由为 `GET /api/v1/notices/inbox`），与 S75 无关，已登记独立修复任务。
- `S75.10` 索引审计结论：models 已大面积建索引（几乎所有 FK `index=True`、status/category/grade-major-class 等热过滤列均有索引，并有 `ix_requests_status_type`、`ix_student_workflows_student_template`、`ix_audit_logs_entity_code_occurred_at` 等合理复合索引）。唯一真实缺口——审批工作台列表 `WHERE status='ACTIVE'` 命中的 `student_workflows.status` 无索引（复合 `(student_id, template_id)` 不服务 status-only 过滤，且本仓库其它 status 列均 `index=True`，属遗漏）。已：
  - `app/workflow/models.py` 给 `status` 加 `index=True`（与 `create_all` / 测试库一致）。
  - 新增迁移 `alembic/versions/0021_s75_student_workflow_status_index.py`（索引名 `ix_student_workflows_status`，与 SQLAlchemy 自动命名一致）。
  - 报表 `academic-gap` 热路径复核：循环均遍历已 `selectinload` 的内存集合，DB 查询为循环外批量 `scalars().all()`，**无 N+1**。

### 验证（第三批）
- 迁移：`alembic upgrade head`（0017→0021）成功，`pg_indexes` 确认 `ix_student_workflows_status` 存在；`downgrade -1` + 再 `upgrade head` 往返干净。
- `uv run ruff check app/workflow/models.py alembic/versions/0021_*.py` → All checks passed。
- 后端全量 `uv run pytest tests/`：`1 failed, 141 passed, 3 warnings in 335.17s`。唯一失败即既有 `test_manual_workflow_reminder_can_force_current_node_before_due`（`/notices` vs `/notices/inbox`，已登记独立任务）。**本轮 S75.1/S75.2/S75.10 改动零回归**，新增 `status` 索引随测试库 `create_all` 生效且全绿。

### S75.8 第一步（2026-06-26，miniapp）
- `miniapp/src/utils/request.ts`：`get()` 增加并发 GET 去重（按完整 URL 复用在途 promise，settle 后清理），消除重复点击 / `onShow` 重复拉取的冗余往返；无需路由取消（小程序模型不同）。
- 验证：`pnpm -C miniapp build:mp-weixin` 通过（Build complete）。
- 暂缓 `lazyCodeLoading: requiredComponents`：该项改变运行时组件加载，需在微信开发者工具做一次性运行时 smoke；当前 devtools automation 受阻（见 S65），故先记录为推荐项，待人工 devtools 验证后再落。

### S75.9（2026-06-26，后端热点 Redis 缓存）
- 新增 `app/core/cache.py`：复用 scheduler 的 `Redis.from_url(decode_responses=True)`，提供 `cache_get_text / cache_set_text / cache_delete_prefix / close_cache`。**核心是故障降级**——任何 Redis 异常都不让业务失败（读失败当未命中直算、写失败静默），并受 `settings.CACHE_ENABLED` 开关短路。
- `app/core/config.py`：新增 `CACHE_ENABLED=True`、`REPORT_OVERVIEW_CACHE_TTL_SECONDS=60`（含 >0 守卫）。
- `app/report/service.py`：`build_overview` 重构为「缓存包装器 + `_build_overview_uncached`」。**安全要点**：概览按 viewer 数据范围过滤，缓存键含 `viewer_user_id`（`report:overview:v1:{uid}:{term}`），绝不跨用户共享，杜绝越权泄露；陈旧度上界 = TTL（60s），看板类聚合可接受；缓存损坏/schema 漂移自动直算覆盖。
- `app/main.py`：lifespan 关闭时 `await close_cache()`。
- `tests/conftest.py`：测试默认 `CACHE_ENABLED=false`，保证「写后即读」断言确定性。
- 失效策略：本轮采用 **TTL-only**（≤60s）。未做事件级失效——概览跨多写路径、且按 viewer 分键，逐路径失效成本/耦合高；如需更强一致，可后续用 `cache_delete_prefix("report:overview:")` 在关键写路径接入（已备好该 helper）。

### 验证（S75.9）
- `uv run ruff check`（cache/config/report/main/test）→ All checks passed；`import app.main` OK。
- 新增 `tests/integration/test_report_overview_cache.py`（monkeypatch 开启缓存）：两次 overview `generated_at` 一致证明命中缓存，`cache_delete_prefix` 后变化证明失效重算。
- `pytest test_report_overview_cache + test_report_contract_flow` → `10 passed`（缓存关闭下既有报表契约测试不受影响）。

### S75.5 评估证据（2026-06-26）
- 大表全部服务端分页：`NoticeList`/`UserManage`/`AuditLog`/`EntryList`/`HonorList`/`PartyStageList` 主表 `pageSize=20`，通知送达记录 `pageSize=50`，导入预检 `pagination={pageSize:10}`——单页 DOM 仅 20~50 行，虚拟化无收益。
- 两处 `:pagination=false`：NoticeList 渲染单条通知的发送批次（有界）、UserManage 渲染导入后新建管理员凭据（有界，一次性展示）——均非大列表。
- 搜索为显式「查询」按钮（`@finish="onSearch"`），无逐键触发请求；仅有的 `watch` 是 tab 切换重载与 blob 清理，非性能问题。
- 结论：web 视图层在路由懒加载 + 服务端分页 + 本轮 S75.3/4/6 之上已具备良好性能，**S75.5 无真实优化对象**，不引入虚拟化以免回归。

## 本轮总结（S75）
- **已完成并各自验证**：`S75.1~S75.4`、`S75.6`、`S75.7`、`S75.9`、`S75.10`；`S75.5` 评估判定不需要；`S75.8` miniapp GET 去重已完成。
- **唯一待外部动作**：`S75.8` 的 `lazyCodeLoading: requiredComponents`——改运行时组件加载，需在微信开发者工具做一次性运行时 smoke（当前 devtools automation 受阻，见 S65），故仅作推荐项，未盲改。
- **可选后续**：`S75.7` 的 `AsyncBoundary` 按需逐页接入（不强制改造已调好页面）；`S75.9` 如需更强一致可在写路径接入 `cache_delete_prefix`；knowledge 检索亦可复用同一缓存基元（未做，避免继续扩面）。
- **既有缺陷（非本轮引入）**：`/notices` vs `/notices/inbox` 测试路径错误，已登记独立修复任务。

## S75 后续优化（2026-06-26 续，用户确认执行）

### 知识库热点缓存 + 写路径事件失效（S75.9 扩展）
- **缓存**（公开已发布内容，非 viewer-scoped，可全局共享）：
  - `GET /knowledge/categories` → `service.list_categories_for_student`，键 `knowledge:categories:v1`（`TypeAdapter(list[CategoryOut])` 序列化）。
  - `GET /knowledge/{id}` → `get_for_student` 包装，键 `knowledge:entry:v1:{id}`，仅缓存已发布条目（未发布仍 `NotFoundError`，不进缓存）。
  - TTL = `KNOWLEDGE_CACHE_TTL_SECONDS`（默认 300s）；缓存损坏自动直查覆盖；故障降级同 `cache.py`。
- **事件级失效**（这是「写路径事件失效」的落地）：新增 `service.invalidate_knowledge_cache()` = `cache_delete_prefix("knowledge:")`，在 4 个条目写函数（create/update/publish/deprecate，统一 commit/refresh 后）与 router 分类 upsert 后调用。知识写操作频率低，整命名空间清空足够简单且保证一致。
- 测试默认关缓存（conftest），新增 `tests/integration/test_knowledge_cache.py`：
  - 条目详情：读→缓存→直改库（绕过 service）→再读仍旧值（**证明命中**）→走 service 更新触发失效→再读新值（**证明写失效**）。
  - 分类：读→命中一致→upsert 新分类→再读含新分类（**证明 upsert 失效**）。
  - `pytest test_knowledge_cache + test_knowledge_flow` → `13 passed`（缓存关闭下既有知识闭环不受影响）。
- ruff + `import app.main` 通过。

### AsyncBoundary 逐页接入：评估后判定不接入（item 1）
- 实际尝试在主要候选页接入，逐一发现**接入即回归**或**无收益**：
  - `Profile.vue`：`user` 来自 auth store（路由守卫 `fetchMe` 预载），`loading` 实际不翻转——无真实异步空白，接入无意义。
  - `StudentProfile.vue`：已区分「部分更新告警 vs 整体失败」，比通用 wrapper 更细，替换会丢细节。
  - `OperationDashboard.vue`：overview/academic-gap 各自独立错误态 + warnings + 生成时间元信息，比通用 wrapper 更细。
  - `QuizBank.vue` 等：`a-table :loading` 自带 loading/空态，无需 wrapper。
- 结论：web 视图层状态处理已普遍精细（表格自管 / store 预载 / 逐页定制），`AsyncBoundary` **强行接入只会回归**。组件保留为「新页面/未来用」的就绪基元（已 vue-tsc 验证、tree-shake 出包，零成本）。

### report overview 失效策略
- 维持 **TTL-only（60s）**：overview 按 viewer 分键、且受请求审批/通知发布/流程推进/导入提交等多模块写影响，逐路径事件失效耦合高、相对 60s TTL 边际收益低。`cache_delete_prefix("report:overview:")` helper 已就绪，如需更强一致可后续接入关键写路径。

### 验证（后续优化）
- `pytest test_knowledge_cache + test_knowledge_flow` → `13 passed`。
- 后端全量回归 `uv run pytest tests/` → `1 failed, 144 passed`（唯一失败仍是既有 `/notices/inbox` 测试缺陷；新增 3 个缓存测试全过，**知识/config 改动零回归**，测试数 141→144）。

## UI/UX 增强（2026-06-26 续，用户要求侧重 UI/UX）

### miniapp 下拉刷新「死代码」激活（真实学生端缺陷）
- 现象：8 个页面已写完整 `onPullDownRefresh`（`await reload()` → `uni.stopPullDownRefresh()`），但 `pages.json` **从未设置 `enablePullDownRefresh`**，微信默认 false ⇒ 下拉刷新永不触发，处理器是死代码。
- 修复：`pages.json` 给这 8 个有处理器的页面（index/workflow.index/workflow.detail/request.index/notice.index/academic.index/progress.index/profile.index）逐页加 `"enablePullDownRefresh": true`；表单/详情等无处理器页不动。`globalStyle` 加 `"backgroundTextStyle": "dark"`，保证浅色背景下下拉 loading 点可见。
- 验证：`pnpm -C miniapp build:mp-weixin` 通过；产物中 8 个 `dist/build/mp-weixin/pages/**/index.json` 均含 `enablePullDownRefresh: true`，app.json 含 `backgroundTextStyle`。

### web 首屏引导态（消除白屏闪烁）
- `web/index.html` 在 `#app` 内内联品牌化 loading（红色 spinner + 文案）+ 内联 `<style>`，在 JS 加载/Vue 挂载前展示；Vue 挂载即替换。perceived-perf 提升，零运行时成本。

### web 无障碍（a11y）
- `theme.scss` 增加 `@media (prefers-reduced-motion: reduce)` 全局重置（弱化过渡/动画/平滑滚动，普通用户无变化），与 `App.vue` 路由过渡兼容。
- `theme.scss` 增加 `:focus-visible` 键盘焦点环（仅键盘聚焦出现，鼠标点击不显示，不影响既有视觉）。

### web 标签标题随路由（导航体验）
- `router/index.ts` `afterEach` 将 `meta.title` 同步到 `document.title`（`{页面} · 信息学院管理后台`）；此前标签页恒为静态标题，现标签/历史/书签可读出当前页。

### 验证（UI/UX）
- `pnpm -C web build` 通过（vue-tsc + vite，vendor chunk 哈希不变，改动局部）；`pnpm -C miniapp build:mp-weixin` 通过并核对产物配置。
