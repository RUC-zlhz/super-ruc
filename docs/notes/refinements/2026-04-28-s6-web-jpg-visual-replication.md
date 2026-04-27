# S6 Web 管理端 JPG 视觉复刻优化

- 日期：`2026-04-28`
- 关联主计划：`S6.1`、`S6.2`、`S6.5`、`S6.9`
- 当前状态：`[x]` 已完成

## 范围

- 以 `design/web/` 下管理端 JPG 设计稿和 `学生画像.png` 为视觉基准，统一 Web 管理端的整体观感。
- 优先复刻共同视觉语言：人大红顶栏、深色侧栏、浅灰工作区、白底卡片、红色主按钮、KPI 指标卡、紧凑表格、状态胶囊、右侧抽屉与弹窗样式。
- 页面结构继续沿用当前 Vue 3 + Ant Design Vue 组件和现有后端 API 契约，不引入假数据。

## 非范围

- 不修改后端接口、权限逻辑、数据字段或业务状态机。
- 不修改 `miniapp`，本轮只覆盖 Web 管理端。
- 不将设计稿内容作为业务数据写死；页面统计只从当前接口响应或当前页数据派生。

## 完成项

- [x] 重做全局视觉令牌与 Ant Design Vue 覆盖样式：`web/src/styles/theme.scss`。
- [x] 重做登录后统一壳层：`web/src/layouts/MainLayout.vue`，形成红色顶栏、深色侧栏、顶部搜索和统一面包屑。
- [x] 重做基础页面：`web/src/views/Login.vue`、`web/src/views/error/Forbidden.vue`。
- [x] 为运营看板、审批工作台、审批详情、知识库、通知中心、用户管理、审计日志、导入导出、党团流程、理论题库、培养方案、荣誉公示、个人信息、学生画像补齐统一 KPI 卡、筛选卡、表格与抽屉视觉。
- [x] 保持现有 API 和业务交互不变，仅做前端结构与样式增强。

## 验证

- `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json` 通过。
- `pnpm -C web build` 通过，产出 `web/dist/`。
- 构建过程中仅出现 Dart Sass legacy JS API deprecation warning，未阻断构建。

## 风险 / 后续

- 设计稿没有提供可直接复用的校徽、校园建筑或人物头像切图，本轮采用 CSS 图形、文字标识和现有数据结构复现视觉气质。
- `2026-04-28` 后续补充：已新增 `docs/notes/refinements/2026-04-28-s6-web-jpg-visual-tightening-round2.md`，基于本轮视觉系统继续执行逐页 Chrome/CDP 截图对照，并补齐通知中心、党团流程管理、导入导出中心的固定右侧工作面板。
- 若需要继续向逐像素级复刻推进，需要后续补充正式品牌图片资产，并继续以截图 contact sheet 作为验收证据。
