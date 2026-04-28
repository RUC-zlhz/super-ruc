# S6 Miniapp 页面模块注册错误修复

- 关联主计划条目：`S6.15`
- 状态：`[x]`
- 日期：`2026-04-28`

## 背景

用户在微信开发者工具中继续反馈：服务页显示正确，但首页和其他页面仍不正确。随后提供精确控制台错误：

- `module 'utils/async.js' is not defined, require args is '../../utils/async.js'`
- `Page "pages/request/index" has not been registered yet.`
- `Page "pages/notice/index" has not been registered yet.`
- `Page "pages/profile/index" has not been registered yet.`

对比后确认：服务页 `pages/request/index` 不依赖 `@/utils/async`，而首页、我的页、荣誉页会在构建产物中生成 `require("../../utils/async.js")`。微信运行时未注册该独立工具模块时，首页先崩溃，后续 tabBar 页面也会连带出现未注册错误。

## 范围

- 修复 `miniapp` 微信小程序运行时模块注册错误。
- 不改业务接口、路由、tabBar 配置和视觉骨架。
- 保持 `mp-weixin` 为权威验收口径。

## 修复项

- [x] 删除 `miniapp/src/utils/async.ts`，避免继续生成独立 `utils/async.js` 运行时模块。
- [x] `miniapp/src/pages/index/index.vue` 内联小型 `settleAll()`，保留首页通知、申请、流程三路并发请求互不阻断的行为。
- [x] `miniapp/src/pages/profile/index.vue` 内联小型 `settleAll()`，保留画像、纠错申诉、成长补录三路并发请求互不阻断的行为。
- [x] `miniapp/src/pages/honor/index.vue` 将初始化并发改为页面内 `Promise.all([task.catch(...)])`，不再引入独立 helper。

## 验证

- [x] `rg -n "@/utils/async|utils/async|allSettled" miniapp\src`：无命中。
- [x] `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json`：通过。
- [x] `pnpm -C miniapp build:mp-weixin`：通过。
- [x] `rg -n "utils/async|allSettled" miniapp\dist\build\mp-weixin`：无命中。
- [x] `miniapp/dist/build/mp-weixin/utils/` 仅包含 `navigation.js`、`request.js`、`uni-button.js`。
- [x] 产物 `pages/index/index.js`、`pages/profile/index.js`、`pages/honor/index.js` 不再 require `../../utils/async.js`。

## 结论

本轮修复关闭了当前微信开发者工具日志中的直接根因。首页和其他页面不再因 `utils/async.js` 未注册而中断页面注册；后续若仍有页面异常，应继续以新的 DevTools 控制台错误为准定位。

## 变更记录

- `2026-04-28`：创建文件，记录 `utils/async.js` 模块未注册错误的根因、修复项与验证结果。
