# 2026-04-19 历史文档资产与脚本清理（v1.2 ~ v1.4）

- 日期：`2026-04-19`
- 关联主计划：`S5A.3, S5B.1, S5B.2, S5B.3`
- 当前状态：`DONE`

## 范围

- 清理 `v1.2 ~ v1.4` 历史文档链仍残留在 `tmp/docs/` 的正式脚本入口与正式渲染输入。
- 将仍承担“最小可复现主链”职责的历史脚本和 PNG 输入迁入受版本控制目录。
- 明确哪些历史脚本和截图仍只是参考材料或中间产物，不升级为正式入口。

## 非范围

- 本轮不重写 `v1.2 ~ v1.4` 的历史实现逻辑。
- 本轮不把 `raw/` 渲染结果、页面截图、比对图和测试图迁入版本控制目录。
- 本轮不重导 `v1.2 ~ v1.4` 的正式 `docx / pdf` 交付件。

## 任务清单

- [x] `HD.1` 识别 `v1.2 ~ v1.4` 历史链中的主构建脚本与包装脚本边界
- [x] `HD.2` 迁移 `v1.2 / v1.3` 历史主链脚本到受版本控制目录
- [x] `HD.3` 建立 `v1.2 / v1.3 / v1.4` 历史主链 PNG 输入资产目录
- [x] `HD.4` 修正历史主链默认路径，避免继续把 `tmp/docs` 当正式输入源
- [x] `HD.5` 回写目录说明与计划文件，明确未迁移历史件的降级角色

## 执行结果

- 已新增 `scripts/srs/v1_2/build_srs_v12_from_template.py`，承接原 `tmp/docs/build_srs_docx.py` 的历史主链职责，并改为读取 `docs/source/diagrams/rendered/v1_2/`。
- 已新增 `scripts/srs/v1_2/polish_srs_v12_layout.ps1`，保留 `v1.2` 历史版式整理逻辑，并改为通过脚本位置解析仓库根目录；后续又把关键中文字面量收敛为 ASCII-safe 码点常量，降低 PowerShell 编码敏感性。
- 已新增 `scripts/srs/v1_3/build_srs_v13_from_v12.py`，承接原 `tmp/docs/build_srs_v13_from_v12.py` 的历史主链职责，并改为读取 `docs/source/diagrams/rendered/v1_3/`。
- 已将 `scripts/srs/update_srs_v14_incremental.py` 的默认图目录切换到 `docs/source/diagrams/rendered/v1_4/`。
- 已新增 `docs/source/diagrams/rendered/` 及 `v1_2/`、`v1_3/`、`v1_4/` 三个受控历史 PNG 目录，并仅复制历史主链实际依赖的最小 PNG 集。
- 已更新 `docs/source/diagrams/README.md` 与 `scripts/srs/README.md`，明确 `rendered/` 是历史主链输入目录，`tmp/docs` 中包装脚本、截图、`raw/` 渲染结果和实验文件默认继续视为参考/中间产物。

## 验证记录

- 已执行 `python -m py_compile scripts/srs/v1_2/build_srs_v12_from_template.py scripts/srs/v1_3/build_srs_v13_from_v12.py scripts/srs/update_srs_v14_incremental.py`，静态编译通过。
- 已执行 PowerShell Parser 校验，`scripts/srs/v1_2/polish_srs_v12_layout.ps1` 当前返回 `OK`，确认受控副本不存在语法级损坏。
- 已执行 `git grep` 追踪文件检索，仓库内对 `polish_srs_v12_layout`、`polish_srs_layout.ps1`、`refresh_export_v12`、`export_preview.ps1` 的正式引用结果为 `NO_TRACKED_MATCHES`；说明这些包装脚本当前不被活跃正式链直接消费。
- 已确认 `docs/source/diagrams/rendered/v1_2/`、`v1_3/`、`v1_4/` 的受控 PNG 数量分别为 `5 / 9 / 11`，与本轮迁移范围一致。

## 未迁移但已定性的历史件

- `tmp/docs/update_srs_v13_incremental.py`：保留为历史增量实验脚本；其默认图集命名与现存 `v1_3` 冻结 PNG 不一致，不作为当前最小可复现主链入口。
- `tmp/docs/refresh_export_v12.py` 与 `tmp/docs/refresh_export_v12.ps1`：保留为历史导出包装层；正式导出能力已由 `scripts/srs/export_docx_pdf.py` 覆盖。
- `tmp/docs/export_preview.ps1`：保留为预览脚本，不升级为正式出件入口。
- `tmp/docs/polish_srs_layout.py`：保留为简化实验脚本；`v1.2` 历史主链保留更完整的 `polish_srs_v12_layout.ps1`。

## 验收条件

- `v1.2 / v1.3 / v1.4` 历史主链不再默认依赖 `tmp/docs` 中的正式脚本入口或正式 PNG 输入。
- 历史包装脚本、预览脚本、截图和实验文件有明确降级说明，不再与正式入口混淆。
- 新对话可通过受版本控制目录识别历史链最小可复现资产。
