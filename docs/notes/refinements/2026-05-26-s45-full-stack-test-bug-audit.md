# S45 全栈测试与 bug 分级审查

- 日期：`2026-05-26`
- 主计划关联：`S45`
- 当前状态：`[x]` 已完成本轮可测试范围审查
- 任务性质：测试审查与缺陷分级，不直接修复业务代码。

## 测试评分口径

- 崩溃类 bug：程序无法启动、运行中崩溃、异常退出、无响应、服务中断、页面白屏等；基础分 `15`。
- Logic bug：程序可以运行，但输出结果、功能行为、业务逻辑、边界输入或异常输入处理与预期不一致；基础分 `8`。

## 覆盖范围

- [x] `S45.1` 读取主计划、最新细化、现有测试资产和运行入口。
- [x] `S45.2` 后端静态、单元、可行集成测试：认证、师生权限联通、申请/审批/证明、通知、学业、画像、荣誉、导入上传。
- [x] `S45.3` Web 管理端类型检查、构建、路由与关键页面可用性测试。
- [x] `S45.4` Miniapp 学生端类型检查、`mp-weixin` 构建、产物与运行时风险检查。
- [x] `S45.5` 教师管理端与学生端联通闭环审查：通知、事务申请、党团流程、画像/荣誉、学业数据。
- [x] `S45.6` 汇总 bug 候选，按崩溃类 / Logic bug 分类，给出触发条件、预期/实际、证据和基础分。

## 环境与约束

- Windows 本机执行 `uv` 前必须设置 `UV_CACHE_DIR=.uv-cache-local`。
- pytest cache/temp 使用 `.tmp` 下路径。
- 当前本机 Docker Linux Engine 与 `localhost:54322` 测试数据库可用性需先实测；若不可用，集成测试状态必须标记为阻塞而不是误判业务失败。
- 不删除、不覆盖用户现有未提交改动；本轮不改业务实现。

## 执行记录

- `2026-05-26`：已开始读取主计划和最新 `S40 ~ S44` 细化；本机 `docker ps` 暂时无法连接 Docker Desktop Linux Engine，`54322` 端口未监听，后续集成测试可能受环境阻塞。
- `2026-05-26`：已完成本轮可测试范围审查。后端静态、编译和单元测试通过；Web 构建与本地浏览器 smoke 通过；Miniapp 类型检查、`mp-weixin` 构建和产物关键风险扫描通过；生产只读 smoke 通过。
- `2026-05-26` DB 补跑：按用户确认启动 Docker Desktop，`docker ps` 可用；执行 `docker compose -f deploy/docker-compose.yml up -d kingbase` 后 `sip-kingbase` healthy，端口 `54322->5432` 可用；随后运行后端全量 DB 集成测试，结果 `109 passed, 10 failed, 3 warnings in 357.78s`，不再存在测试库连接阻塞。

## 环境阻塞与不计分项

- `docker ps` 无法连接 Docker Desktop Linux Engine；本机 `localhost:54322` 未监听。
- `uv run --extra dev pytest unit_tests -q -o cache_dir=.tmp/pytest-cache-unit --basetemp=.tmp/pytest-tmp-unit` 通过 `10 passed`。
- `uv run --extra dev pytest --collect-only -q ...` 可收集 `134` 条测试。
- 后端 DB 依赖集成测试未进入业务断言：定向 route / auth flow 测试均在 fixture setup 阶段因 `ConnectionRefusedError [WinError 1225]` 连接 `localhost:54322/sip_db_test` 失败。本轮将其记录为环境阻塞，不作为业务 bug 计分。
- 本地后端 `uvicorn` 可启动，`GET /healthz` 返回 `200`；登录类 DB 请求在本机缺少数据库时返回 `500`，归因于测试数据库不可用，不作为业务 bug 计分。
- 未进行真实微信小程序设备联调和真实微信 code 成功登录；仅完成代码、构建产物和可达接口层面的审查。
- DB 补跑后，上述 `54322` 环境阻塞已关闭；全量集成测试失败项见“DB 集成测试补跑发现”。

## 已通过验证

- 后端：
  - `uv --version`：`uv 0.9.26`。
  - `uv run --extra dev ruff check app tests unit_tests scripts`：通过。
  - `uv run --extra dev python -m compileall -q app tests unit_tests scripts`：通过。
  - `uv run --extra dev pytest unit_tests -q ...`：`10 passed`。
- Web 管理端：
  - `pnpm -C web build`：通过。
  - 本地浏览器 smoke：`/login?redirect=/profile`、`/preview/requirements`、`/error/403` 均可渲染且无控制台错误；未登录访问 `/dashboard`、`/profile/student/1` 均重定向到登录页。
