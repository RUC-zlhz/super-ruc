# S6 前端体验增量优化 Round 6 (交互与动画增强)

- 负责人：Agent
- 状态：`[x]` 已完成
- 关联主计划：`S6.19` (新增)

## 目标

基于现有的 JPG 视觉对齐成果，进一步优化 `web` 与 `miniapp` 双端的交互细节与动效体验，不改变已有版式，仅增加反馈与平滑度。

## 变更范围

### Web 端
1. **全局卡片动画**：为 `.page-card`、`.filter-card`、`.table-card`、`.panel-card` 等关键容器增加 `fade-in-up` 载入动画，并增加 `box-shadow` 的 hover 放大效果。
2. **路由切换动画**：在 `web/src/layouts/MainLayout.vue` 中为 `<router-view>` 增加 `fade-slide` 路由切换过渡，提升导航体验。
3. **交互组件强化**：为表格行 `.ant-table-tbody > tr > td` 增加背景色过渡动画，为所有按钮 `.ant-btn` 增加 `:active` 缩放效果与平滑渐变，并强化 `.metric-tile` 的悬停位移。

### Miniapp 端
1. **全局触摸反馈**：在 `miniapp/src/App.vue` 增加通用的 `.hover-opacity` 与 `.hover-scale` 触摸反馈类。
2. **首页高频入口**：为 `miniapp/src/pages/index/index.vue` 中的待办提醒、最新通知、常用服务与刷新按钮增加原生 hover 交互。
3. **事务申请与进度**：为 `miniapp/src/pages/request/index.vue` 与 `miniapp/src/pages/workflow/index.vue` 中的申请列表卡片、发起按钮、流程卡片、理论自测卡片增加触摸缩放或透明度变化，提供更清晰的操作确认感。
4. **通知列表**：为 `miniapp/src/pages/notice/index.vue` 中的通知卡片与加载更多按钮增加触摸反馈。

## 验证项

- [x] Web 端执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json` 与 `pnpm -C web build` 均通过。
- [x] Miniapp 端执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 与 `pnpm -C miniapp build:mp-weixin` 均通过。
- [x] 验证 Web 路由动画、按钮点击态与卡片悬停正常渲染，无报错。
- [x] 验证 Miniapp 微信出包成功，构建产物 `app.json` 完整。