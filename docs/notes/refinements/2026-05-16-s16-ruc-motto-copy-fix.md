# S16 RUC 校训文案修正

- 日期：`2026-05-16`
- 关联主计划：`S16.1, S16.2, S16.3`
- 当前状态：`DONE`

## 问题

- 用户指出当前 Web 管理端侧栏中 `RUC` 下方文案误写为 `立学为民 · 治学报国`。
- 正确校训文案应为 `实事求是`。

## 修复

- [x] `S16.1` 全仓库检索 `立学为民 / 治学报国 / 实事求是`，确认真实 UI 残留位置。
- [x] `S16.2` 将 `web/src/layouts/MainLayout.vue` 侧栏底部文案替换为 `实事求是`。
- [x] `S16.3` 重新构建 Web 产物，并确认旧文案不再出现在 Web / Miniapp / 后端 / 文档计划 / SRS / specs / scripts 范围内。

## 验证

- `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json` -> 通过。
- `pnpm -C web build` -> 通过；Vite 构建仅输出 Dart Sass legacy JS API 弃用警告。
- `rg -n "立学为民|治学报国" web miniapp backend docs/notes docs/srs specs scripts` -> 无命中。
- `rg -n "实事求是" web/src web/dist` -> 命中源码与新构建产物。

