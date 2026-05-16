# S21 默认培养方案重复导入落库修复

- 状态：`[x]` 已完成
- 关联主计划：`S21.1, S21.2, S21.3, S21.4`
- 输入依据：用户反馈 `http://127.0.0.1:5174/academic/curriculum` 仍显示旧培养方案内容。

## 问题

5174 Web 页面读取的是当前后端 `/api/v1/admin/curriculum/plans` 返回的数据库内容，不会直接读取 `docs/source/training program/2024_information.md`。现场库中 6 个 `2024-default` 方案仍是旧数据：总学分为空，模块数为 6/7。

重跑默认培养方案导入时，仓储函数 `set_plan_modules()` 在同一事务中删除旧模块后立即插入新模块，未先 flush 删除操作，导致 Postgres 在插入相同 `(plan_id, module_code)` 时触发 `uq_curriculum_modules_plan_code` 唯一约束，重导入失败，页面因此仍显示旧内容。

## 执行项

- [x] `S21.1` 核对 5174 页面实际数据，确认页面仍显示旧库内容：6 个方案、模块数 6/7、总学分为空。
- [x] `S21.2` 修复 `backend/app/exchange/repository.py` 的 `set_plan_modules()`，改为先删除并 flush 旧模块，再插入新模块，保证覆盖式导入幂等。
- [x] `S21.3` 在 `backend/tests/integration/test_s12_gap_closure.py` 增加二次默认培养方案导入断言，确认重复导入走 `updated_count=7` 且不触发唯一约束。
- [x] `S21.4` 对当前 `localhost:8080` 后端连接的 `sip_db` 重跑默认培养方案导入，并刷新 5174 页面验证新数据可见。

## 验证

- 当前库验证：6 个启用 2024 默认专业方案均为 19 个模块；总学分为计算机科学与技术 `155`、信息管理与信息系统 `153`、软件工程 `156`、信息安全 `155`、数据科学与大数据技术 `155`、数据科学与大数据技术（理学）`153`；另有停用的 `源文件全量课程池`。
- 浏览器验证：`http://127.0.0.1:5174/academic/curriculum` 刷新后显示 `培养方案数 7`、`模块数 19`、专业方案总学分不再为空。
- 后端定向集成：`UV_CACHE_DIR=D:\Codes\super-ruc\.uv-cache-local` 下执行 `uv run pytest tests\integration\test_s12_gap_closure.py -q`，结果 `5 passed in 72.28s`。
- 后端静态校验：`uv run ruff check app\exchange\repository.py app\exchange\default_imports.py tests\integration\test_s12_gap_closure.py` 通过。
- 语法校验：`uv run python -m py_compile app\exchange\repository.py app\exchange\default_imports.py tests\integration\test_s12_gap_closure.py` 通过。

## 结论

页面显示旧内容的根因已修复：旧库数据已被新默认培养方案覆盖，重复导入也具备幂等性，后续通过管理端“导入默认培养方案”不会再因旧模块唯一约束失败。
