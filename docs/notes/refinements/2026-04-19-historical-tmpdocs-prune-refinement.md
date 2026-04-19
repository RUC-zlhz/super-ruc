# 2026-04-19 历史文档链第二阶段收口（v1.3 入口定版 + tmp/docs 本地遗留清理）

- 日期：`2026-04-19`
- 关联主计划：`S5A.3, S5B.1, S5B.2, S5B.3`
- 当前状态：`DONE`

## 范围

- 解决 `v1.3` 在“受控脚本入口”和 `tmp/docs` 本地实验脚本之间的权威性歧义。
- 清理 `tmp/docs` 中已明确判定为实验件或纯中间产物的 `v1.2 ~ v1.4` 历史遗留。
- 将“`tmp/docs` 完全 ignored，本地文件不构成仓库保证内容”的边界回写到受版本控制说明中。

## 非范围

- 本轮不重导 `v1.3 / v1.4` 的正式 `docx / pdf`。
- 本轮不删除当前活跃的 `tmp/docs/v1_5/` 工作目录及其评审产物。
- 本轮不再为低价值历史包装脚本新增受控副本，除非其仍承担正式或参考主链职责。

## 任务清单

- [x] `HT.1` 固化 `v1.3` 权威入口，消除双入口歧义
- [x] `HT.2` 回写 `tmp/docs` ignored-local 边界，避免新对话误把本地临时件当仓库资产
- [x] `HT.3` 删除本地 `tmp/docs` 中已定性的历史实验件、截图与纯中间产物

## 执行结果

- 已确认 [scripts/srs/v1_3/build_srs_v13_from_v12.py](D:/Codes/super-ruc/scripts/srs/v1_3/build_srs_v13_from_v12.py) 是当前仓库内唯一可信的 `v1.3` 受控入口。
- 已确认 `tmp/docs/update_srs_v13_incremental.py` 仅是 ignored 的本地实验脚本：其默认图目录仍指向 `tmp/docs/diagrams/v1_3/`，且图名集合与当前受控 `rendered/v1_3/` 不一致，不再作为仓库保证内容。
- 已更新 `scripts/srs/README.md` 与相关细化文件，明确 `v1.3` 权威入口、`tmp/docs` ignored-local 属性，以及本地实验脚本的降级边界。
- 已清理本地 `tmp/docs` 中以下历史遗留：
  - `tmp/docs/__pycache__/`、`tmp/docs/v1_5/__pycache__/`
  - `review_current_pages/`、`review_template_pages/`、`srs_pages*/`、`template_pages/`
  - `change_compare.png`、`cover_compare.png`、`general_compare.png`、`intro_compare.png`、`other_compare.png`、`toc_compare.png`
  - `fig-3-2a-test.*`、`fig-3-2b-test.*`、`fig-3-2b2-test.*`
  - `system-context-root-htmlfalse.*`、`system-context-test.svg`
  - `svg-insert-test.docx`、`svg-test.puppeteer.json`
  - `word_export_trace.log`、`word_open_alt_trace.log`
  - `tmp/docs/diagrams/test.mmd`、`tmp/docs/diagrams/test.png`
  - `tmp/docs/diagrams/cropped/`、`tmp/docs/diagrams/v1_3/`、`tmp/docs/diagrams/v1_4/`
  - `tmp/docs/diagrams/` 根目录下已被 `docs/source/diagrams/mermaid/` 替代的旧 Mermaid 源副本与 PNG 渲染副本
  - `tmp/docs/build_srs_docx.py`、`tmp/docs/build_srs_v13_from_v12.py`、`tmp/docs/draw_orthogonal_class_diagram.py`、`tmp/docs/export_docx_pdf.py`、`tmp/docs/update_srs_v14_incremental.py`
  - `tmp/docs/update_srs_v13_incremental.py`

## 验证记录

- 已执行 `git ls-files tmp/docs`，返回计数 `0`，确认 `tmp/docs` 为完全 ignored 的本地工作目录。
- 已人工核对 `scripts/srs/v1_3/build_srs_v13_from_v12.py` 与本地 `tmp/docs/update_srs_v13_incremental.py` 的行为差异：前者直接对齐受控 `rendered/v1_3/` 图集，后者属于图名漂移的实验性增量脚本。
- 已在本地工作区完成上述 `tmp/docs` 清理；该清理不产生 Git 跟踪差异，但会减少后续会话对历史临时件的误读和误用。

## 当前边界

- `tmp/docs/` 仍可继续作为本地工作目录使用，但其中任何文件默认都不应被视为仓库保证内容。
- 若后续仍有本地临时脚本需要长期保留，必须先迁入受版本控制目录，再写入细化文件登记。