- Miniapp 学生端：
  - `vue-tsc --noEmit -p miniapp/tsconfig.json`：通过。
  - `pnpm -C miniapp build:mp-weixin`：通过。
  - 产物存在 `miniapp/dist/build/mp-weixin/app.json` 与 `project.config.json`。
  - `miniapp/src` 与 `miniapp/dist/build/mp-weixin` 未发现 `uni-popup`、`resolveComponent("uni-popup")`、`wx_test_appid`、`utils/async`、`宿`、`DORM` 风险残留。
- 生产只读 smoke：
  - `http://10.10.0.13/healthz` 返回 `200`。
  - `http://10.10.0.13/` 返回 `200` HTML。
  - `http://10.10.0.13/api/v1/knowledge/categories` 返回 `200`。
  - `http://10.10.0.13/api/v1/knowledge/search?page=1&page_size=5` 返回 `200` 且有数据。
  - `/api/v1/honors...` 与 `/api/v1/workflow/public/templates` 未登录返回 `401`，符合需要认证的接口边界。

## 缺陷汇总

- 崩溃类 bug：`1` 个，基础分 `15`。
- Logic bug：`16` 个，基础分 `128`。
- 本轮基础分合计：`143`。

## 崩溃类 bug

| ID | 分值 | 模块 | 触发条件 | 预期 | 实际与证据 |
|---|---:|---|---|---|---|
| S45-C01 | 15 | Web 管理端学生画像 | 前端允许进入 `/profile/student/:studentId`，但画像、纠错或全量查看任一接口返回失败，例如角色被后端拒绝或网络异常 | 页面应显示错误态、403 引导或保留可读空态，不应出现主体不可用 | `web/src/views/profile/StudentProfile.vue:722-735` 使用 `Promise.all` 加载三组接口但没有 `catch`；模板主体在 `profile` 存在时才渲染（`:22-24`）。任一接口失败会导致页面主体空白，符合“页面白屏/功能无法继续执行”口径 |

## Logic bug

