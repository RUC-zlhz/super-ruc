# S65 小程序按钮反馈与效果审查

- 状态：`[!]`
- 主计划引用：`S65.1 ~ S65.5`
- 日期：`2026-05-27`

## 背景

用户要求检查小程序按钮是否均可点击、是否能收到正确反馈并产生正确效果。当前小程序交互分布在首页、通知、知识库、申请、党团流程、学业、荣誉、画像和通用空态/提示组件。

## 拆分

- [x] `S65.1` 静态扫描所有小程序 Vue 页面与组件中的 `@tap / @click / @change / @confirm / @action` 绑定，确认事件处理函数均可解析。
- [x] `S65.2` 修复点击后静默无反馈或失败回退不明确的交互点。
- [x] `S65.3` 对理论自测提交、知识检索匹配、知识详情、申请详情编辑、通知详情返回、成绩单 PDF 上传和敏感字段完整查看申请补齐反馈约束。
- [x] `S65.4` 运行小程序类型检查与 `mp-weixin` 构建，确认微信小程序产物可生成。
- [!] `S65.5` 使用微信开发者工具 CLI 打开项目并尝试自动化点击烟测；CLI 打开成功，自动化 SDK 连接当前 DevTools WebSocket 协议未完成。

## 修复内容

- 知识库“检索匹配”在未输入问题时提示“请先输入检索问题”，不再静默无效。
- 知识详情打开失败时显示“知识详情打开失败”。
- 理论自测提交前校验是否存在未答题目，并自动跳到第一道未答题且提示题号。
- 申请详情“继续完善/修改并重新提交”跳转失败时显示页面跳转失败。
- 通知详情异常态“返回列表”在无上一页时回退到通知 tab。
- 学业成绩单上传在文件名缺失时也按路径校验 `.pdf` 后缀。
- 画像敏感字段完整查看申请在提交中再次点击时提示“正在提交，请稍候”。
- 学业页模板中的 `result?.disclaimer / data_warnings / suggested_courses` 改为 computed 派生值，避免 DevTools 自动化 dev 编译路径将模板可选链转成不兼容表达式。

## 验证记录

- 事件绑定扫描：`ALL_MINIAPP_EVENT_HANDLERS_RESOLVED`。
- Miniapp 类型检查：`.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json` 通过。
- Miniapp 微信构建：`pnpm -C miniapp build:mp-weixin` 通过，输出提示可导入 `dist\build\mp-weixin`。
- 微信开发者工具 CLI：
  - `D:\Software\WeChatDevTool\cli.bat --help` 可用。
  - `D:\Software\WeChatDevTool\cli.bat auto --project D:\Codes\super-ruc\miniapp --port 51972 --trust-project` 成功，输出 `Using AppID: wxcb6352a74505bc41` 与 `auto`。
  - `D:\Software\WeChatDevTool\cli.bat open --project D:\Codes\super-ruc\miniapp\dist\dev\mp-weixin --port 51972` 成功，输出 `open`。
  - `pnpm -C miniapp exec uni -p mp-weixin --auto-port 9520` 在临时本地依赖兼容补丁下可生成 `miniapp/dist/dev/.automator/mp-weixin/.automator.json` 和 `miniapp/dist/dev/mp-weixin`。
- 自动化连接现状：
  - `@dcloudio/uni-automator` 当前版本仍按旧参数链路调用 DevTools，并在 Windows 下会触发 `.CMD` spawn / DevTools runtime 连接问题。
  - 临时安装 `miniprogram-automator@0.12.1` 后，连接 `ws://127.0.0.1:51972` 失败；扫描 DevTools 监听端口发现 `31611` 可 WebSocket upgrade，但不是 `miniprogram-automator` 协议，连接后返回 `Connection closed`。
  - 本轮未杀微信开发者工具进程；只清理了 Codex 启动的 `miniapp dev:mp-weixin --auto-port 9520` node watcher。

## 当前结论

源码层面未发现未绑定或缺失处理函数的按钮。已修复 7 处点击反馈/失败回退不足的问题，并确认微信开发者工具 CLI 可启动自动化与打开当前小程序产物；但本机当前 DevTools 的自动化 WebSocket 端点尚未被 `@dcloudio/uni-automator` 或 `miniprogram-automator` 成功接入，所以“逐按钮真实点击并断言 toast/路由/原生弹窗”的自动化验收仍为阻塞项。原生能力弹窗、文件选择、订阅授权、PDF 打开等仍需在 DevTools 自动化端点打通后或真机上最终联调。
