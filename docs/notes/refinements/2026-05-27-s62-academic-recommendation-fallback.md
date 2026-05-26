# S62 学业缺口课程推荐无开课数据兜底增强

- 日期：`2026-05-27`
- 主计划编号：`S62`
- 状态：`[x]` 已完成

## 背景

生产当前 `course_offerings=0`，学业缺口计算可用，但旧实现只能返回“无本学期开课数据，课程建议暂为空”。这避免了把培养方案课程误说成本学期开课，但对学生和老师仍不够有用。

## 实施范围

- [x] `S62.1` 后端学业缺口推荐保留真实本学期开课优先级，只要 `CourseOffering.is_active=True AND term_code=推荐学期` 命中，就标记为 `CURRENT_TERM_OFFERING`。
- [x] `S62.2` 当推荐学期缺少开课记录时，基于培养方案模块课程清单补充 `CURRICULUM_CANDIDATE` 兜底建议，并明确 `is_current_term_offering=False`。
- [x] `S62.3` 每条建议输出来源、开课状态、容量/先修/冲突等数据限制提示，避免把候选课程当作可选课表。
- [x] `S62.4` Miniapp 与 Web 管理端展示建议来源，区分“本学期开课”和“培养方案候选”。
- [x] `S62.5` 补充并回跑后端定向回归、前端类型检查与构建。

## 边界

- 本轮不伪造 `course_offerings`，不新增默认开课表 seed。
- `CURRICULUM_CANDIDATE` 只表示培养方案中与缺口模块相关的候选课程，不代表当前学期实际开课、容量、时间安排或先修满足。
- 若后续老师导入真实开课表，真实开课建议仍排在培养方案候选之前。

## 验证记录

- 后端静态与编译：`uv run --extra dev ruff check app\report\service.py tests\integration\test_report_contract_flow.py tests\integration\test_s12_gap_closure.py` 通过；`uv run --extra dev python -m py_compile app\report\service.py app\report\schemas.py tests\integration\test_report_contract_flow.py tests\integration\test_s12_gap_closure.py` 通过。
- 后端定向集成：`uv run --extra dev pytest tests\integration\test_report_contract_flow.py tests\integration\test_s12_gap_closure.py -q --basetemp=..\.tmp\pytest-tmp-s62-academic-reco` 结果 `13 passed, 3 warnings in 106.36s`。
- 前端构建：`pnpm -C web build` 通过；`.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json` 通过；`pnpm -C miniapp build:mp-weixin` 通过。

## 当前结论

- 生产 `course_offerings=0` 时，学业缺口页不再只能空白提示，而是返回培养方案候选课程，并明确标记不是本学期开课。
- 导入真实开课表后，`CURRENT_TERM_OFFERING` 仍排在 `CURRICULUM_CANDIDATE` 之前，前端会显示“本学期开课”或“培养方案候选”的来源标签。
