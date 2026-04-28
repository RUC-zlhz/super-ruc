# S6 前端体验增量优化 Round 7 (按钮图标语义补齐)

- 负责人：Agent
- 状态：`[x]` 已完成
- 关联主计划：`S6.21` (新增)

## 目标

在 Web 管理端与 Miniapp 学生端全局补齐按钮图标，提高功能入口的可辨识度，减少纯文本按钮带来的视觉单调感与识别成本。

## 变更范围

### Web 端
利用已有的 `@ant-design/icons-vue` 组件，全面为各管理页面的 `<a-button>` 补充语义化图标：
1. **全局操作按钮**：查询 (`SearchOutlined`)、重置 (`ReloadOutlined`)、保存 (`SaveOutlined`)、取消/关闭 (`CloseOutlined`)、新增 (`PlusOutlined`) 等。
2. **数据管理与流程控制**：编辑 (`EditOutlined`)、查看 (`EyeOutlined`)、发布 (`SendOutlined` / `CloudUploadOutlined`)、停用 (`StopOutlined`)、归档 (`InboxOutlined` / `HistoryOutlined`)、撤销 (`RollbackOutlined`)、重新启用 (`CheckCircleOutlined`) 等。
3. **数据交换**：上传/导入 (`UploadOutlined` / `ImportOutlined`)、下载/导出 (`DownloadOutlined`)。
4. **覆盖页面**：
   - `ApprovalDetail.vue`, `WorkbenchList.vue`
   - `AuditLog.vue`
   - `Login.vue`
   - `CurriculumRules.vue`
   - `OperationDashboard.vue`
   - `ImportCenter.vue`
   - `HonorList.vue`
   - `EntryList.vue`
   - `NoticeList.vue`
   - `StudentProfile.vue`, `Profile.vue`
   - `UserManage.vue`
   - `PartyStageList.vue`, `QuizBank.vue`
   - `Forbidden.vue`

### Miniapp 端
遵循“无外部重依赖、轻量化符号”的策略，利用文本 Emoji、Unicode 符号和少量样式控制为按钮补齐图标：
1. **全局统一样式**：在 `.action-btn`, `.primary-btn`, `.ghost-btn`, `.search-btn` 等基础按钮样式中增加 `display: inline-flex; align-items: center; justify-content: center;`，以确保文本图标与文字能垂直居中对齐，并新增 `.btn-icon` 规范间距与字号。
2. **首页 (`index.vue`)**：为数据同步按钮补充 `↻` 图标。
3. **事务申请 (`request/create.vue`, `request/detail.vue`)**：补充重选 (`↺`)、保存 (`💾`)、提交 (`🚀`)、附件 (`📎`)、预览 (`🔍`)、撤回 (`↩️`)、编辑 (`✏️`)。
4. **党团流程 (`workflow/quiz.vue`)**：补充开始 (`⚡`)、上一题 (`‹`)、下一题 (`›`)、提交 (`✓`)、再来一轮 (`↺`)。
5. **知识库与画像 (`knowledge/index.vue`, `profile/index.vue`)**：补充搜索 (`🔍`)、微信登录 (`❖`)、提交申诉 (`✓`)、提交补录 (`🚀`)。

## 验证项

- [x] Web 端执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json` 与 `pnpm -C web build` 均通过，无图标引用报错。
- [x] Miniapp 端执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 与 `pnpm -C miniapp build:mp-weixin` 均通过，页面样式无崩坏。
- [x] 验证 Web 各页面按钮图标正确渲染。
- [x] 验证 Miniapp 构建产物 `app.json` 完整。