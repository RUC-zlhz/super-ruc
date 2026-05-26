# 信息学院学生综合服务与党团管理平台 - 当前 HEAD 测试工程师 Bug 报告

- 测试日期：2026-05-26
- 测试对象：当前 HEAD `0374c2e`（`main`）
- 测试工程师：Codex
- 测试范围：后端、Web 管理端、Miniapp 学生端、生产只读 smoke

## 评分口径

- 崩溃类 bug：程序无法启动、运行中崩溃、异常退出、无响应、服务中断、页面白屏等；基础分 `15`。
- Logic bug：程序可以运行，但输出结果、功能行为、业务逻辑、边界输入或异常输入处理与预期不一致；基础分 `8`。

## 本轮验证结果

- 后端静态检查：`uv run --extra dev ruff check app tests unit_tests scripts` 通过。
- 后端编译检查：`uv run --extra dev python -m compileall -q app tests unit_tests scripts` 通过。
- 后端全量测试：`uv run --extra dev pytest -q -o cache_dir=../.tmp/pytest-cache-s50-full --basetemp=../.tmp/pytest-tmp-s50-full` 通过，`143 passed, 3 warnings in 275.89s`。
- Web 管理端构建：`pnpm -C web build` 通过。
- Miniapp 类型检查：`.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json` 通过。
- Miniapp 微信小程序构建：`pnpm -C miniapp build:mp-weixin` 通过。
- Miniapp 风险残留扫描：`request-badge / uni-popup / wx_test_appid / utils/async / DORM / 宿 / resolveComponent` 均无命中。
- 生产只读 smoke：`http://10.10.0.13/healthz` 与 `/api/v1/knowledge/search?page=1&page_size=5` 返回 `200`；需登录接口 `/api/v1/honors`、`/api/v1/workflow/public/templates` 返回 `401`，符合认证边界。

## 缺陷汇总

- 崩溃类 bug：`0` 个，基础分 `0`。
- Logic bug：`14` 个，基础分 `112`。
- 本轮基础分合计：`112`。

## 崩溃类 Bug

本轮未发现当前 HEAD 可稳定复现的新增崩溃类 bug。旧版 `bug-report.md` 中的“配置启动失败、数据库不可用、路由死循环、文件上传内存”等条目已在 `S40/S41/S46/S49` 中被生产事实否定或代码修复，不再重复计分。

## Logic Bug

