# ADR-001: 技术选型

**状态**: 已确认
**日期**: 2026-04-15
**决策人**: 开发团队

---

## 背景

需在以下约束下选型：

1. 数据库**必须**兼容 Kingbase ES（人大金仓）
2. 团队语言偏好：**Python**
3. 学生端**优先**微信小程序
4. 管理端需适配 PC 浏览器（复杂查询、导入导出、统计）
5. 需支持受控 AI 问答（Claude API，有预算开关）
6. 并发规模小（≤50 并发），优先可维护性

---

## 决策

### 后端：Python 3.11 + FastAPI + SQLAlchemy 2.0 + Alembic

**理由**:

- 团队熟悉 Python，学习曲线最低
- FastAPI 原生 async/await，接口自动生成 OpenAPI 文档
- SQLAlchemy 2.0 async 模式 + asyncpg 驱动，与 Kingbase（PostgreSQL 兼容）无缝对接
- Alembic 版本化迁移，DDL 变更可追溯
- Anthropic Python SDK 直接可用，受控 AI 问答开发便捷

**关键依赖**:

| 包 | 用途 |
|---|---|
| fastapi, uvicorn | Web 框架 + ASGI 服务器 |
| sqlalchemy[asyncio], asyncpg | ORM + Kingbase 驱动 |
| alembic | 数据库迁移 |
| redis[asyncio] | 缓存 |
| minio | MinIO 文件存储 |
| python-jose, passlib | JWT + 密码哈希 |
| openpyxl | Excel 导入导出 |
| python-docx | Word 模板处理 |
| weasyprint | PDF 生成（证明预览） |
| anthropic | Claude API 受控问答 |
| pydantic-settings | 配置管理 |
| httpx | 微信 code2session 接口调用 |

### 管理前端：Vue 3 + Vite + Ant Design Vue 4.x

**理由**:

- Ant Design Vue 提供全面的企业组件（表格、表单、上传、权限控制）
- Vue 3 与 uni-app（学生端）共享语法和 Composition API，减少团队切换成本
- Vite 构建速度快

### 学生端：uni-app（Vue 3）→ 微信小程序（主）

**理由**:

- uni-app 一套代码主输出微信小程序，兼容 H5（未来无需重写）
- 基于 Vue 3，与管理前端共享技术栈和 API 调用逻辑
- 微信小程序 AppID 申请中，开发阶段用测试 AppID 推进

**替代方案（未选）**: 微信小程序原生（WXML/WXSS）无法输出 H5，舍弃跨端能力。

### 数据库：Kingbase ES（甲方强制）

- JDBC/asyncpg 连接串：`postgresql+asyncpg://user:pass@host:port/sip_db`
- 本地开发阶段用 `postgres:15-alpine` 镜像替代进行功能验证
- 上线前必须在真实 Kingbase 环境回归所有测试

### 缓存：Redis 7.x

- JWT 黑名单、角色权限缓存、导入批次状态缓存

### 文件存储：MinIO

- 存储 PDF 附件、Word 模板、Excel 导入原始文件
- 提供签名 URL 供前端直接下载，无需经过后端中转

### 受控 AI 问答：Anthropic Python SDK（按需启用）

- 默认模型：`claude-haiku-4-5`（成本低，延迟小）
- 配置开关：`AI_QA_ENABLED=false`（关闭时降级为关键词匹配）
- 返回内容必须携带 `knowledge_entry_id`，不允许输出无来源生成内容（约束 C-07）

---

## 已确认的关键业务决策

| 问题编号 | 问题 | 确认结果 | 影响 |
|---------|------|---------|------|
| Q-01 | 请假/证明/盖章是否允许学院平台正式生效 | **是** | 审批状态机终点为 `APPROVED`（正式生效），无需跳转校级系统 |
| Q-07 | 甲方是否能提供结构化培养方案 Excel | **是** | FR-014/FR-015 按原计划落地，不使用样例数据兜底 |
| AppID | 微信小程序 AppID | 申请中，可获得 | 开发阶段用测试 AppID；登录流程和消息推送按正式流程设计 |

---

## 后果与注意事项

- `asyncpg` 要求 PostgreSQL 协议版本兼容；Kingbase ES V9 支持 PostgreSQL 15 协议，需在上线前验证 `asyncpg` 连接串
- `weasyprint` 在 Windows 开发环境需要安装 GTK（建议在 WSL 或 Docker 内运行 PDF 生成相关测试）
- 微信小程序登录依赖 `wx.login()` → `code2session` 接口，需要 AppID + AppSecret 才能本地真实联调；开发阶段用 mock 登录绕过
- 培养方案 Excel 需要甲方提供标准字段格式后才能编写 `exchange/validators/curriculum.py` 的完整校验逻辑
