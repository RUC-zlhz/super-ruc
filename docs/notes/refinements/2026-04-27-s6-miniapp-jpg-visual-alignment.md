# S6 Miniapp JPG 视觉对齐优化

- 状态：`[x]`
- 关联主计划条目：`S6.3`、`S6.4`
- 创建日期：`2026-04-27`

## 目标

以 `design/miniapp/` 下 13 张微信小程序 JPG 页面稿为视觉基准，在不改写已闭合业务契约的前提下，对 `miniapp` 学生端进行前端美化与体验收口。

## 范围

- 首页、知识查询、通知中心、通知详情、学业查看、荣誉榜、我的画像。
- 事务申请列表、发起申请、申请详情。
- 党团进度列表、党团进度详情、理论自测。

## 约束

1. 只做微信小程序学生端视觉与交互表现优化，不回退 `S1 ~ S6` 已完成的接口与业务闭环。
2. 设计稿作为视觉基准，页面文案与数据仍以当前后端契约和前端接口为准。
3. 验收口径继续使用 `pnpm -C miniapp build:mp-weixin`，必要时补跑 `vue-tsc`。

## 执行项

- [x] `S6.JPG.1` 统一小程序全局色板、卡片、按钮、状态标签、页面背景和导航栏色彩。
- [x] `S6.JPG.2` 按 JPG 优化首页、知识查询、通知、学业、荣誉和画像页面观感。
- [x] `S6.JPG.3` 按 JPG 优化申请列表、发起申请、申请详情的卡片层级、表单区和底部操作区。
- [x] `S6.JPG.4` 按 JPG 优化党团进度列表、详情和理论自测三阶段页面。
- [x] `S6.JPG.5` 完成类型检查、微信小程序出包和计划回写。

## 验证记录

- `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json`：通过。
- `pnpm -C miniapp build:mp-weixin`：沙箱内因 esbuild `spawn EPERM` 失败；提权环境下通过，输出 `dist\build\mp-weixin`。
- 产物复核：`miniapp/dist/build/mp-weixin/app.json` 与 `project.config.json` 均存在，页面级 JSON 已包含本轮设置的导航栏颜色。
