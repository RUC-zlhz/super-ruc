# web — 管理端 PC 网页

**框架**: Vue 3 + Vite + TypeScript  
**UI 库**: Ant Design Vue 4.x  
**状态管理**: Pinia  
**路由**: Vue Router 4  
**HTTP**: Axios  
**构建**: pnpm + Vite  

---

## 目录结构

```
web/
├── src/
│   ├── views/                         页面视图（按功能模块分目录）
│   │   ├── knowledge/                 知识库管理 (FR-001~003)
│   │   │   ├── EntryList.vue          知识条目列表
│   │   │   ├── EntryEdit.vue          新增/编辑知识条目
│   │   │   ├── TemplateList.vue       模板文件管理
│   │   │   └── SourceList.vue         知识来源治理
│   │   ├── workflow/                  党团流程管理 (FR-004~005)
│   │   │   ├── PartyStageList.vue     党团阶段列表
│   │   │   ├── ReminderConfig.vue     提醒规则配置
│   │   │   └── QuizBank.vue           理论自测题库
│   │   ├── approval/                  审批工作台 (FR-007~008)
│   │   │   ├── WorkbenchList.vue      待审列表（所有事务类型）
│   │   │   ├── ApprovalDetail.vue     审批详情（材料、历史、附件）
│   │   │   └── ApprovalHistory.vue    已办记录
│   │   ├── notice/                    通知管理 (FR-010~011)
│   │   │   ├── NoticeList.vue         通知列表
│   │   │   ├── NoticeCreate.vue       创建/编辑通知
│   │   │   ├── AudienceSelector.vue   目标人群圈选组件
│   │   │   └── DeliveryRecord.vue     发送记录
│   │   ├── exchange/                  导入导出 (FR-009)
│   │   │   ├── ImportCenter.vue       导入中心（上传、进度、错误报告）
│   │   │   └── ExportCenter.vue       导出中心
│   │   ├── academic/                  学业管理 (FR-014~015)
│   │   │   ├── CurriculumRules.vue    培养方案规则维护
│   │   │   └── AcademicGapAdmin.vue   学业缺口管理视图
│   │   ├── dashboard/                 统计看板 (FR-016)
│   │   │   └── OperationDashboard.vue 运营统计看板
│   │   ├── audit/                     审计与权限 (FR-012~013)
│   │   │   ├── AuditLog.vue           操作审计日志
│   │   │   └── RolePermission.vue     角色权限配置
│   │   └── system/                    系统配置
│   │       ├── UserManage.vue         用户/学生列表维护
│   │       └── TagManage.vue          标签管理
│   ├── components/                    全局公共组件
│   │   ├── layout/                    布局（侧边栏、顶部栏、面包屑）
│   │   ├── FileUploader.vue           通用文件上传组件
│   │   ├── StatusTag.vue              申请状态标签
│   │   └── BoundaryAlert.vue          校级边界提示组件（C-03 强制显示）
│   ├── api/                           Axios 接口封装（按后端模块分文件）
│   │   ├── knowledge.ts
│   │   ├── workflow.ts
│   │   ├── approval.ts
│   │   ├── notice.ts
│   │   ├── exchange.ts
│   │   ├── report.ts
│   │   └── auth.ts
│   ├── router/
│   │   └── index.ts                   路由配置（含角色守卫）
│   ├── store/
│   │   ├── auth.ts                    登录态、角色、权限
│   │   └── app.ts                     全局 UI 状态
│   ├── utils/
│   │   ├── request.ts                 Axios 实例 + 拦截器
│   │   ├── permission.ts              前端权限判断工具
│   │   └── download.ts                文件下载工具
│   ├── types/                         TypeScript 类型定义
│   ├── App.vue
│   └── main.ts
├── public/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
└── README.md
```

---

## 页面 → FR 映射

| 页面路径 | 对应 FR | 角色要求 |
|---------|---------|---------|
| `/knowledge/entries` | FR-001, FR-002, FR-003 | L1-L3 |
| `/knowledge/templates` | FR-003 | L1-L3 |
| `/workflow/party-stage` | FR-004, FR-005 | L3（团委老师）, L4 |
| `/workflow/quiz-bank` | FR-005 | L1-L3 |
| `/approval/workbench` | FR-007, FR-008 | L2-L4（按角色过滤） |
| `/notice/list` | FR-010, FR-011 | L1-L3 |
| `/exchange/import` | FR-009 | L1 |
| `/academic/curriculum` | FR-015 | L1-L3 |
| `/dashboard` | FR-016 | L1-L2 |
| `/audit/log` | FR-013 | L1 |
| `/audit/permissions` | FR-012 | L1 |

---

## 快速启动

```bash
pnpm install
pnpm dev        # 开发服务器，默认 http://localhost:5173
pnpm build      # 生产构建，输出到 dist/
pnpm preview    # 预览构建产物
```

---

## 颜色主题（来自 UI/UX 规格）

```
主色:       #A61E2D  （学院红）
深阶主色:   #7F1722
侧边导航:   #1E293B
内容区底:   #F5F7FA
成功色:     #15803D
警告色:     #D97706
错误色:     #DC2626
```
