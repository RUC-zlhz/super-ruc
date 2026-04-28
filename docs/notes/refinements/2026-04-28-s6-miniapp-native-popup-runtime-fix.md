# S6 Miniapp 原生弹层运行时修复

- 关联主计划条目：`S6.18`
- 状态：`[x]`
- 日期：`2026-04-28`

## 背景

微信开发者工具 CLI 复核后，继续检查小程序页面运行时依赖，发现当前仓库没有 `miniapp/uni_modules/uni-popup`，但以下页面仍直接使用 `<uni-popup>`：

- `miniapp/src/pages/knowledge/index.vue`
- `miniapp/src/pages/honor/index.vue`
- `miniapp/src/pages/profile/index.vue`

这类依赖在 H5 或部分开发环境中可能被兜底处理，但在微信小程序产物中属于未注册组件风险。若运行时尝试解析未注册组件，容易继续表现为页面主体空白或局部交互失效。

## 修复项

- [x] 将知识查询详情弹层改为页面内 `fixed` 遮罩与底部面板。
- [x] 将荣誉详情弹层改为页面内 `fixed` 遮罩与底部面板。
- [x] 将画像纠错申诉、成长补录弹层改为页面内 `fixed` 遮罩与底部面板。
- [x] 移除 `detailPopup / appealPopup / growthPopup` refs，改为 `selected / appealVisible / growthVisible` 状态控制。
- [x] 为三处原生弹层补 `.sheet-mask` 与面板宽度，保留点击遮罩关闭、点击面板内部不冒泡关闭的交互。

## 验证

- [x] `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json`：通过。
- [x] `pnpm -C miniapp build:mp-weixin`：通过，输出 `miniapp/dist/build/mp-weixin`。
- [x] `rg -n '<uni-' miniapp\dist\build\mp-weixin\pages -g '*.wxml'`：无命中。
- [x] `rg -n 'uni-popup|resolveComponent' miniapp\dist\build\mp-weixin\pages -g '*.js' -g '*.wxml'`：无命中。
- [x] `rg -n 'utils/async|async\.js|allSettled' miniapp\src miniapp\dist\build\mp-weixin`：无命中，确认没有回退到上一轮模块注册错误。
- [x] `rg -n 'appid|wx_test_appid|wxcf977479348ca1d3' miniapp\src\manifest.json miniapp\project.config.json miniapp\dist\build\mp-weixin\project.config.json`：微信 AppID 口径一致，未带出 `wx_test_appid`。
- [x] `cli.bat islogin --port 21115`：返回 `{"login":true}`。
- [x] `cli.bat open --project D:\Codes\super-ruc\miniapp\dist\build\mp-weixin --port 21115 --trust-project`：通过。
- [x] `cli.bat preview --project D:\Codes\super-ruc\miniapp\dist\build\mp-weixin --port 21115 --qr-format terminal --trust-project`：通过，显示 `Using AppID: wxcf977479348ca1d3`，包体 `518.3 KB`。
- [x] 按最后一次 CLI 打开开始时间过滤微信开发者工具日志：未出现 `module not defined`、`AppID 不合法`、`ReferenceError`、`TypeError`、`SyntaxError` 或 route timeout。

## 说明

本轮尝试通过窗口截图确认 DevTools 模拟器画面，但当前开发者工具窗口被 Git 扩展提示遮挡，且 `PrintWindow` 对 Electron 渲染层只返回深色背景。因此本细化文件不将截图作为通过证据，验收依据以源码、构建产物、CLI `open / preview` 和按时间过滤后的运行日志为准。

## 结论

知识、荣誉、画像三处小程序弹层已从外部组件依赖改为页面内原生实现。当前 `mp-weixin` 产物不再包含 `uni-popup` 或 `resolveComponent` 运行时依赖，降低微信开发者工具中页面空白与组件注册失败的风险。

## 变更记录

- `2026-04-28`：创建文件，记录 `uni-popup` 运行时风险、页面内原生弹层替换和微信开发者工具 CLI 验证结果。