| ID | 分值 | 模块 | 触发条件 | 预期 | 实际与证据 |
|---|---:|---|---|---|---|
| S45-L01 | 8 | 微信登录 | 生产 `WECHAT_GUEST_LOGIN_ENABLED=false`，已绑定微信的学生再次一键登录且不重新填写学号 | 已绑定 openid 应可直接登录，首次绑定才要求学号与校验信息 | 后端在查询 openid 前先拒绝无 `student_no` 请求（`backend/app/auth/service.py:200-210`）；小程序文案写明“已绑定微信可直接登录”，但 `onWxLogin` 在无学号时直接 toast 并返回（`miniapp/src/pages/profile/index.vue:814-821`） |
| S45-L02 | 8 | 后端学业看板 | 调用 `/admin/report/academic-gap?risk_level=HIGH` 且结果分页 | `meta.total` 应返回满足该风险等级的总数 | 服务在风险过滤 fallback 中明确返回基础查询总数而非过滤后总数，导致前端分页页码不准（`backend/app/report/service.py:753-755`） |
| S45-L03 | 8 | 后端学业看板权限 | 辅导员、班主任、党团教师查询 `/admin/report/academic-gap` | 应按角色和 `scope_code` 限制学生范围 | 路由只校验角色，不把当前用户或 scope 传入服务（`backend/app/report/router.py:97-115`）；服务仅按 `keyword/grade/major` 过滤学生（`backend/app/report/service.py:690-704`） |
| S45-L04 | 8 | 通知来源抓取 | 管理端配置 `http://127.0.0.1`、`http://localhost` 或内网 IP 作为通知来源 | “公开 URL/RSS”应拒绝本机、私网、环回和 link-local 地址 | `_ensure_public_http_url` 仅校验 scheme 与 netloc（`backend/app/notice/service.py:216-221`），随后 `httpx.AsyncClient().get(source.source_url)` 直接抓取（`:522-524`） |
| S45-L05 | 8 | 事务申请 | 非学生账号或 `student_id=None` 的认证用户调用学生侧 `POST /requests` | 学生侧申请创建应要求绑定学生身份 | `ActiveStudentDep` 对 `student_id is None` 直接放行（`backend/app/core/dependencies.py:105-118`）；`create_draft_request` 会把 `applicant_student_id=None` 落到申请（`backend/app/workflow/service.py:1036-1043`、`:1153-1164`） |
| S45-L06 | 8 | Miniapp 申请列表 | 申请超过 20 条且“待处理”状态分布在第 2 页以后，切换“待处理” tab | 应由后端按 `SUBMITTED/IN_REVIEW` 返回全量分页或前端继续翻页过滤 | “待处理” tab 值是 `SUBMITTED,IN_REVIEW`（`miniapp/src/pages/request/index.vue:218-225`），请求时逗号状态不传给后端且只拉 `size=20`，再本地过滤（`:325-330`），会漏掉后续页待处理申请 |
| S45-L07 | 8 | Miniapp 知识库 | 不输入关键词，仅点击分类或标签 | 应按分类或标签列出知识条目 | 后端支持 `q=None` 且按分类/标签过滤（`backend/app/knowledge/router.py:71-83`、`repository.py:123-155`），但小程序 `onSearch` 在关键词为空时直接返回（`miniapp/src/pages/knowledge/index.vue:291-300`）；分类/标签点击只调用 `onSearch`（`:342-350`） |
| S45-L08 | 8 | Miniapp 知识库 | 搜索接口网络错误、401、500 或解析失败 | 应显示错误态或重试入口 | `onSearch` 先设置已搜索，再在 `catch` 中只把 `results=[]`（`miniapp/src/pages/knowledge/index.vue:291-307`），用户会看到类似“无结果”的状态，无法区分接口错误 |
| S45-L09 | 8 | Miniapp 荣誉公示 | 荣誉列表接口失败或鉴权失败 | 应显示错误态或重试入口 | `reload` 先清空列表，`finally` 只关闭 loading（`miniapp/src/pages/honor/index.vue:353-375`），调用方统一吞掉异常（`:378-410`），模板显示“暂无荣誉记录”（`:114`） |
| S45-L10 | 8 | Miniapp 荣誉公示 | 打开荣誉详情并点击“查看附件” | 应打开真实附件、隐藏按钮或提示当前记录无附件 | 详情页固定展示“查看附件”，点击只显示“附件查看入口已保留，请以后端附件数据为准”（`miniapp/src/pages/honor/index.vue:194`、`:430-431`），属于未闭合功能入口 |
| S45-L11 | 8 | Web 学生画像权限 | `YOUTH_LEAGUE_TEACHER` 或 `PARTY_BUILD_TEACHER` 从菜单/链接进入学生画像 | 前后端角色边界应一致 | 前端 `/profile/student/:studentId` 使用 `SYSTEM_USER_ROLES`，包含党团教师（`web/src/router/index.ts:133-139`、`web/src/utils/permission.ts:67-73`）；后端画像管理角色只允许超管、学院领导、辅导员、班主任（`backend/app/profile/router.py:35-41`） |
| S45-L12 | 8 | Web 运营看板权限 | 辅导员、班主任、党团教师登录管理端 | 后端已允许这些角色访问看板数据时，前端也应提供一致入口 | 后端报表 `_LEADER_ROLES` 包含 `COUNSELOR/HEAD_TEACHER/YOUTH_LEAGUE_TEACHER/PARTY_BUILD_TEACHER`（`backend/app/report/router.py:31-39`），但前端 dashboard 路由和导航只允许 `SUPER_ADMIN/COLLEGE_LEADER`（`web/src/router/index.ts:46-50`、`web/src/config/navigation.ts:40-44`） |
| S45-L13 | 8 | Web 403 可用性 | 非 dashboard 角色进入 403 页后点击“返回首页” | 应返回该角色有权访问的默认页 | 403 页硬编码 `$router.replace('/dashboard')`（`web/src/views/error/Forbidden.vue:13-15`），对无 dashboard 权限角色会再次进入 403，形成错误引导循环 |

## DB 集成测试补跑发现

命令：

```powershell
$env:UV_CACHE_DIR = "D:\Codes\super-ruc\.uv-cache-local"
$env:DATABASE_URL = "postgresql+asyncpg://sip_user:sip_pass_dev@localhost:54322/sip_db_test"
$env:TEST_DATABASE_BOOTSTRAP_URL = "postgresql://sip_user:sip_pass_dev@localhost:54322/sip_db"
uv run --extra dev pytest tests/integration -q -o cache_dir=../.tmp/pytest-cache-s45-db --basetemp=../.tmp/pytest-tmp-s45-db
```

结果：`109 passed, 10 failed, 3 warnings in 357.78s`。

### 新增计分 Logic bug

