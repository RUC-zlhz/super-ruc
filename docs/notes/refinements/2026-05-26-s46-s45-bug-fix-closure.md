# S46 S45 缺陷修复闭环

- 日期：`2026-05-26`
- 主计划关联：`S46`
- 当前状态：`[x]` 已完成
- 输入依据：`docs/notes/refinements/2026-05-26-s45-full-stack-test-bug-audit.md`

## 范围

- [x] `S46.1` 后端缺陷修复：微信已绑定登录、学生侧身份依赖、学业看板风险 total 与 scope、通知来源 URL 安全、荣誉 recipients 更新响应、知识匹配 engine 契约、工作流拒绝审计结构。
- [x] `S46.2` Web 管理端修复：学生画像加载错误态、画像/看板角色边界、403 返回首页默认落点。
- [x] `S46.3` Miniapp 学生端修复：微信登录留空路径、申请待处理筛选、知识库空关键词分类/标签搜索与错误态、荣誉列表错误态与媒体入口。
- [x] `S46.4` 测试闭环：补新增回归用例，修正 mock openid 与 PDF 生成 monkeypatch 等测试资产漂移，回跑后端全量 DB 集成与双端构建。

## 修复摘要

- 后端：
  - `auth`：访客开关关闭时，已绑定 openid 且已有 `student_id` 的用户可不填学号直接登录。
  - `core.dependencies`：学生侧写操作依赖拒绝 `student_id=None` 的认证用户。
  - `report`：管理端学业缺口列表按当前用户 scope 过滤；`risk_level` 过滤返回精准 `meta.total`；详情读取也复用同一 scope 校验。
  - `notice`：通知抓取来源拒绝本机、内网、保留地址和重定向后的非公网 URL；DNS 可解析到非公网地址时拒绝。
  - `honor`：替换 recipients 时先 flush 删除，再刷新关系，避免 PATCH 响应仍带旧获奖人。
  - `knowledge`：`ai-match` fallback engine 契约收口为 `retrieval`。
  - `workflow`：范围外发起拒绝审计使用稳定 `detail.target` 结构。
- Web：
  - `REPORT_VIEWER_ROLES` 与 `PROFILE_ADMIN_ROLES` 分离，运营看板放开到后端已允许的老师角色，学生画像与后端画像管理角色保持一致。
  - 403 页“返回首页”改为按当前角色计算默认落点，避免无 dashboard 权限角色循环回 403。
  - 学生画像先加载主体，再降级加载辅助信息；失败时显示可重试错误态。
- Miniapp：
  - 生产访客关闭时不再前端拦截空学号登录，交由后端区分“已绑定直接登录”和“未绑定拒绝”。
  - 申请“待处理”按 `SUBMITTED` / `IN_REVIEW` 分别请求后合并排序，避免只取前 20 条再本地过滤漏数。
  - 知识库支持无关键词按分类/标签搜索，并区分接口错误与空结果。
  - 荣誉列表接口失败显示错误态，详情仅在存在媒体 URL 时展示“查看媒体”，并打开图片预览或复制链接。

## 验证记录

- 后端定向 DB 集成：
  - `uv run --extra dev pytest tests/integration/test_auth_flow.py tests/integration/test_report_contract_flow.py tests/integration/test_notice_flow.py tests/integration/test_request_flow.py tests/integration/test_honor_flow.py tests/integration/test_knowledge_flow.py tests/integration/test_profile_flow.py tests/integration/test_workflow_party_flow.py tests/integration/test_s12_gap_closure.py -q -o cache_dir=../.tmp/pytest-cache-s45-target --basetemp=../.tmp/pytest-tmp-s45-target`
  - 结果：`94 passed, 3 warnings in 220.37s`
- 后端全量 DB 集成：
  - `uv run --extra dev pytest tests/integration -q -o cache_dir=../.tmp/pytest-cache-s45-full --basetemp=../.tmp/pytest-tmp-s45-full`
  - 结果：`123 passed, 3 warnings in 231.05s`
- 后端静态与单元：
  - `uv run --extra dev ruff check app tests unit_tests scripts`：通过。
  - `uv run --extra dev python -m compileall -q app tests unit_tests scripts`：通过。
  - `uv run --extra dev pytest unit_tests -q -o cache_dir=../.tmp/pytest-cache-s45-unit --basetemp=../.tmp/pytest-tmp-s45-unit`：`10 passed in 1.11s`
- Web：
  - `pnpm -C web build`：通过。
  - 本地 Vite `http://127.0.0.1:4173/error/403` smoke：403 页渲染、返回首页按钮唯一、点击后落到 `/login?redirect=/profile`，浏览器 error log 为空。
- Miniapp：
  - `.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json`：通过。
  - `pnpm -C miniapp build:mp-weixin`：通过。

## 复核记录

- `2026-05-26` 本轮复核确认 `sip-kingbase` 已由 `deploy/docker-compose.yml` 拉起且处于 healthy；从仓库根目录执行 `docker compose -f deploy/docker-compose.yml up -d kingbase` 后容器保持 Running。
- 后端复核：
  - `uv run --extra dev ruff check app tests unit_tests scripts`：通过。
  - `uv run --extra dev python -m compileall -q app tests unit_tests scripts`：通过。
  - `uv run --extra dev pytest unit_tests -q -o cache_dir=../.tmp/pytest-cache-s46-unit-rerun --basetemp=../.tmp/pytest-tmp-s46-unit-rerun`：`10 passed in 1.06s`。
  - `uv run --extra dev pytest tests/integration -q -o cache_dir=../.tmp/pytest-cache-s46-full-rerun --basetemp=../.tmp/pytest-tmp-s46-full-rerun`：`123 passed, 3 warnings in 205.89s`。
- 双端复核：
  - `pnpm -C web build`：通过。
  - `.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json`：通过。
  - `pnpm -C miniapp build:mp-weixin`：通过。
- 浏览器复核：本地 Vite `http://127.0.0.1:4173/error/403` 可渲染 403 页面，`返回首页` 按钮唯一，点击后落到 `/login?redirect=/profile`，浏览器 error log 为空；截图证据保存为 `.tmp/s46-403-smoke.png`。

## 剩余外部验证

- [!] 真实微信开发者工具 + 真实 code 登录仍需外部微信环境验证；当前自动化已覆盖后端契约和前端拦截逻辑，但无法在本机直接生成真实微信登录凭证。
