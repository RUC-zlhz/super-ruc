# miniapp — 学生端（uni-app）

**框架**: uni-app（Vue 3 基础）  
**目标平台**: 微信小程序（主）+ H5（兼容）  
**UI 库**: uni-ui 或 uv-ui（兼容微信小程序和 H5）  
**HTTP**: uni.request 封装 / axios（H5 模式）  
**构建**: HBuilderX 或 CLI（`pnpm dev:mp-weixin` / `pnpm dev:h5`）  

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
├── static/                            静态资源（图标、空态图）
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

# H5 模式（开发调试方便）
pnpm dev:h5

# 微信小程序模式（需要 HBuilderX 或微信开发者工具）
pnpm dev:mp-weixin
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
