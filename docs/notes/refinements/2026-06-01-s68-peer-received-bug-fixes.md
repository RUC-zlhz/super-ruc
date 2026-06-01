# 2026-06-01 S68 第 12 组收到 bug 复现与代码修复

- 关联主计划条目：`S68.1` ~ `S68.7`
- 状态：`[x]` 已完成
- 输入来源：互测平台 `http://183.174.61.212:8001/bugs/received`，第 12 组账号读取到 6 条 `valid` 反馈。

## 范围

本轮只处理第 12 组收到的 `229 / 218 / 217 / 191 / 160 / 162` 六条反馈，不扩大到其它组或旧版 `bug-report.md` 条目。

## 执行拆分

- [x] `S68.1` 复核互测反馈：6 条均为 `logic / valid / pending`。
- [x] `S68.2` `ID 229`：Miniapp 通知列表、通知详情、首页通知卡片改用 `Asia/Shanghai` 时间格式化，不再直接截取 UTC ISO 字符串。
- [x] `S68.3` `ID 218`：Miniapp 模板下载优先调用 `/knowledge/templates/{id}/file`，失败后回退 `/download` 的预签名链接；下载成功但端侧无法预览时提示“已下载，当前设备暂无法打开”。
- [x] `S68.4` `ID 217`：新增后端集成回归，覆盖“来源带实际 URL + 新增知识条目保存为草稿”；当前 HEAD 不复现服务器内部错误，回归已通过。
- [x] `S68.5` `ID 191`：Web 学生画像 PDF/XLSX 快照下载补齐 403/404/5xx/网络错误提示，不再表现为按钮无反应。
- [x] `S68.6` `ID 160`：培养方案课程明细展开时，0 门课程显示稳定空态和新增课程入口，不再渲染空表格造成页面拉长。
- [x] `S68.7` `ID 162`：请假起止日期顺序问题已由 `S67` 覆盖，本轮复核并保留回归入口。

## 复现结论

- `ID 229`：当前 Miniapp 代码直接 `slice(0, 16).replace('T', ' ')`，可解释 Web 22:25 / 小程序 14:25 的 UTC 展示偏差，已修复。
- `ID 218`：已有文件流接口，但端侧此前只走单一路径；本轮增加 fallback 与提示区分。
- `ID 217`：当前 HEAD 可保存带 URL 来源的知识草稿，按“不复现但补回归”处理；定向集成回归已通过。
- `ID 191`：后端已有快照导出回归，Web 侧失败反馈不足，本轮修复前端错误显式化。
- `ID 160`：当前 Web 会对空课程数组渲染展开表格，本轮改为空态。
- `ID 162`：`S67` 已实现小程序端和后端兜底校验，本轮不重复改逻辑。

## 验证结果

- [x] 后端静态：`uv run --no-sync --extra dev ruff check app/knowledge tests/integration/test_knowledge_flow.py tests/integration/test_knowledge_template_flow.py tests/integration/test_profile_flow.py tests/integration/test_request_flow.py` 通过。
- [x] 后端编译：`uv run --no-sync --extra dev python -m py_compile app/knowledge/router.py app/knowledge/service.py app/core/storage.py tests/integration/test_knowledge_flow.py tests/integration/test_knowledge_template_flow.py tests/integration/test_profile_flow.py tests/integration/test_request_flow.py` 通过。
- [x] Miniapp 类型检查：`.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json` 通过。
- [x] Web 构建：`pnpm -C web build` 通过。
- [x] Miniapp 构建：`pnpm -C miniapp build:mp-weixin` 通过。
- [x] 后端定向集成：启动本地 `deploy/docker-compose.yml` 后，`uv run --no-sync --extra dev pytest tests/integration/test_knowledge_flow.py::test_admin_create_draft_entry_with_url_source tests/integration/test_knowledge_template_flow.py::test_student_template_list_and_download_after_publish tests/integration/test_profile_flow.py::test_profile_read_only_student_and_snapshot_exports tests/integration/test_request_flow.py::test_leave_request_rejects_start_date_after_end_date -q -o cache_dir=../.tmp/pytest-cache-s68 --basetemp=../.tmp/pytest-tmp-s68` 通过，结果 `4 passed in 76.87s`。
