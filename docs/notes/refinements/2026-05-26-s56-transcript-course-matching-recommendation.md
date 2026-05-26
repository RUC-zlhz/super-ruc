# S56 成绩单课程匹配推荐与教师审核辅助

- 关联主计划条目：`S56.1, S56.2, S56.3, S56.4`
- 当前状态：`[x]` 已完成首版后端推荐、教师审核页接线与定向验证
- 首次落盘：`2026-05-26`

## 背景

当前成绩单 PDF 上传链路只完成了文本层抽取与候选行生成，教师在审核提交前仍需手工填写 `course_code`。这会导致两类问题：

1. PDF 里能解析出课程名，但没有课程代码时，教师需要人工检索培养方案。
2. 同名或近似课程较多时，缺少系统侧受控推荐，审核效率和一致性较弱。

本轮目标不是做生成式课程认定，也不是在学生上传后自动落正式成绩，而是在教师审核环节提供“可解释、可点击、可覆盖”的推荐辅助。

## 实施范围

- [x] `S56.1` 后端基于受控课程库为 PDF 候选行生成推荐课程代码列表。
- [x] `S56.2` 推荐算法采用确定性规则，不引入生成式 RAG。
- [x] `S56.3` Web 教师审核页支持点击推荐后自动回填课程编码与课程名，并保留手工修改入口。
- [x] `S56.4` 补定向 contract 回归、后端静态校验与 Web 构建验证。

## 实现口径

### 课程库来源

- 优先使用学生自身 `grade_code + major_code` 命中的 active 培养方案。
- 同时补充使用当前仓库已落库的 `2024-default` 信息学院培养方案课程表作为受控参考池。
- 不使用生成式知识补全；推荐只来源于当前数据库中的培养方案课程白名单。

### 匹配策略

- 课程编码精确匹配：若 PDF 已解析出 `course_code` 且命中课程库，直接作为最高优先级推荐。
- 课程名称精确匹配：对课程名做 `NFKC` 归一、空白/常见分隔符清洗后做精确比对。
- 课程名称包含/相似匹配：对课程名做括号内容消歧后，结合包含关系与 `SequenceMatcher` 相似度排序。
- 学分一致性加权：候选学分与课程库学分一致时加分，明显不一致时降权。
- 学生专业/年级命中加权：命中学生当前专业方案或年级方案时优先级更高。

### PDF 解析兼容

- 兼容原有人大成绩单紧凑文本层排版，以及新版“课程名 / 教师 / 课程属性 / 学分 / 成绩 / 绩点”排版。
- 兼容学期汇总行出现在课程块之后的情况；当课程行先出现、学期汇总后出现时，按汇总行回填本段课程的 `term_code`。
- 课程名抽取会剔除教师姓名、课程属性等尾部噪声，避免将 `游泳 刘佳 任选课` 之类的文本误截断为错误课程名。

### 教师审核边界

- 推荐结果只作为审核辅助，不自动写正式成绩。
- 教师仍可直接手填 `course_code`、`course_name`、`credits`、`term_code`。
- 点击推荐仅执行回填，不改变现有“教师提交后才落库”的治理边界。

## 涉及文件

- `backend/app/report/service.py`
- `backend/app/report/schemas.py`
- `backend/app/report/transcript_pdf.py`
- `backend/tests/integration/test_report_contract_flow.py`
- `backend/tests/test_transcript_pdf_analysis.py`
- `web/src/api/exchange.ts`
- `web/src/views/exchange/ImportCenter.vue`

## 验证证据

- 后端静态校验：`py -m uv run --project backend --extra dev ruff check backend/app/report/service.py backend/app/report/schemas.py backend/tests/integration/test_report_contract_flow.py`
- 后端编译校验：`py -m uv run --project backend --extra dev python -m py_compile backend/app/report/service.py backend/app/report/schemas.py backend/tests/integration/test_report_contract_flow.py`
- 定向集成测试：`py -m uv run --project backend --extra dev pytest backend/tests/integration/test_report_contract_flow.py -q -k transcript_pdf --basetemp=.tmp/pytest-tmp-transcript-match`
- 解析器静态校验：`py -m uv run --project backend --extra dev ruff check backend/app/report/transcript_pdf.py backend/tests/test_transcript_pdf_analysis.py`
- 解析器编译校验：`py -m uv run --project backend --extra dev python -m py_compile backend/app/report/transcript_pdf.py backend/tests/test_transcript_pdf_analysis.py`
- 解析器单元测试：`py -m uv run --project backend --extra dev pytest backend/tests/test_transcript_pdf_analysis.py -q --basetemp=.tmp/pytest-tmp-transcript-unit`（`3 passed`）
- Web 类型与构建：`.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p web\tsconfig.json`、`corepack.cmd pnpm -C web build`
- 真实样本复测：将 `D:/大学/校务/毛概/1779807358619.pdf` 复制到 ASCII 路径后，一次直接调用 `analyze_transcript_pdf(...)` 与一次真实 `POST /api/v1/report/transcript-pdf` 上传均返回 `parsed_courses_count=34`；首条候选为 `游泳 / 2024-FALL`，并带出推荐课程 `BCPEQD0003 / 游泳`。
- 教师端可用性补丁：`ImportCenter.vue` 已将成绩单 PDF 批次列表改为“批次号内直出 打开核验 + 整行可点击展开”，不再依赖容易被挤出可视区的最右侧操作列；Web `vue-tsc` 与 `pnpm -C web build` 已通过。

## 当前结论

- 首版已形成“学生上传 PDF -> 后端生成课程推荐 -> 教师点击套用或手工覆盖 -> 审核提交落正式成绩”的闭环。
- 当前方案比 RAG 更适合该场景，因为课程来源、编码和治理边界都要求强约束、可解释、可回归。
- 真实样本 `1779807358619.pdf` 已验证通过：新版人大成绩单排版不再落成 `0 条候选`，现在能稳定识别 `34` 条候选课程，并在可命中的课程上返回受控推荐。
- 教师端入口可见性问题已收口：现在无需横向拖动去找隐藏操作列，直接点击批次行或批次号下方“打开核验”即可看到候选课程表与推荐课程列。
- 后续若继续增强，优先方向应是补课程别名表、历史课程更名映射和教师端按关键词即时重搜，而不是直接引入生成式判定。
