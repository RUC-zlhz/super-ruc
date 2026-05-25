# S37 党团官方流程默认模板修正

- 创建日期：`2026-05-25`
- 状态：`[x]`
- 关联主计划：`S37.1, S37.2, S37.3, S37.4, S37.5`

## 背景

对照仓库内官方资料复核后确认，当前默认党团流程模板是压缩版：党员发展只覆盖少量关键节点，团员发展模板混入了推优入党与毕业团员转出，不足以作为“入党 / 入团流程正确编写”的默认口径。

## 实施内容

- [x] 新增 `PARTY_DEVELOPMENT_OFFICIAL_V2`，按 `data/党团平台官方文件/微信图片_20260427155537.workflow.json` 中 4 阶段 29 步建立默认党员发展模板。
- [x] 新增 `YOUTH_LEAGUE_DEVELOPMENT_OFFICIAL_V2`，按仓库内入团资料的 5 阶段 15 步建立默认发展团员模板。
- [x] 将 `PARTY_DEVELOPMENT_V1` 与 `YOUTH_LEAGUE_V1` 改为 inactive 历史兼容模板，保留旧节点，不删除旧实例可读性。
- [x] 新增 `YOUTH_LEAGUE_MEMBERSHIP_MANAGEMENT_V1`，把“推优入党 / 毕业团员转出”从入团发展主流程拆到团籍管理模板。
- [x] 管理端模板查询返回 inactive 历史模板供查看，学生/公开模板查询和发起入口仍只使用 active 模板。

## 验证

- [x] `uv run --extra dev ruff check scripts/seed/workflow_templates.py app/workflow/router.py app/workflow/service.py app/workflow/repository.py tests/integration/test_workflow_party_flow.py unit_tests/test_workflow_template_specs.py`
- [x] `uv run --extra dev python -m py_compile scripts/seed/workflow_templates.py app/workflow/router.py app/workflow/service.py app/workflow/repository.py tests/integration/test_workflow_party_flow.py unit_tests/test_workflow_template_specs.py`
- [x] `uv run --extra dev pytest unit_tests/test_workflow_template_specs.py -q --basetemp=.tmp/pytest-tmp-workflow-template-specs`，结果 `2 passed`
- [!] `uv run --extra dev pytest tests/integration/test_workflow_party_flow.py -q --basetemp=.tmp/pytest-tmp-workflow-official-v2` 因 `localhost:54322/sip_db_test` 连接拒绝在 fixture setup 阶段失败，当前结果为 `13 errors`，未进入业务断言。

## 当前结论

默认新发起党团流程已切到官方 V2 模板口径；旧 V1 模板和历史实例不删除。待本机测试数据库恢复后，应补跑 `tests/integration/test_workflow_party_flow.py` 验证 V2 发起、节点推进和提醒闭环。
