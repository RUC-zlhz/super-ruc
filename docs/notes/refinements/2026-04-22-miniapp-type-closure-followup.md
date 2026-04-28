# Miniapp 类型收口补丁

- 日期：`2026-04-22`
- 关联主计划：`S1.3, S1.4, S1.5, S2A.4, S2B.1, S2B.2, S2B.4, S2C.2, S3B.3, S3B.4, S3B.5`
- 当前状态：`DONE`
- 背景：`2026-04-22` 的 `miniapp` 全量 `vue-tsc` 仍存在一组历史遗留类型错误，既包含 `request.ts` 的 `PATCH` 请求签名，也包含多个 uni-app `<button type="primary|warn">` 被误按原生 HTML button 检查的问题；此外还有 `academic` 页的空值比较和 `notice` 页 tab 字面量推断问题。虽然这些错误不改变既有业务闭环实现，但会阻塞当前工作线的 `miniapp` 静态验收。

## 本轮修正

### [x] `S1.3/S1.5-F1` 收口 `request` helper 的 `PATCH` 类型兼容

- `miniapp/src/utils/request.ts`
  - 允许 `request()` 接收 `PATCH`。
  - 调用 `uni.request()` 时保留真实运行时 `PATCH` 值，同时对当前落后的 uni-app 类型声明做最小范围断言，避免把兼容修复扩散到业务页。

### [x] `S1.5-F2` 统一 miniapp 按钮类型误报的共享 helper

- 新增 `miniapp/src/utils/uni-button.ts`
  - 集中导出 `UNI_BUTTON_TYPE.primary / warn`，以共享方式保留 uni-app 运行时按钮语义。
  - 避免在各页面重复写局部 `as unknown as 'button'` 常量。
- 已接入页面：
  - `miniapp/src/pages/knowledge/index.vue`
  - `miniapp/src/pages/profile/index.vue`
  - `miniapp/src/pages/request/create.vue`
  - `miniapp/src/pages/request/detail.vue`
  - `miniapp/src/pages/workflow/quiz.vue`

### [x] `S2A.4/S2C.2-F1` 收口页面级推断错误

- `miniapp/src/pages/notice/index.vue`
  - 为 tab 值补字面量联合类型，消除 `all/unread/read` 推断漂移。
- `miniapp/src/pages/academic/index.vue`
  - 将“差额参考是否为正”的判断拆成独立 computed，避免对可空值直接做数值比较。

## 影响说明

- `request/create` 与 `request/detail` 的附件上传、proof-preview、提交/重提/撤回按钮维持原有 `primary/warn` 视觉语义。
- `profile` 页的登录、纠错申诉、成长补录按钮维持原有主按钮语义。
- `workflow/quiz` 与 `knowledge` 页本轮只收口类型误报，不调整交互与文案。
- 本轮不改动现有业务协议，也不改变此前 `S2/S3` 已关闭条目的完成结论；修复目标仅是恢复当前 `main` 工作线的 `miniapp` 静态可验证性。

## 验证记录

- `[x]` `miniapp` 类型校验：`& '.\\web\\node_modules\\.bin\\vue-tsc.CMD' --noEmit -p miniapp\\tsconfig.json`

## 结论

- 当前 `main` 工作线上的 `miniapp` 历史类型错误已收口，`vue-tsc` 全量校验恢复通过。
- 本轮修复应作为独立的 “miniapp 类型收口” 记录保留，不覆盖 `2026-04-22-s2-notice-followup-and-plan-alignment.md` 的 `S2 notice` 专项背景。
