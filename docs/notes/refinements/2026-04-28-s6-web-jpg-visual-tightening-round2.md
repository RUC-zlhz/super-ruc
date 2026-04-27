# S6 Web JPG 逐页截图对照 Round 2 收紧

- 日期：`2026-04-28`
- 关联主计划：`S6.1`、`S6.2`、`S6.5`、`S6.9`、`S6.11`
- 当前状态：`[x]` 已完成

## 背景

- 用户要求打开 Web 端逐页截图对照，继续收紧与 `design/web/` JPG / PNG 基准的像素级差距。
- 本轮延续 `2026-04-28-s6-web-jpg-visual-replication.md` 的视觉系统，不替换既有业务流程、不写死设计稿中的业务数据。
- `browser-use` in-app browser 运行时在当前 REPL 中受插件内部静态 `node:os` import 限制阻塞；本轮改用本地 Chrome + CDP 截图链，仍以真实浏览器渲染结果作为逐页视觉证据。

## 范围

- 继续使用 `design/web/` 的 16 张管理端设计稿和 `学生画像.png` 为基准。
- 重点收紧上一轮截图中结构差距最大的区域：
  - 通知中心右侧编辑 / 投递治理面板缺失。
  - 党团流程管理右侧流程配置面板缺失。
  - 导入导出中心右侧校验 / 质量 / 快捷导出面板缺失。
  - 运营看板、知识库、用户管理已在上一轮补右侧面板，本轮保留并复核。

## 完成项

- [x] 逐页运行本地 Chrome/CDP 截图，覆盖 `login`、`403`、`dashboard`、`approval`、`notice`、`knowledge`、`user`、`workflow`、`quiz`、`curriculum`、`honor`、`audit`、`import`、`profile`、`student-profile` 共 `16` 页。
- [x] 生成对照 contact sheet：`.tmp/web-visual-review/web-visual-contact-sheet.png`。
- [x] `web/src/views/notice/NoticeList.vue` 增加固定右侧通知编辑器，展示当前通知、发布信息、标签、投递闭环与原有编辑 / 发送动作。
- [x] `web/src/views/workflow/PartyStageList.vue` 增加固定右侧流程配置面板，展示模板概览、学生流程、提醒规则、节点预览与原有新建 / 查看节点动作。
- [x] `web/src/views/exchange/ImportCenter.vue` 增加固定右侧导入任务面板，展示最新批次、质量比例与原有快捷导出动作。
- [x] 所有新增面板均在 `max-width: 1320px` 下回落为普通卡片，不改变 API 契约或状态机。

## 验证

- `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json` 通过。
- `node .tmp\web-visual-review\capture-web-pages.mjs` 通过，重新生成 `16` 页截图。
- `UV_CACHE_DIR=D:\Codes\super-ruc\.uv-cache uv run --project backend --no-sync --with pillow python -` 通过，重新生成对照 contact sheet。
- `pnpm -C web build` 通过，产出 `web/dist/`；仅出现 Dart Sass legacy JS API deprecation warning。

## 风险 / 后续

- 当前截图仍使用 CDP mock 数据，真实环境中的行数、批次数、权限策略数量会随后端数据变化；本轮只调整布局和视觉容器，不用设计稿假数据填充。
- 仍有少数页面的数据密度低于 JPG，例如题库、培养方案、荣誉、公示等页面；后续若继续收紧，应优先做已有数据区块的并列面板化，而不是硬编码参考图内容。
