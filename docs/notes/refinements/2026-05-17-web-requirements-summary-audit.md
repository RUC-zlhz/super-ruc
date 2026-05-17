# Web 需求总结对照核查

- 创建日期：`2026-05-17`
- 状态：`[x]`
- 关联主计划：`S1 ~ S22（现状复核）`
- 输入依据：`需求总结.docx`

## 目标

对照《需求总结.docx》中按会议转写整理的需求点，复核当前仓库 `web` 端的真实实现范围，明确哪些能力已在老师/管理员后台落地，哪些仍只是部分对齐，哪些实际属于 `miniapp` 或全平台范围而不应计入 Web 已实现。

## 审计范围

- 前端代码：`web/src`
- 必要时补充核对少量后端契约/注释，用于确认 Web 所消费 API 的真实业务边界
- 当前线程验证：`& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json`、`web` 目录下 `& '.\node_modules\.bin\\vite.CMD' build`

## 结论概览

### 已实现

- 老师/管理员侧复杂工作台已基本齐备：知识库治理、通知中心、审批工作台、证明 PDF 预览/下载、导入导出中心、默认数据导入、成绩单 PDF 教师核验、荣誉公示管理、学生画像与敏感字段申请、运营看板/学业缺口、培养方案管理、审计日志。
- Web 当前真实定位是“信息学院管理后台”，而不是覆盖学生端场景的统一 Web 前台。

### 部分实现 / 与需求摘要仍有差距

- 角色层级虽然建模到班团骨干与学生，但 Web 路由/菜单实际只向老师与管理员角色开放，未真正把“团支书等团干部具备管理员权限”落实到 Web 可用入口。
- Web 登录当前仅支持 `工号 + 密码`，未提供需求摘要中提到的“微信登录或学校统一账号”式 Web 登录口径，也没有完整的 Web 端绑定流程。
- 党团流程页已有模板、学生流程、节点提醒生成入口，但“提醒规则查询接口暂未接通”，学生节点推进/完成记录深度也不足，仍未达到“固定流程 + 大致提醒时间”的完整闭环。
- 通知来源管理已支持公开 `URL / RSS` 抓取，但 Web 通知模块没有像知识库那样显式维护“官方来源”标识或优先级口径；对“官方平台公众号为准、非官方来源不建议采用”的需求只做到了部分贴合。
- 请假在 Web 审批侧仍被当作普通事务类型处理；虽然支持“转线下办理”，但没有明确把“本平台不作为正式请假渠道”的业务边界写到 Web 审批界面上。
- 画像页已实现学生基础字段脱敏、非在读只读与完整查看申请，但对 API 中 `hidden_sensitive_fact_count`、敏感事实完整查看等深层治理字段尚未形成完整 Web 展示。
- 工作量记录目前主要通过画像成长事实、时长字段和党团流程概览间接承载，没有单独的“学生组织日常工作量”专门工作台。

### 不应直接计入 Web 已实现

- 学生身份绑定、学生登录、学生问答使用流程、学生端消息接收等需求更接近 `miniapp` 或后端能力，不属于当前 `web` 端的主范围。

## 关键证据

- 角色与路由：`web/src/utils/permission.ts`、`web/src/router/index.ts`、`web/src/config/navigation.ts`
- 登录与账号：`web/src/views/Login.vue`、`web/src/api/auth.ts`、`web/src/views/Profile.vue`
- 通知中心：`web/src/views/notice/NoticeList.vue`、`web/src/api/notice.ts`
- 知识库治理：`web/src/views/knowledge/EntryList.vue`、`web/src/api/knowledge.ts`
- 审批与证明：`web/src/views/approval/WorkbenchList.vue`、`web/src/views/approval/ApprovalDetail.vue`、`web/src/api/workflow.ts`
- 导入与核验：`web/src/views/exchange/ImportCenter.vue`、`web/src/api/exchange.ts`
- 画像与学籍：`web/src/views/profile/StudentProfile.vue`、`web/src/views/system/UserManage.vue`、`web/src/api/profile.ts`
- 荣誉与看板：`web/src/views/honor/HonorList.vue`、`web/src/views/dashboard/OperationDashboard.vue`
- 党团流程与提醒：`web/src/views/workflow/PartyStageList.vue`
- 审计：`web/src/views/audit/AuditLog.vue`、`web/src/api/audit.ts`

## 验证结果

- `web` 类型检查通过：`vue-tsc --noEmit -p web\tsconfig.json`
- `web` 生产构建通过：`vite build`

## 结论

当前 Web 端已经能够支撑老师/管理员侧的大部分复杂校务治理任务，但它并不是“需求总结中所有角色、所有场景”的完整 Web 实现。若要严格宣称“Web 端已完整实现需求总结”，至少还需要继续补齐：班团骨干角色入口、Web 登录口径对齐、党团提醒规则闭环、通知官方来源治理表达，以及若干业务边界文案与深层治理展示。
