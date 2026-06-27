# 第 14 组本地小程序配置说明

本说明用于在不把第 12 组平台密码写入命令、文件或日志的前提下，从互评平台下载第 14 组资料并定位可导入微信开发者工具的小程序项目。

## 安全登录方式

1. 将第 12 组互评平台完整密码复制到剪贴板。
2. 在仓库根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/testing/setup-group14-miniapp-from-platform.ps1 -RegisterIfMissing
```

3. 脚本只从剪贴板读取密码一次，不打印、不保存密码；如希望读取后清空剪贴板，可增加 `-ClearClipboardAfterRead`。

## 脚本产出

- 平台资料下载目录：`tmp/docs/group14/platform-documents`
- 项目解包目录：`tmp/group14-miniapp/extracted`
- 配置摘要：`tmp/group14-miniapp/SETUP_SUMMARY.md`

## 导入微信开发者工具

脚本完成后，打开 `tmp/group14-miniapp/SETUP_SUMMARY.md`：

- 若列出包含 `project.config.json` 的目录，直接用微信开发者工具导入该目录。
- 若列出 `manifest.json`、`pages.json` 或 `package.json`，先按项目类型安装依赖并构建微信小程序产物，再导入构建目录。
- 若没有任何候选项目目录，说明平台资料中可能只有 PDF 或未提供源码包；可按指导书记录为“文档/交付资料不足导致小程序端无法运行”的候选问题。

## 已知入口

- Web 管理端：`http://10.10.0.4/admin/admin.html`
- Web 后端健康检查：`http://10.10.0.4/api/health`
- 小程序端：需以平台下载到的源码包为准，PDF 本身未给出源码包路径。

## 2026-05-28 执行结果

- 已使用第 12 组账号登录互评平台。
- 第 14 组已在“我的测试对象”中，无需重复登记。
- 第 14 组平台资料接口仅返回 1 个 `usage` PDF：`/uploads/a26b255d5f1f41a1b454c00b2b32278e.pdf`。
- 已下载到：`tmp/docs/group14/platform-documents/group14-usage.pdf`。
- 已扫描 `tmp/group14-miniapp`，未发现 `project.config.json`、`app.json`、`pages.json`、`manifest.json` 或 `package.json`。
- 当前无法完成微信开发者工具本地导入配置；已整理候选 bug：`docs/testing/group14-bug-report-drafts.md`。

## 2026-05-28 补充 Markdown 复核

- 用户补充链接：`http://183.174.61.212:8001/uploads/784ad38352564ddcb562ebdd2c9f4ae7.md`。
- 已保存到：`tmp/docs/group14/platform-documents/group14-extra.md`。
- 该 Markdown 是 Web 互测指南，提供 `http://10.10.0.14/`、`demo.* / demo1234` 演示账号和 Web 功能测试项。
- 已验证 `http://10.10.0.14/` 与 `http://10.10.0.14/api/health` 可访问，五类 `demo.*` 账号均可登录。
- 该 Markdown 仍未提供微信小程序源码包或可导入微信开发者工具的项目目录；因此只能补充 Web 测试入口，不能完成小程序本地配置。
- Web 测试摘要见：`docs/testing/group14-web-test-summary.md`。
