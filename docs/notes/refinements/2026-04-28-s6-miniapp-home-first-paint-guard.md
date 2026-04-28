# S6 Miniapp 首页首屏防白屏兜底

- 关联主计划条目：`S6.14`
- 状态：`[x]`
- 日期：`2026-04-28`

## 背景

用户在微信开发者工具中继续反馈首页主体为空白：顶部原生导航栏与底部 tabBar 可见，但中间页面主体没有渲染出内容。

本轮复核确认：

- `miniapp/dist/build/mp-weixin/pages/index/index.wxml` 已包含完整首页结构，不是模板未出包。
- 微信开发者工具本地 `miniprogramLog` 可见 `pages/index/index onLoad / onShow / onReady`，说明页面生命周期已触发。
- 因此需要降低首页首屏对运行时初始化、Pinia active instance、后端 API 和复杂 WXSS 背景解析的依赖。

## 范围

- 只改 `miniapp/src/pages/index/index.vue`。
- 不改接口契约、页面路由、tabBar 配置和整体视觉骨架。
- 保持 `mp-weixin` 为权威验收口径。

## 修复项

- [x] 将首页 `useAuthStore()` 从 `setup` 顶层移入 `loadDashboard()` 内部保护块，避免 Pinia 初始化异常阻断首屏组件创建。
- [x] 将首页姓名默认值改为本地 `ref("同学")`，登录态获取成功后再异步更新。
- [x] 通知、申请、流程接口结果全部增加空数组兜底，接口失败或返回缺字段时不影响静态首屏。
- [x] 为首页根容器与 Hero 增加内联背景色，避免微信 WXSS 对 CSS 变量、多重渐变或复杂背景解析异常时出现白底白字。

## 验证

- [x] `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json`：通过。
- [x] `pnpm -C miniapp build:mp-weixin`：通过。
- [x] 产物 `miniapp/dist/build/mp-weixin/pages/index/index.wxml` 已包含 `background-color:#f8f3f4` 与 `background-color:#b70f24;color:#ffffff` 内联首屏兜底。
- [x] 产物 `miniapp/dist/build/mp-weixin/pages/index/index.js` 中 `useAuthStore()` 已位于 `loadDashboard()` 的保护块，不再位于页面 `setup` 顶层。
- [x] 产物 JS 扫描 `?? / Promise.allSettled / Object.fromEntries / flatMap / matchAll / .at(`：无命中。

## 结论

本轮修复使首页首屏具备静态先渲染能力：即使 Pinia、登录态、后端接口或部分 WXSS 解析存在运行时问题，也不应再出现只有原生导航栏和 tabBar、主体完全空白的状态。

## 变更记录

- `2026-04-28`：创建文件，记录首页首屏防白屏兜底的根因判断、修复项与验证结果。
