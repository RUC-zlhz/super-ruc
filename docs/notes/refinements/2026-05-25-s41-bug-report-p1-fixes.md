# S41 bug-report P1 代码修复

- 状态：`[x]` 已完成
- 主计划引用：`docs/notes/current-implementation-plan.md`
- 来源审查：`docs/notes/refinements/2026-05-25-bug-report-production-review.md`
- 日期：`2026-05-25`

## 范围

- [x] `S41.1` 新增统一上传读取 helper，按 chunk 读取 `UploadFile`，超过上限立即返回 `413`。
- [x] `S41.2` 替换现有后端上传入口的直接 `await file.read()`：事务附件、成绩单 PDF、导入中心、知识模板、后台账号导入。
- [x] `S41.3` 修复学业缺口等价课程学分消耗模型，同一条已修成绩只可被一个模块消耗一次。
- [x] `S41.4` 扩展导入日期解析，支持 `YYYY-MM-DD`、`YYYY/MM/DD`、`YYYY年M月D日` 和 ISO datetime。
- [x] `S41.5` 为 `/admin/report/academic-gap` 补 `page/page_size` FastAPI 参数边界。
- [x] `S41.6` 补充上传 helper、日期解析、等价课程消耗和分页参数回归测试。

## 非本轮范围

- `Bug #3 / #11 / #17` 保留为 P2。
- `Bug #8` 排序偏好等待业务确认。
- `Bug #15` 荣誉导入排序等待具体样例确认。
- 本轮不做生产部署。

## 实现记录

- 上传 helper：`backend/app/core/uploads.py`
- 学业缺口修复：`backend/app/report/service.py`
- 日期解析修复：`backend/app/exchange/service.py`
- 分页参数修复：`backend/app/report/router.py`
- 定向测试：`backend/unit_tests/test_uploads.py`、`backend/unit_tests/test_exchange_parse_date.py`、`backend/tests/integration/test_report_contract_flow.py`

## 验证

- `uv run --extra dev ruff check app tests unit_tests`：通过。
- `uv run --extra dev python -m py_compile app\core\uploads.py app\workflow\router.py app\report\router.py app\exchange\router.py app\knowledge\router.py app\admin_users\router.py app\report\service.py app\exchange\service.py unit_tests\test_uploads.py unit_tests\test_exchange_parse_date.py tests\integration\test_report_contract_flow.py`：通过。
- `uv run --extra dev pytest unit_tests/test_uploads.py unit_tests/test_exchange_parse_date.py -q -o cache_dir=.tmp/pytest-cache-s41-unit --basetemp=.tmp/pytest-tmp-s41-unit`：`4 passed`。
- 本机定向集成限制：`uv run --extra dev pytest unit_tests/test_uploads.py unit_tests/test_exchange_parse_date.py tests/integration/test_report_contract_flow.py -q -o cache_dir=.tmp/pytest-cache-s41 --basetemp=.tmp/pytest-tmp-s41` 中，单元测试先通过 `4 passed`，随后 `tests/integration/test_report_contract_flow.py` 在 setup 阶段因本机 `localhost:54322/sip_db_test` 拒连失败，未进入业务断言；同机 `docker ps` 无法连接 Docker Desktop Linux Engine。
- 远程服务器验证：在 `10.10.0.13:/opt/super-ruc/test-runs/s41-p1` 基于生产提交 `a558c61` 建立隔离 worktree，并将本轮变更同步到该 worktree；使用生产后端镜像 `super-ruc-intranet-prod-backend` 执行一轮 `python -m py_compile` 覆盖改动文件，通过。
- 远程业务断言：使用同一后端镜像、生产 Compose 网络 `super-ruc-intranet-prod_default` 和隔离测试库 `sip_db_test_s41` 执行手写断言脚本，覆盖上传 helper 小文件/超限、日期解析、schema 建表与种子、等价课程 credit bucket 只消耗一次、`/api/v1/admin/report/academic-gap` 非法分页返回 `422`；输出 `S41 remote manual assertions passed`，脚本结束后已删除隔离测试库。
