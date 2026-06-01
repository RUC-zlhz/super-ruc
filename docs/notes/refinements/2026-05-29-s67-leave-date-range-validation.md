# 2026-05-29 S67 请假起止日期顺序校验

- 关联主计划条目：`S67.1`, `S67.2`, `S67.3`, `S67.4`, `S67.5`
- 状态：`[!]` 代码修复与可用静态/单元/构建验证已完成；DB 集成测试受本机测试库拒连阻塞。

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
- [!] `S67.5` 执行验证：静态、编译、单元测试和 Miniapp 构建已通过；DB 集成测试因本机测试库拒连未进入业务断言。

## 验证结果

- `uv run --no-sync --extra dev ruff check app/workflow/service.py tests/integration/test_request_flow.py unit_tests/test_request_form_validation.py`：通过。
- `uv run --no-sync --extra dev python -m py_compile app/workflow/service.py tests/integration/test_request_flow.py unit_tests/test_request_form_validation.py`：通过。
- `uv run --no-sync --extra dev pytest unit_tests/test_request_form_validation.py -q -o cache_dir=../.tmp/pytest-cache-s67-unit --basetemp=../.tmp/pytest-tmp-s67-unit`：`3 passed in 1.27s`。
- `.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json`：通过。
- `pnpm -C miniapp build:mp-weixin`：通过，生成物可导入 `dist\build\mp-weixin`。
- `uv run --no-sync --extra dev pytest tests/integration/test_request_flow.py::test_leave_request_rejects_start_date_after_end_date -q -o cache_dir=../.tmp/pytest-cache-s67-leave --basetemp=../.tmp/pytest-tmp-s67-leave`：未通过环境准备，`ConnectionRefusedError: [WinError 1225] 远程计算机拒绝网络连接`，未进入业务断言。

## 结论

请假申请现已在小程序端和后端 API 端同时拒绝“起始日期晚于结束日期”的输入。当前可用验证均已通过；待本机测试数据库恢复后，可直接补跑新增的 DB 集成回归用例。