| ID | 分值 | 模块 | 触发条件 | 预期 | 实际与证据 |
|---|---:|---|---|---|---|
| S50-L01 | 8 | 后端认证 | 已登录用户调用 `/api/v1/auth/change-password` 后继续使用修改前的 access token 或 refresh token | 改密后旧 token 应立即失效 | `change_password` 仅更新 `password_hash` 和 `must_change_password`，未递增 `token_version`（`backend/app/auth/service.py:373-385`）；而 access/refresh 校验依赖 token version（`backend/app/core/dependencies.py:67-72`、`backend/app/auth/service.py:482-486`）。结果是旧 access token 仍可访问 `/auth/me`，旧 refresh token 仍可刷新 |
| S50-L02 | 8 | 后端运营看板 | 带 `scope_code` 的辅导员、班主任、党团教师访问 `/api/v1/admin/report/overview` | overview 聚合应只统计其 scope 内学生相关数据 | 路由允许 scoped 角色进入（`backend/app/report/router.py:31-39`），但 `admin_overview` 直接调用无 viewer/scope 参数的 `build_overview`（`backend/app/report/router.py:87-92`、`backend/app/report/service.py:968-979`），请求、通知、流程聚合会按全局统计 |
| S50-L03 | 8 | 后端党团流程发起 | 具备有效 workflow scope 的协同角色，例如 `PARTY_BRANCH_SECRETARY + CLASS:CS2401`，调用 `/api/v1/admin/workflow/students/search` | 该角色既然可发起 scoped workflow，就应能搜索 scope 内学生 | workflow 发起角色包含协同角色（`backend/app/workflow/router.py:80-88`、`backend/app/workflow/service.py:96-102`），但学生搜索转调 profile 搜索（`backend/app/workflow/router.py:324-351`），profile scope 只认辅导员、班主任、党团教师等角色（`backend/app/profile/service.py:55-60`、`:379-382`、`:527`），导致“能发起，不能搜人” |
| S50-L04 | 8 | 后端通知圈人/投递 | 带 scope 的通知编辑角色，例如 `COUNSELOR + CLASS:CS2401`，预览或投递 scope 外班级 | 目标预览和分发都应收口到操作者 scope 内 | 通知编辑角色包含 scoped 教师/协同角色（`backend/app/notice/router.py:48-57`），但预览与分发没有传入 actor scope（`backend/app/notice/router.py:212-226`），目标解析只按 `target_rule` 查询学生（`backend/app/notice/repository.py:151-185`），分发直接使用该结果（`backend/app/notice/service.py:1010`） |
| S50-L05 | 8 | Web 路由默认落点 | 浏览器已有 `sip.access_token`，硬刷新或直接访问 `/` | 应先恢复用户信息，再进入该角色默认首页 | 根路由 redirect 在 `fetchMe()` 前读取 `auth.roleCodes`（`web/src/router/index.ts:42-45`），而恢复会话时 `user=null`、`roleCodes=[]`（`web/src/store/auth.ts:15-20`），因此先落到默认 `/profile`，与 dashboard-capable 角色预期不一致 |
| S50-L06 | 8 | Web 登录态保持 | 刷新受保护页面时 `/auth/me` 临时 500 或网络错误 | 应保留本地 session，并给出重试或错误态 | 路由守卫对 `fetchMe()` 的所有异常都执行 `auth.logout()`（`web/src/router/index.ts:181-187`），`logout()` 会清空 access/refresh token（`web/src/store/auth.ts:48-63`），瞬时服务错误会误退出用户 |
| S50-L07 | 8 | Web 401 重定向 | token 失效后，在 `/approval/123` 或 `/profile/student/1` 触发普通 API 请求或画像快照下载 | 应跳到 `/login?redirect=<current fullPath>`，登录后可回到原页面 | Axios 401 拦截器直接 `location.replace('/login')`（`web/src/utils/request.ts:52-60`），画像 raw fetch 下载也直接跳裸 `/login`（`web/src/api/profile.ts:272-283`、`:327-338`），丢失原始目标路径 |
| S50-L08 | 8 | Web 党团提醒工作台 | token 过期后打开或刷新 `/workflow/party-stage` 的提醒记录/运行记录区域 | 应进入统一登录失效处理 | 提醒 API 使用 raw `fetch` 并自行解析（`web/src/api/workflow.ts:190-217`），没有 401 分支；页面的提醒加载链路没有统一重定向处理（`web/src/views/workflow/PartyStageList.vue:1275`、`:1358-1362`），会停留在 stale/empty 状态 |
| S50-L09 | 8 | Web 通知短信回执 | 在生产管理端打开 SMS 投递行并点击“模拟回执” | 生产 UI 应只显示真实投递状态，或 mock 写入入口必须 dev/test gated | Web 生产页面展示“模拟回执”按钮（`web/src/views/notice/NoticeList.vue:762-769`）和“模拟短信回执”弹窗（`:987-995`），提交会调用 `/admin/notices/deliveries/{id}/receipt/mock`（`:2056-2064`、`web/src/api/notice.ts:251-256`） |
| S50-L10 | 8 | Web 通知详情侧栏 | 选择通知时详情接口或批次接口返回 403/500/网络错误 | 应显示明确加载错误，不应把错误解释成真实业务空态 | `loadSelectedNoticeDetail` 失败后清空 detail（`web/src/views/notice/NoticeList.vue:1460-1470`），`loadSelectedNoticeBatches` 失败后清空 batches（`:1478-1500`）；侧栏随后显示“全体在读学生”“当前通知暂无发送批次”等正常空态文案（`:161-202`），误导操作员 |
| S50-L11 | 8 | Miniapp 首页未读通知统计 | 学生有超过 5 条未读站内通知时进入首页 | 首页“未读通知”应反映真实未读总数，或明确标注“最近 5 条” | 首页只请求 `getMyNotices({ page: 1, size: 5 })`（`miniapp/src/pages/index/index.vue:795-801`），再用这 5 条计算未读数（`:409-410`）和焦点卡片（`:563-571`），第 6 条及之后未读通知被漏计 |
| S50-L12 | 8 | Miniapp 首页待跟进申请统计 | 学生申请总数超过 20，且 `SUBMITTED / IN_REVIEW / REJECTED` 记录落在第 2 页以后 | 首页“待跟进申请”和焦点卡片应覆盖全部待关注申请 | 首页只请求 `getMyRequests({ page: 1, size: 20 })`（`miniapp/src/pages/index/index.vue:803-806`），再本地计算待跟进数（`:412-417`）和最新待关注申请（`:574-585`），第 21 条及之后会被漏掉 |
| S50-L13 | 8 | Miniapp 事务申请列表 | 单状态 tab，例如“已通过”“草稿”“已驳回”，记录数超过 20 | 应支持分页/加载更多，或明确仅展示最近 20 条 | 单状态 tab 固定请求 `page=1,size=20`（`miniapp/src/pages/request/index.vue:325-342`），页面没有加载更多入口，却显示“共 {{ requests.length }} 项”（`:80-87`）并直接渲染当前数组（`:133-188`） |
| S50-L14 | 8 | Miniapp 我的画像历史记录 | 纠错申诉超过 10 条，或成长补录/完整查看申请超过 20 条 | 历史区应支持查看完整记录，或提供分页/剩余数量提示 | `loadAll()` 只拉第一页：纠错 `size=10`、补录 `size=20`、完整查看 `size=20`（`miniapp/src/pages/profile/index.vue:863-889`）；模板直接渲染数组，无分页或加载更多（`:287-350`） |

