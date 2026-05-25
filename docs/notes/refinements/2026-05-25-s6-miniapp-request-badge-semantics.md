# S6 Miniapp 事务单字徽章语义修复

- 关联主计划条目：`S6.23`
- 状态：`[x]` 已完成
- 日期：`2026-05-25`

## 背景

用户复核小程序首页和事务申请页时指出，“事务办理”入口的单字徽章错误显示为 `宿`，申请类型卡片也存在多个事项统一退化为不准确单字的问题。经检查，当前小程序并没有独立 SVG 资源承载这些字形，截图中的所谓“图标”来自 Vue 页面中的文本单字徽章。

## 范围

- 检查 `miniapp/src` 下所有 SVG / 图标相关引用，确认小程序源码内无独立 `.svg` 图标资源；仓库中唯一 `.svg` 为后端 PDF 用 `backend/app/pdf_assets/ruc-logo.svg`。
- 将首页“事务办理”入口单字从 `宿` 修正为 `事`。
- 新增 `miniapp/src/utils/request-badge.ts`，统一事务类型 / 分类的单字徽章映射。
- 将申请发起页、申请列表页、申请详情页改为复用统一 helper。
- 补齐常见申请分类语义：请假 `假`、证明 `证`、盖章 `章`、报名 `报`、材料 `材`，未知事务统一为 `事`。
- 清除小程序源码和 `mp-weixin` 构建产物中的 `宿 / DORM` 图标映射残留。

## 执行项

- [x] `S6.23.1` 全量扫描小程序 SVG / PNG / 文本徽章来源，确认问题来自页面文本徽章而非 SVG 文件。
- [x] `S6.23.2` 修复首页“事务办理”入口单字徽章。
- [x] `S6.23.3` 提取事务徽章统一 helper，避免页面内重复硬编码。
- [x] `S6.23.4` 同步申请创建、列表、详情三处事务徽章映射。
- [x] `S6.23.5` 完成类型检查、构建与残留扫描。

## 验证结果

- `git diff --check -- miniapp/src/utils/request-badge.ts miniapp/src/pages/index/index.vue miniapp/src/pages/request/create.vue miniapp/src/pages/request/index.vue miniapp/src/pages/request/detail.vue` 通过。
- `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 通过。
- `pnpm -C miniapp build:mp-weixin` 通过，输出 `miniapp/dist/build/mp-weixin`。
- `rg -n "宿|DORM" miniapp/src miniapp/dist/build/mp-weixin -g "*.vue" -g "*.ts" -g "*.js" -g "*.wxml" -g "*.json"` 无命中。

## 结论

本轮完成小程序学生端事务单字徽章语义修复。后续新增申请类型时，应优先复用 `miniapp/src/utils/request-badge.ts`，避免在页面内再次散落硬编码映射。
