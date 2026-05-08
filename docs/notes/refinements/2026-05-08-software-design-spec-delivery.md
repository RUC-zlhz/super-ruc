# 软件设计规格说明书出件

- 创建日期：`2026-05-08`
- 关联主计划：`S10.1, S10.2, S10.3`
- 状态：`[x]`
- 输入依据：当前仓库代码、`docs/source/` 需求输入、`docs/srs/` 追踪矩阵、`docs/notes/current-implementation-plan.md`、模板文件 `软件设计规格说明书.doc`

## 目标

严格按照根目录 `软件设计规格说明书.doc` 的章节结构与版式要求，生成软件设计规格说明书，覆盖引言、软件设计约束、体系结构、用户界面、用例、类、数据与部署设计，并配套 Mermaid 图。

## 任务清单

- [x] `S10.1` 读取并转换 `.doc` 模板，抽取封面、变更历史表、目录、章节标题和正文样式。
- [x] `S10.2` 基于当前代码和需求资料生成 SDS 正文，覆盖 backend / web / miniapp / deploy / docs 的真实实现。
- [x] `S10.3` 生成并嵌入 6 张 Mermaid 图，保留正式图源到 `docs/source/diagrams/mermaid/software-design-spec/`，并通过 Word 导出 PDF 与页面 PNG 渲染检查。

## 验收条件

- 输出文件：`output/doc/软件设计规格说明书-信息学院学生综合服务与党团管理平台-v1.0.docx`
- 图源文件：`docs/source/diagrams/mermaid/software-design-spec/*.mmd`
- 渲染检查：Word COM 更新目录并导出 PDF，`pdftoppm` 渲染 12 页 PNG，未发现明显重叠、截断或空白页。

## 风险 / 阻塞

- 未使用 image generation；本轮全部图均为 Mermaid 受控图源，便于后续维护和 Word 兼容。
- `S9.DB` 后端定向集成测试仍按原计划处于数据库拒连阻塞状态；本 SDS 将该事实作为当前验证风险记录，不将其改写为已通过。

## 变更记录

- `2026-05-08`：创建本细化文件，登记软件设计规格说明书出件、正式图源迁移与渲染检查结果。