## 不计分但需关注

- `report/overview` 中 notices/workflows 聚合与 requests 同属一个 scope 缺失根因，本轮只按 `S50-L02` 计一次，避免同根因重复计分。
- 通知管理列表、批次、投递明细也缺少 actor scope 模型迹象；本轮只对已能造成越权投递的 `preview/dispatch` 计分。
- Miniapp “学籍信息”“纠错申诉附件”等入口存在未闭合迹象，但当前需要先确认后端契约和交付范围，暂不作为本轮有效 bug。
- Web 个人信息页“绑定手机 -> 更换”、登录设备“管理”、403“联系管理员”等可见死按钮偏向未完成功能或 UX 缺口，暂不计分。

## 修复优先级建议

- P0：`S50-L01` 改密后旧 token 未失效；`S50-L04` scoped 通知编辑者可越权投递；`S50-L02` scoped 运营看板全局聚合。
- P1：`S50-L03` 协同角色搜人权限不一致；`S50-L07/S50-L08` Web 401 处理不一致；`S50-L09` 生产暴露模拟回执。
- P2：`S50-L05/S50-L06/S50-L10` Web 登录态与错误态；`S50-L11 ~ S50-L14` Miniapp 首页/列表分页截断。

## 旧报告处理结论

2026-05-25 旧版报告中的 `6` 个崩溃类和 `12` 个 Logic 条目不再作为当前 HEAD 的有效计分依据：其中配置守卫、数据库依赖、Mock 生产风险等已由 `S40` 生产事实审查否定；上传读取、等价学分、日期解析、分页参数等已由 `S41` 修复；`S45/S46/S49` 后当前全量测试已恢复到 `143 passed`。本文件是当前 HEAD 的最新测试报告。
