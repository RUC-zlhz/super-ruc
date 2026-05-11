# 2026-05-11 Miniapp 图标与空态收口 Round 8

- 关联主计划条目：`S6.22`
- 状态：`[x]` 已完成
- 背景：恢复 Git 历史后，工作区保留了一批 Miniapp 学生端 UI 微调。经审查，这批改动不是缓存或误生成，而是围绕页面小图标、加载态、空态和高频入口反馈的真实体验优化，需要按计划治理规则补登记。

## 范围

- 保留 `miniapp/src/components/EmptyState.vue`，统一通知、申请、党团流程等页面的加载中、无数据、无权限/未找到状态。
- 保留 `miniapp/src/App.vue` 中当前实际使用的 `mini-chevron` / `mini-chevron-left` 基础箭头样式。
- 保留首页“常用服务”的单字语义徽章、分组色彩和两行描述，降低 emoji / 符号在微信端显示差异。
- 保留申请、通知、画像、荣誉、知识和理论自测页面的按钮小图标语义化与 hover 反馈。
- 清理当前未使用的全局样式占位，避免 `surface / chip / skeleton / btn-secondary / mini-icon*` 等未接入工具类扩大维护面。
- 清理替换 `EmptyState` 后遗留的页面级旧空态样式，避免父组件 scoped `.empty` 样式覆盖复用组件根节点。
- `.gitignore` 保留 `.trae/` 与 `miniapp/project.private.config.json` 忽略，但不忽略整个 `output/`，避免正式交付件被静默漏提交。

## 执行拆分

- [x] `S6.22.1` 审查恢复后的未提交改动，确认主体为 Miniapp UI 体验优化。
- [x] `S6.22.2` 保留 `EmptyState` 组件和页面级图标 / 空态 / 箭头替换。
- [x] `S6.22.3` 删除未使用的全局样式占位，保留当前页面实际依赖的基础样式。
- [x] `S6.22.4` 删除替换 `EmptyState` 后不再引用的页面级旧空态样式。
- [x] `S6.22.5` 修正 `.gitignore` 中会遮蔽正式 `output/` 交付件的规则。
- [x] `S6.22.6` 回写主计划与细化登记，并完成静态与构建验证。

## 验证结果

- `git diff --check` 通过。
- `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 通过。
- `pnpm -C miniapp build:mp-weixin` 通过，输出 `miniapp/dist/build/mp-weixin`。

## 结论

本轮改动应保留。它没有改变业务接口或路由契约，主要提升微信小程序学生端的空态一致性、页面可读性和操作识别效率；同时避免 `.gitignore` 与未使用全局样式带来后续维护风险。
