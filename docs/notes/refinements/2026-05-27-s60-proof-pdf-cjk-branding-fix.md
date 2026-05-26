# S60 证明 PDF 信息学院品牌与中文字体修复

- 状态：`[x]` 已完成
- 日期：`2026-05-27`
- 目标：修复证明 PDF 在生产容器中中文字体不可用导致的渲染异常，并用测试锁定证明模板必须使用“中国人民大学信息学院”品牌。

## 问题

- 本地 ReportLab 可注册 Windows 中文字体，证明 PDF 能正常显示中文。
- 生产 backend 容器当前没有 CJK 字体文件，`_register_reportlab_font()` 回退到 `Helvetica`，中文会出现缺字、方块或渲染异常。
- 生产数据库中的默认证明模板内容已是“中国人民大学信息学院”，未发现“社会学院”字样；需要用测试防止模板品牌再次漂移。

## 修复内容

- backend Docker 镜像安装 `fontconfig` 与 `fonts-noto-cjk`，并执行 `fc-cache -f`，让生产 WeasyPrint/Pango 能找到中文字体。
- ReportLab fallback 不再直接回退到 `Helvetica`；当找不到本机 CJK 字体文件时注册内置 CID 字体 `STSong-Light`。
- ReportLab fallback 只尝试兼容的 TrueType 本地字体；Noto CJK TTC 只作为 WeasyPrint/Pango 字体来源，不再被 ReportLab 直接注册，避免生产日志出现 TTC 注册异常。
- `html_to_pdf_bytes()` 在 Linux 环境检测不到 CJK 字体文件时，直接走 ReportLab CID fallback，避免 WeasyPrint 在缺字体环境下输出不可读中文。
- 单元测试锁定默认证明模板包含“中国人民大学信息学院”，并不包含“社会学院”或“社会与人口学院”。
- 单元测试覆盖无本机字体文件时 ReportLab fallback 返回 `STSong-Light`。
- 单元测试覆盖 ReportLab 字体候选列表不包含 Noto CJK TTC。

## 验证

- 本地生成 `tmp/pdfs/proof-font-smoke.pdf` 并渲染为 PNG，页面中文可读，版头、正文、水印和落款均显示“中国人民大学信息学院”。
- 后端 `py_compile` 通过。
- 后端 `ruff check` 通过。
- `backend/unit_tests/test_proof_template_engine.py` 通过。
- 本地 smoke backend 镜像中 `_register_reportlab_font()` 返回 `STSong-Light`，不再先触发 Noto TTC 注册异常。
- 生产部署验证：`main` 推送后 GitHub Actions self-hosted runner 完成部署，生产 `.deploy/current_commit` 到 `d021164ee27f03cf634db55924964845ec2fac74`，backend/web 均 healthy，`smoke.sh` 与外部 `/healthz` 通过。
- 生产字体验证：backend 容器 `fc-list :lang=zh` 可见 Noto CJK，`_has_cjk_font_file()` 返回 `True`，`html_to_pdf_bytes()` 可生成包含“中国人民大学信息学院”的中文 PDF 字节流。
