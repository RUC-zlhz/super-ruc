# 2026-05-29 S67 请假起止日期顺序校验

- 关联主计划条目：`S67.1`, `S67.2`, `S67.3`, `S67.4`, `S67.5`
- 状态：`[x]` 代码修复与全部验证已完成；`2026-06-03` 已在恢复后的本机测试库上补跑 DB 集成回归。

## 背景

互测反馈指出小程序端提交个人请假时，起始日期可以晚于结束日期。当前 `LEAVE_PERSONAL` 的 `form_schema` 只声明了 `start_date` / `end_date` 为必填日期字段，小程序动态表单只校验必填，后端创建、修改和提交申请时也未做跨字段顺序校验。

## 范围

- 小程序事务申请页在保存草稿、保存修改和提交前校验请假起止日期顺序。
- 后端在创建草稿、修改草稿和提交草稿三处兜底校验，防止绕过小程序直接调用 API。
- 保留非请假类型的通用动态表单能力，不把请假专属校验扩散到证明、盖章、报名等类型。

## 执行拆分

- [x] `S67.1` 复核请假类型 schema、Miniapp 动态表单和后端申请服务，确认缺少 `start_date <= end_date` 校验。
- [x] `S67.2` 在小程序申请创建页补请假类型日期顺序校验，提示“请假起始日期不能晚于结束日期”。
- [x] `S67.3` 在后端申请服务补 `_validate_request_form_data`，覆盖创建、修改和提交三个入口。
- [x] `S67.4` 新增不依赖数据库的单元测试和 DB 集成回归用例，锁定逆序日期拒绝。
- [x] `S67.5` 执行验证：静态、编译、单元测试、Miniapp 构建和定向 DB 集成回归均已通过。

## 验证结果

- `uv run --no-sync --extra dev ruff check app/workflow/service.py tests/integration/test_request_flow.py unit_tests/test_request_form_validation.py`：通过。
- `uv run --no-sync --extra dev python -m py_compile app/workflow/service.py tests/integration/test_request_flow.py unit_tests/test_request_form_validation.py`：通过。
- `uv run --no-sync --extra dev pytest unit_tests/test_request_form_validation.py -q -o cache_dir=../.tmp/pytest-cache-s67-unit --basetemp=../.tmp/pytest-tmp-s67-unit`：`3 passed in 1.27s`。
- `.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json`：通过。
- `pnpm -C miniapp build:mp-weixin`：通过，生成物可导入 `dist\build\mp-weixin`。
- `uv run --no-sync --extra dev pytest tests/integration/test_request_flow.py::test_leave_request_rejects_start_date_after_end_date -q -o cache_dir=../.tmp/pytest-cache-s67-leave --basetemp=../.tmp/pytest-tmp-s67-leave`：未通过环境准备，`ConnectionRefusedError: [WinError 1225] 远程计算机拒绝网络连接`，未进入业务断言。
- `2026-06-03` 补充验证：用户确认 Docker 已开启后，已启动 `deploy/docker-compose.yml` 中的 `sip-kingbase`，恢复 `localhost:54322` 测试库；随后执行 `.\.venv\Scripts\python.exe -m pytest tests/integration/test_request_flow.py::test_leave_request_rejects_start_date_after_end_date -q -o cache_dir=../.tmp/pytest-cache-s67-leave-rerun --basetemp=../.tmp/pytest-tmp-s67-leave-rerun`，结果 `1 passed in 12.20s`。

## 结论

请假申请现已在小程序端和后端 API 端同时拒绝“起始日期晚于结束日期”的输入。静态校验、单元测试、Miniapp 构建和定向 DB 集成回归均已通过，`S67` 已正式闭环；`2026-05-29` 当天的 `WinError 1225` 仅保留为历史阻塞事实记录。
