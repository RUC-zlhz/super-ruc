# S6 Design Detail Frontend Optimization Round 5

- 日期：`2026-04-28`
- 关联主计划：`S6.1`、`S6.2`、`S6.3`、`S6.4`、`S6.7`、`S6.9`、`S6.11`、`S6.12`、`S6.17`
- 当前状态：`[x]` 已完成

## 背景

用户要求继续根据 `design/` 中的图片内容做一轮更细致的前端设计优化。本轮在既有 `S6.9 ~ S6.12` 视觉系统之上补齐剩余结构差距，避免推翻已确认的 Web 壳层、小程序四栏 tabBar、微信运行时白屏修复和 AppID 对齐修复。

## 范围

- Web 管理端：按 `design/web/` 的宽屏工作台特征，补齐仍偏标准表格页的题库、培养方案、审计日志和荣誉公示页面。
- Miniapp 学生端：按 `design/miniapp/` 的白色导航、浅粉底、红色头图、底部动作和弹层上传区特征，继续收紧理论自测、知识详情、事务申请、通知详情、荣誉详情与画像弹层。
- 保持前端范围，不改后端 API、权限逻辑和业务状态机。

## 完成项

- [x] `web/src/views/workflow/QuizBank.vue`：将题目新增/编辑从弹窗改为右侧常驻编辑面板，并补题库主题摘要。
- [x] `web/src/views/academic/CurriculumRules.vue`：将 tabs/modal 改为“方案列表 / 模块与开课 / 等价关系”三栏工作台。
- [x] `web/src/views/audit/AuditLog.vue`：将详情 popover 升级为右侧日志详情面板，展示事件、实体、对象、操作人、IP、范围和详情载荷。
- [x] `web/src/views/honor/HonorList.vue`：补右侧公示治理面板，集中展示状态分布、类别入口和批量导入入口。
- [x] `miniapp/src/pages/workflow/quiz.vue`：将理论自测进一步靠近设计稿的红色头图、白卡选题、白底答题卡和结果横幅。
- [x] `miniapp/src/pages/request/index.vue`：补状态筛选动作 sheet 与请求失败兜底提示，避免可点击筛选无响应。
- [x] `miniapp/src/pages/knowledge/index.vue`、`notice/detail.vue`、`honor/index.vue`：为查看原文、收藏、分享、附件等视觉动作补前端反馈或剪贴板行为。
- [x] `miniapp/src/pages/profile/index.vue`：在纠错申诉与成长补录弹层中补上传凭证/附件视觉区和点击反馈。

## 验证

- `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json`：通过。
- `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json`：通过。
- `pnpm -C web build`：沙箱内命中本机已知 `esbuild spawn EPERM`，提权重跑通过，输出 `web/dist/`。
- `pnpm -C miniapp build:mp-weixin`：沙箱内命中本机已知 `esbuild spawn EPERM`，提权重跑通过，输出 `miniapp/dist/build/mp-weixin`。

## 风险 / 后续

- 本轮只补前端视觉与轻量反馈；画像附件上传、荣誉附件查看等仍需以后端附件字段和上传接口为准再接真实文件流。
- 若继续做像素级复刻，应优先以真机或微信开发者工具截图复核小程序页面，而不是再扩大业务范围。
