# miniapp — 微信小程序学生端（uni-app）

**框架**: uni-app（Vue 3 基础）  
**目标平台**: 微信小程序（`mp-weixin`，唯一权威验收口径）  
**H5 说明**: 仅保留为本地临时预览入口，不作为需求完成态或交付验收依据  
**UI 约束**: 以微信小程序可用组件、交互约束和页面栈能力为准  
**HTTP / 文件能力**: `uni.request`、`uni.uploadFile`、`uni.downloadFile`  
**构建**: HBuilderX 或 CLI（主入口：`pnpm dev:mp-weixin` / `pnpm build:mp-weixin`）  

---

## 目录结构

```
miniapp/
├── pages/                             页面（按功能分目录）
│   ├── index/                         首页 / 服务入口
│   │   └── index.vue                  学生服务入口卡片式导航
│   ├── knowledge/                     知识库与政策查询 (FR-001~002)
│   │   ├── search.vue                 搜索入口（关键词 + 受控 AI 匹配）
│   │   ├── detail.vue                 知识条目详情（含来源、官方链接）
│   │   └── template-list.vue          模板下载列表 (FR-003)
│   ├── workflow/                      党团流程 (FR-004~005)
│   │   ├── party-progress.vue         党团进度可视化（当前阶段、下一动作）
│   │   ├── quiz.vue                   理论自测答题页
│   │   └── quiz-result.vue            自测结果与历史
│   ├── request/                       事务申请 (FR-006~008)
│   │   ├── list.vue                   我的申请列表（含状态筛选）
│   │   ├── create.vue                 新建申请（按类型动态表单）
│   │   ├── detail.vue                 申请详情（含审批流水、附件）
│   │   └── proof-preview.vue          证明 PDF 预览页 (FR-006)
│   ├── notice/                        通知中心 (FR-011)
│   │   ├── list.vue                   我的通知列表
│   │   └── detail.vue                 通知详情
│   ├── academic/                      学业分析 (FR-014) — 弱结论
│   │   └── gap-view.vue               学业缺口展示（含边界提示）
│   └── profile/                       个人中心
│       ├── index.vue                  基本信息（脱敏展示）
│       └── login.vue                  绑定学号 / 微信登录
├── components/                        公共组件
│   ├── StepProgress.vue               流程步骤进度条（党团阶段可视化）
│   ├── RequestTypeCard.vue            事务类型选择卡片
│   ├── BoundaryNotice.vue             "仅学院预检/非正式生效"提示组件（强制显示）
│   ├── AcademicBoundaryTip.vue        学业弱结论边界提示组件（强制显示）
│   └── FileUploadItem.vue             附件上传项
├── api/                               请求封装
│   ├── request.ts                     uni.request 封装（含 JWT header）
│   ├── knowledge.ts
│   ├── workflow.ts
│   ├── request-affairs.ts             事务申请接口
│   ├── notice.ts
│   └── academic.ts
├── store/                             状态管理（Pinia for uni-app）
│   └── auth.ts                        登录态、学生信息、角色
├── utils/
│   ├── format.ts                      日期/状态格式化
│   └── upload.ts                      文件选择与上传工具
├── src/static/                        静态资源（主图标、tabBar 图标、空态图，微信小程序资源从此目录出包）
├── pages.json                         页面路由配置
├── manifest.json                      应用配置（AppID、权限）
├── App.vue
├── main.ts
├── package.json
└── README.md
```

---

## 页面 → FR 映射

| 页面 | 对应 FR | 说明 |
|------|---------|------|
| `knowledge/search` | FR-001, FR-002 | 受控 AI 返回必须携带来源 |
| `knowledge/template-list` | FR-003 | 只读下载，不可上传 |
| `workflow/party-progress` | FR-004 | 展示当前阶段、下一动作 |
| `workflow/quiz` | FR-005 | 题库由管理端导入，学生答题 |
| `request/create` | FR-006 | 证明类型触发 PDF 预览入口 |
| `request/detail` | FR-007, FR-008 | 驳回后可重提，保留原表单内容 |
| `notice/list` | FR-011 | 仅展示本人相关通知 |
| `academic/gap-view` | FR-014 | 必须显示弱结论边界提示 |

---

## 快速启动

```bash
pnpm install

# H5 模式（仅临时预览，不作为验收依据）
pnpm dev:h5

# 微信小程序模式（权威开发 / 验收入口，需要 HBuilderX 或微信开发者工具）
pnpm dev:mp-weixin

# 生成微信开发者工具可导入产物
pnpm build:mp-weixin
```

---

## 颜色主题（来自 UI/UX 规格）

```
主色:       #A61E2D  （学院红）
深阶主色:   #7F1722
背景色:     #F8FAFC
卡片底色:   #FFFFFF
成功色:     #15803D
警告色:     #D97706
错误色:     #DC2626
```

---

## 注意事项

- `BoundaryNotice` 组件必须在所有"仅预检/非正式生效"场景强制渲染，不允许通过 props 隐藏。
- `AcademicBoundaryTip` 组件必须在学业缺口页面顶部强制渲染。
- 学生端不得展示未脱敏的身份证号、处分记录字段（权限由后端控制）。
- 申请附件上传限制：单文件 ≤ 30MB，支持 PDF/Word/图片格式。
- 新增或修改页面能力时，应优先检查是否符合微信小程序约束，例如页面栈、文件能力、登录能力、导航方式和审核可接受性；不要先按 H5 语义实现再被动适配。
- 微信开发者工具请先执行 `pnpm build:mp-weixin`，再导入 `miniapp/dist/build/mp-weixin`；也可以导入 `miniapp` 根目录，根目录的 `project.config.json` 已通过 `miniprogramRoot` 指向构建产物目录。`tabBar` 图标源码位于 `miniapp/src/static/`，不能只放在项目根目录的其他临时静态目录中。
- 小程序主图标资产位于 `miniapp/src/static/app-icon.png`，同时提供 `app-icon-512.png` 与 `app-icon-144.png` 尺寸变体；源脚本为 `scripts/miniapp/generate_app_icon.ps1`。微信小程序头像/图标最终仍需在微信公众平台后台上传该 PNG，代码构建只负责保留和出包项目内静态资产。
