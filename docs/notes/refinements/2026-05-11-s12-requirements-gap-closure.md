# S12 需求缺口闭环与默认数据导入

- 创建日期：`2026-05-11`
- 关联主计划：`S12.1, S12.2, S12.3, S12.4, S12.5, S12.6, S12.7, S12.8, S12.9, S12.DOC`
- 状态：`[x]`
- 输入依据：上一轮代理确认的 `S12 需求缺口闭环与默认数据导入计划`

## 目标

在 `S1 ~ S11` 已闭合的基础上，继续关闭需求文档与当前实现之间的 9 项缺口：默认学生与培养方案导入、证明 PDF 管理端预览、独立模板下载、成绩单 PDF 人工核验入库、课程推荐边界、统一进度中心、受控通知抓取、短信 provider/重试/回执、官方链接优先知识匹配，并同步形成 SRS v1.7 增量交付件。

## 数据源

- 默认学生花名册：`docs/source/students/students.xlsx`
- 默认培养方案：`docs/source/training program/2024_information.md`

## 执行拆分

- [x] `S12.1` 默认数据导入：新增管理端默认导入接口与 Web 导入中心按钮；学生只导核心字段，培养方案导入生成 `2024-default` 版本并写入课程白名单。
- [x] `S12.2` 成绩单 PDF 核验：学生上传仍只生成候选批次；教师核验提交后才写入正式成绩。
- [x] `S12.3` 学业缺口与课程推荐增强：修复培养方案导入 `courses` 落库，推荐结果基于缺口、开课学期、已修课程和可用数据排序；缺少容量/课表/先修/偏好数据时显式提示“数据未配置”。
- [x] `S12.4` 模板下载与知识官方链接：新增独立常用模板列表，收紧模板下载权限，知识匹配同等相关度下优先官方来源并返回来源链接。
- [x] `S12.5` 统一进度中心：新增 `GET /progress/my` 聚合事务申请与党团流程，小程序新增进度中心页。
- [x] `S12.6` 受控通知抓取：新增公开 URL/RSS 来源、手工抓取、历史记录；抓取结果只生成 draft notice，不自动群发。
- [x] `S12.7` 短信投递治理：新增 mock/local provider、投递 attempt、失败重试和 mock 回执。
- [x] `S12.8` Web 管理端接入：审批详情证明 PDF 预览/下载、默认导入按钮、成绩单核验、模板下载、通知来源/抓取历史/SMS 重试入口。
- [x] `S12.9` Miniapp 学生端接入：学业首页入口、PDF 解析候选明细、常用模板页、进度中心、AI 卡片官方链接展示。
- [x] `S12.DOC` 文档出件：增量更新 SRS/FR/追踪矩阵/验收走查，复制 v1.6 出件链为 v1.7 并导出 DOCX/PDF。

## 验证要求

- Backend：设置 repo-local `UV_CACHE_DIR` 后执行 ruff、py_compile 与 S12 定向集成测试。
- Web：`& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json` 与 `pnpm -C web build`。
- Miniapp：`& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 与 `pnpm -C miniapp build:mp-weixin`。
- Docs：SRS v1.7 DOCX/PDF 导出成功，并抽检页数、图资源和关键页面可读性。

## 验证证据

- Backend：`UV_CACHE_DIR=backend/.uv-cache-local` 下执行 `uv run pytest tests\integration\test_s12_gap_closure.py -q`，结果 `5 passed`；执行 `uv run pytest tests\integration\test_report_contract_flow.py -q`，结果 `4 passed`；`ruff check` 与 `py_compile` 均通过。
- Web：执行 `pnpm -C web build`，结果通过，构建包含 `vue-tsc --noEmit`。
- Miniapp：执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 与 `pnpm -C miniapp build:mp-weixin`，均通过。
- Docs：执行 `scripts/srs/v1_7/run_v17_delivery_gate.ps1 -Force` 完成 v1.7 出件；随后将 S12 增量说明注入三份 v1.7 DOCX 并重导 PDF。`v1.7 / v1.7-emf / v1.7-emf-inkscape` 三份 PDF 均为 `38` 页，DOCX 均包含 `S12 需求缺口闭环增量说明`，首页与末页渲染抽检可读。

## 风险与约束

- 短信一期只实现可运行的 `mock/local` provider、重试和回执闭环，不接真实运营商。
- 抓取一期只支持公开 URL/RSS，不绕过登录、验证码、公众号限制或反爬策略。
- 成绩单 PDF 始终是“解析候选 + 教师核验”，不允许学生上传后自动写入正式成绩。
- 默认学生数据不从学号或毕业年份推断专业、年级、班级。
- 默认培养方案是 demo/初始数据；只更新 `version_label=2024-default` 的默认版本，不覆盖教师后续维护的新版本。

## 变更记录

- `2026-05-11`：创建本细化文件，登记 S12 全量闭环范围、默认数据源、执行拆分和验证口径。
- `2026-05-11`：已补 S12 上游 SRS 增量文本，并落盘 `build_srs_v17_from_v16.py` 与 `scripts/srs/v1_7/` 脚本骨架；`S12.DOC` 进入进行中状态，等待后续 DOCX/PDF 导出验证。
- `2026-05-11`：完成 S12 后端、Web、Miniapp 与文档出件闭环；修复学业建议排序，确保默认信息安全培养方案中的 `BISYMS0012` 可进入缺口建议；导出并抽检含 S12 增量说明的 SRS v1.7 DOCX/PDF。
