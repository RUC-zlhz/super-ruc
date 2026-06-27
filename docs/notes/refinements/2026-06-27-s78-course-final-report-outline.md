# S78 软件工程导论课程结项汇报提纲

- 关联主计划：`S78.1 ~ S78.5`
- 状态：`[x]` 已完成
- 日期：`2026-06-27`
- 范围：根据当前代码、README、CLAUDE 项目说明、SRS 追踪矩阵、S77 最新验证记录和部署文档，补齐《软件工程导论》课程结项汇报提纲中“能从代码与仓库证据确认”的部分。

## 执行拆分

- [x] `S78.1` 重新读取 `docs/notes/current-implementation-plan.md` 和相关细化文件，确认当前主线已到 `S77`。
- [x] `S78.2` 核对项目入口、技术栈、页面目录、后端路由、测试目录、部署说明与最新验证记录。
- [x] `S78.3` 生成结项汇报提纲 Markdown，保留团队成员、汇报人等仓库无事实来源字段为待填写。
- [x] `S78.4` 新增两张竖版 Mermaid 图源：总体架构图与进度验证闭环图。
- [x] `S78.5` 回写主计划与本细化文件，记录产物路径和剩余人工补充项。

## 产物

- 汇报提纲：`output/doc/软件工程导论课程结项汇报提纲-信息学院学生综合服务与党团管理平台.md`
- 总体架构图源：`docs/source/diagrams/mermaid/course-final-architecture.mmd`
- 进度验证图源：`docs/source/diagrams/mermaid/course-final-progress.mmd`
- 总体架构图 SVG：`docs/source/diagrams/rendered/course-final/course-final-architecture.svg`
- 进度验证图 SVG：`docs/source/diagrams/rendered/course-final/course-final-progress.svg`

## 证据边界

- 功能完成情况以 `docs/srs/traceability-matrix.md`、`docs/notes/current-implementation-plan.md` 和最新 `S77` 验证记录为依据。
- 最新整合验证采用 `S77` 记录：后端全量 `146 passed, 4 warnings`，Web 构建、Miniapp `mp-weixin` 构建、GitHub Actions 部署与生产只读回归通过。
- 团队成员真实姓名、课堂基础需求原表、汇报人、PPT 截图和现场演示账号不在仓库中，未编造，已在提纲中标记为待填写。
- Mermaid SVG 使用 `@mermaid-js/mermaid-cli@10.9.1` 与无 BOM config 渲染；已检查两个 SVG 均包含真实 `<text>` 节点，且不含 `foreignObject/html/div/span`。

## 后续建议

- 若需要提交 Word/PPT 版，可在本 Markdown 基础上按课程模板转写。
- 若老师要求代码行覆盖率，需要额外引入 coverage 工具重新执行测试；当前仓库没有统一代码行覆盖率报告。
