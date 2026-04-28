# S6 Miniapp JPG 视觉对齐 Round 4

- 状态：`COMPLETED`
- 关联主计划条目：`S6.3`、`S6.4`、`S6.7`、`S6.8`、`S6.10`、`S6.12`
- 创建日期：`2026-04-28`

## 背景

用户复核指出 `miniapp` 当前界面与 `design/miniapp/` JPG 设计截图仍有明显差距。本轮在不改业务接口、不引入 Claude/Anthropic 兼容层的前提下，继续围绕微信小程序学生端视觉骨架做 Round 4 收紧。

## 本轮目标

1. 将首页底部导航从三栏调整为更贴近设计稿的 `首页 / 服务 / 消息 / 我的` 四栏，并保证 tabBar 页面跳转逻辑同步。
2. 收紧首页、事务申请、发起申请、通知中心、通知详情、党团进度列表等高频页面的卡片半径、阴影、浅粉背景、红色 CTA 与紧凑信息密度。
3. 统一动态表单输入控件为浅粉卡片式表单块，贴近 `发起申请.jpg` 的柔和表单观感。
4. 保持 `mp-weixin` 出包作为权威验收入口。

## 执行项

- [x] `miniapp/src/pages.json` 增加 `pages/request/index` 为 `服务` tab，并将通知 tab 文案收口为 `消息`。
- [x] `miniapp/src/utils/navigation.ts` 将 `request/index` 纳入 tabBar 页面集合，避免 tab 页误用 `navigateTo`。
- [x] 新增 `miniapp/src/static/tab-service.png` 与 `tab-service-active.png`，并确认构建产物带出。
- [x] `miniapp/src/App.vue` 收紧全局红色、浅粉背景、边框、阴影和圆角变量。
- [x] `miniapp/src/pages/index/index.vue` 将常用服务改为设计稿式八宫格入口，并收紧首页 hero、同步卡、KPI 卡、服务卡节奏。
- [x] `miniapp/src/pages/request/index.vue` 调整事务申请顶部说明、红色发起按钮、状态卡、筛选条和申请卡样式。
- [x] `miniapp/src/pages/request/create.vue` 与 `miniapp/src/components/DynamicForm.vue` 收紧类型卡、表单卡、输入框、底部操作区和确认弹窗观感。
- [x] `miniapp/src/pages/notice/index.vue` 与 `notice/detail.vue` 收紧通知卡、图标、红色详情页头部和内容卡密度。
- [x] `miniapp/src/pages/workflow/index.vue` 修正党团列表中段标题色和卡片骨架，使红色 hero 下方回到白卡内容区。

## 验证

- `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json`：通过。
- `pnpm -C miniapp build:mp-weixin`：沙箱内首次命中本项目已知 esbuild `spawn EPERM`，提权环境重跑通过，输出 `miniapp/dist/build/mp-weixin`。
- `miniapp/dist/build/mp-weixin/app.json`：已包含四栏 tabBar，且 `static/tab-service*.png` 已进入构建产物。

## 结果说明

本轮完成小程序视觉 Round 4 收口，重点补齐设计稿中的四栏底部导航、首页服务入口、浅粉白卡、紧凑状态筛选、表单块和红色关键动作。后续若继续推进，应优先用微信开发者工具真机预览逐页截图，对照 `design/miniapp/` 继续做像素级间距和图标资产收紧。
