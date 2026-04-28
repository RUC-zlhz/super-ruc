# S6 Miniapp 微信开发者工具 CLI AppID 对齐

- 关联主计划条目：`S6.16`
- 状态：`[x]`
- 日期：`2026-04-28`

## 背景

用户开启微信开发者工具服务端口后，使用 CLI 进一步验证小程序运行状态。验证中发现：

- `cli.bat islogin --port 21115` 返回 `{"login":true}`，确认服务端口可用。
- `cli.bat open --project D:\Codes\super-ruc\miniapp --port 21115 --trust-project` 可正常打开项目。
- `cli.bat open --project D:\Codes\super-ruc\miniapp\dist\build\mp-weixin --port 21115 --trust-project` 报 `AppID 不合法`。

根因是源码 `miniapp/src/manifest.json` 的 `mp-weixin.appid` 仍为 `wx_test_appid`，导致 `pnpm -C miniapp build:mp-weixin` 生成的 `dist/build/mp-weixin/project.config.json` 带出测试 AppID。根目录 `miniapp/project.config.json` 已配置真实 AppID 和 `miniprogramRoot`，所以导入根目录可运行；但按构建输出提示直接导入 `dist/build/mp-weixin` 会触发 AppID 校验失败。

## 修复项

- [x] 将 `miniapp/src/manifest.json` 的 `mp-weixin.appid` 对齐为 `wxcf977479348ca1d3`。
- [x] 重新执行 `pnpm -C miniapp build:mp-weixin`，确认生成物 `dist/build/mp-weixin/project.config.json` 也带出真实 AppID。
- [x] 用微信开发者工具 CLI 服务端口验证根目录项目可打开，且构建产物目录可直接打开和预览。

## 验证

- [x] `pnpm -C miniapp build:mp-weixin`：通过。
- [x] `rg -n "appid" miniapp\src\manifest.json miniapp\dist\build\mp-weixin\project.config.json miniapp\project.config.json`：三处微信 AppID 口径一致。
- [x] `cli.bat islogin --port 21115`：返回 `{"login":true}`。
- [x] `cli.bat open --project D:\Codes\super-ruc\miniapp\dist\build\mp-weixin --port 21115 --trust-project`：通过。
- [x] `cli.bat preview --project D:\Codes\super-ruc\miniapp\dist\build\mp-weixin --port 21115 --qr-format terminal --trust-project`：通过，并显示 `Using AppID: wxcf977479348ca1d3`。
- [x] 微信开发者工具日志显示 `simulator launch success`、`finish load user code`、`webview page ready`，未再出现 `utils/async.js` 或页面未注册错误。

## 结论

本轮修复消除了“根目录可打开、直接导入构建产物 AppID 不合法”的不一致状态。后续微信开发者工具验收优先使用 `miniapp/dist/build/mp-weixin`，与 `uni build -p mp-weixin` 的输出提示保持一致；`miniapp` 根目录仍保留 `miniprogramRoot` 作为兼容入口，但不再依赖它覆盖构建产物中的测试 AppID。

## 变更记录

- `2026-04-28`：创建文件，记录 DevTools CLI 服务端口验证、AppID 漂移根因和修复结果。
