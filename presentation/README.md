# 课程结项汇报 presentation 产物说明

本目录整理《软件工程导论》课程结项汇报可直接使用的材料。内容均来自当前仓库代码、文档、测试记录和计划记录，未编造团队姓名、演示账号或截图。

## 文件清单

| 文件 | 用途 |
|---|---|
| `软件工程导论课程结项汇报提纲-信息学院学生综合服务与党团管理平台.md` | 汇报正文提纲，可直接拆成 PPT |
| `source-evidence.md` | 证据来源索引，便于核对功能、测试、部署和工具使用口径 |
| `diagrams/course-final-architecture.mmd` | 总体架构图 Mermaid 源文件 |
| `diagrams/course-final-architecture.svg` | 总体架构图 SVG，可插入 Word/PPT |
| `diagrams/course-final-progress.mmd` | 进度验证闭环 Mermaid 源文件 |
| `diagrams/course-final-progress.svg` | 进度验证闭环 SVG，可插入 Word/PPT |

## 使用建议

1. 先从提纲开头的“汇报页结构建议”拆 PPT。
2. 架构页使用 `diagrams/course-final-architecture.svg`。
3. 进度页使用 `diagrams/course-final-progress.svg`。
4. 测试结果页直接引用 S77：后端全量 `146 passed, 4 warnings in 267.14s`，Web 构建、Miniapp `mp-weixin` 构建、GitHub Actions run `28233332227` 和生产只读回归均通过。

## 仍需人工确认

| 需要确认 | 建议处理 |
|---|---|
| 团队成员、汇报人、日期 | 填到首页和团队分工页 |
| 是否放真实截图/录屏 | 现场网络或账号不稳时，优先使用截图或短录屏 |
| 课堂是否要求沿用老师给的基础需求原编号 | 若要求，将提纲中的 `FR-001 ~ FR-018` 映射回课堂编号 |