| ID | 分值 | 模块 | 触发条件 | 预期 | 实际与证据 |
|---|---:|---|---|---|---|
| S45-L14 | 8 | 荣誉管理 | 管理端 PATCH 荣誉记录并替换 `recipients` | 返回的新详情应展示替换后的获奖人/集体成员 | `test_honor_manual_media_recipients_and_empty_guard` 失败：更新后仍返回旧获奖人 `张三`，预期 `示范团队`。代码在同一 session 中删除并插入 recipients 后立刻 `get_record`，可能命中已加载的旧 relationship（`backend/app/honor/service.py:292-318`、`backend/app/honor/repository.py:205-219`） |
| S45-L15 | 8 | 知识匹配接口契约 | `AI_QA_ENABLED=false` 时调用 `/knowledge/ai-match` | 既有 schema/test 契约期望 `engine="keyword"` 或文档同步更新为新值 | `test_ai_match_fallback_to_keyword` 失败：实际返回 `engine="retrieval"`。服务注释称旧接口名保留且当前做检索式匹配（`backend/app/knowledge/service.py:167-218`），但 schema 仍描述 `keyword | claude-haiku`（`backend/app/knowledge/schemas.py:219`），测试与接口契约未统一 |
| S45-L16 | 8 | 工作流范围审计 | 辅导员为范围外学生发起党团流程被拒绝 | 拒绝审计应以稳定结构记录目标学生，便于断言和后续检索 | `test_scoped_launcher_can_start_only_students_in_scope` 失败：`denied_log.detail["student_id"]` 不存在。服务传入扁平 `detail={"student_id": ...}`（`backend/app/workflow/service.py:349-364`），审计归一化会把未知键移动到 `refs`（`backend/app/audit/service.py:146-185`），导致测试和消费方不能按原路径读取 |

### 不计分的测试断言漂移

| 失败测试 | 失败原因 | 判断 |
|---|---|---|
| `test_wechat_subscribe_config_and_authorization_record`、`test_wechat_subscribe_send_records_success_and_failure`、`test_admin_creates_student_updates_master_data_and_unbinds_wechat` | 测试仍期望旧 mock openid `mock_wx_*`，当前实现已按本地 Mock 微信登录稳定性修复改为 `mock_student_{student_no}`（`backend/app/auth/service.py:46-49`） | 测试资产未跟上 `2026-05-19` 已登记实现变更，不作为应用 bug 计分 |
| `test_proof_preview_returns_pdf_stream`、`test_proof_preview_uses_active_template_engine`、`test_proof_preview_requires_active_template`、`test_proof_preview_rejects_other_student` | 测试 monkeypatch 旧函数 `pdf_generator._html_to_pdf_bytes`，当前实现直接调用 `pdf_branding.html_to_pdf_bytes`（`backend/app/workflow/pdf_generator.py:215`） | 测试资产未跟上 `S39` PDF 品牌统一后的函数边界，不作为应用 bug 计分 |

## 建议修复优先级

- P0：先修 `S45-C01`，给学生画像加载增加 `catch`、错误态和按接口失败降级渲染。
- P1：修权限/身份边界类 `S45-L01`、`S45-L03`、`S45-L05`、`S45-L11`、`S45-L12`、`S45-L13`；这些影响教师学生联通、正式登录和后台入口一致性。
- P1：修 DB 集成补跑发现的 `S45-L14` 荣誉更新响应陈旧、`S45-L15` 知识匹配 engine 契约不一致、`S45-L16` 工作流拒绝审计 detail 结构不稳定。
- P1：修安全边界 `S45-L04`，URL 抓取前解析 DNS/IP 并拒绝环回、私网、link-local、保留地址和重定向后的非公网地址。
- P2：修列表和错误态体验 `S45-L02`、`S45-L06`、`S45-L07`、`S45-L08`、`S45-L09`、`S45-L10`。

## 待补验证

- 修复上述业务缺陷和测试断言漂移后，回跑 `uv run --extra dev pytest tests/integration -q -o cache_dir=../.tmp/pytest-cache-s45-db --basetemp=../.tmp/pytest-tmp-s45-db`，目标从当前 `109 passed / 10 failed` 收口到全绿。
- 使用真实微信开发者工具与真实 code 回测 `S45-L01`，确认已绑定学生二次登录路径。
- 使用教师、辅导员、班主任、党团教师、学生账号各一组，做一次教师-学生联通 E2E：通知、申请、党团流程、画像/荣誉、学业看板。

## 修复闭环登记

- `2026-05-26`：本报告中可代码闭环的缺陷已登记到 `S46`，细化文件为 `docs/notes/refinements/2026-05-26-s46-s45-bug-fix-closure.md`。
- 后端全量 DB 集成已从 `109 passed, 10 failed` 收口到 `123 passed, 3 warnings in 231.05s`。
- 真实微信开发者工具 + 真实 code 登录仍属于外部验证项，需在具备真实微信凭证环境时补测。
