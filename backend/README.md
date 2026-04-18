# backend — 后端 API 服务

**运行时**: Python 3.11+
**框架**: FastAPI (async)
**ORM**: SQLAlchemy 2.0 (async, mapped_column 风格)
**迁移**: Alembic
**数据库**: Kingbase ES（PostgreSQL 兼容，asyncpg 驱动）
**缓存**: Redis 7.x (redis-py asyncio)
**文件存储**: MinIO (minio-py)

---

## 目录结构

```
backend/
├── app/
│   ├── main.py                    FastAPI app 创建、路由挂载、中间件
│   ├── core/
│   │   ├── config.py              pydantic-settings 全局配置
│   │   ├── database.py            async engine、SessionLocal、Base
│   │   ├── security.py            JWT 签发/校验、密码哈希、字段加解密
│   │   ├── dependencies.py        get_db、get_current_user、require_role
│   │   └── exceptions.py          全局异常处理器
│   │
│   ├── auth/                      身份绑定 / JWT / 角色 (无 FR，支撑全局)
│   │   ├── router.py              POST /api/v1/auth/wx-login
│   │   │                          POST /api/v1/auth/refresh
│   │   ├── service.py             微信 code2session、学号绑定、JWT 签发
│   │   ├── repository.py          User / Role / Permission 数据库操作
│   │   ├── models.py              User, Role, UserRole ORM 模型
│   │   └── schemas.py             WxLoginRequest, TokenResponse, UserInfo
│   │
│   ├── knowledge/                 知识库闭环 FR-001, FR-002, FR-003
│   │   ├── router.py              GET  /api/v1/knowledge/search
│   │   │                          GET  /api/v1/knowledge/{id}
│   │   │                          POST /api/v1/knowledge/ai-match
│   │   │                          CRUD /api/v1/admin/knowledge/entries
│   │   │                          CRUD /api/v1/admin/knowledge/templates
│   │   │                          CRUD /api/v1/admin/knowledge/sources
│   │   ├── service.py             关键词匹配、Claude API 受控问答、来源版本化
│   │   ├── repository.py
│   │   ├── models.py              KnowledgeEntry, KnowledgeSource, TemplateAsset
│   │   └── schemas.py
│   │
│   ├── workflow/                  流程 + 审批闭环 FR-004~008
│   │   ├── router.py              GET  /api/v1/workflow/party-status/{student_id}
│   │   │                          POST /api/v1/requests/           (提交申请)
│   │   │                          GET  /api/v1/requests/{id}
│   │   │                          POST /api/v1/requests/{id}/withdraw
│   │   │                          POST /api/v1/admin/requests/{id}/approve
│   │   │                          POST /api/v1/admin/requests/{id}/reject
│   │   │                          GET  /api/v1/workflow/proof-preview/{request_id}
│   │   │                          CRUD /api/v1/admin/quiz-bank
│   │   │                          POST /api/v1/quiz/submit
│   │   ├── service.py             审批状态机、证明 PDF 生成、党团阶段推进
│   │   ├── state_machine.py       ApprovalStateMachine (PENDING→APPROVED/REJECTED/WITHDRAWN)
│   │   ├── pdf_generator.py       weasyprint/reportlab 证明 PDF 预览
│   │   ├── repository.py
│   │   ├── models.py              PartyMemberStatus, CommonRequest, ApprovalRecord,
│   │   │                          RequestAttachment, QuizQuestion, QuizRecord
│   │   └── schemas.py
│   │
│   ├── notice/                    通知闭环 FR-010, FR-011
│   │   ├── router.py              CRUD /api/v1/admin/notices
│   │   │                          POST /api/v1/admin/notices/{id}/send
│   │   │                          GET  /api/v1/notices/           (学生侧)
│   │   │                          GET  /api/v1/admin/notices/{id}/delivery
│   │   ├── service.py             目标人群解析、站内/邮件/短信发送、受控抓取入口
│   │   ├── audience.py            AudienceResolver: 按年级/专业/班级/角色圈选
│   │   ├── sender.py              EmailSender, SMSSender（短信有开关）
│   │   ├── repository.py
│   │   ├── models.py              Notice, NoticeTag, DeliveryBatch, DeliveryRecord
│   │   └── schemas.py
│   │
│   ├── exchange/                  文件交换 + 主数据 FR-009, FR-015
│   │   ├── router.py              POST /api/v1/admin/import/students
│   │   │                          POST /api/v1/admin/import/curriculum
│   │   │                          POST /api/v1/admin/import/{batch_id}/commit
│   │   │                          GET  /api/v1/admin/import/{batch_id}/errors
│   │   │                          GET  /api/v1/admin/export/requests
│   │   ├── service.py             批次登记、模板识别、结构/业务校验、整批原子提交
│   │   ├── validators/            per-type 校验器（students, curriculum, notices）
│   │   ├── repository.py
│   │   ├── models.py              ImportBatch, ImportBatchRow, Student,
│   │   │                          CurriculumModule, CourseOffering
│   │   └── schemas.py
│   │
│   ├── report/                    统计 + 学业风险 FR-014, FR-016
│   │   ├── router.py              GET /api/v1/students/{id}/academic-gap
│   │   │                          GET /api/v1/admin/dashboard
│   │   ├── service.py             学业缺口计算（弱结论）、运营统计聚合
│   │   ├── repository.py
│   │   └── schemas.py
│   │
│   └── audit/                     审计 + 权限 FR-012, FR-013
│       ├── router.py              GET  /api/v1/admin/audit-logs
│       │                          CRUD /api/v1/admin/role-policies
│       ├── service.py             权限策略评估、日志写入
│       ├── repository.py
│       ├── models.py              AuditLog, RoleFieldPolicy
│       └── schemas.py
│
├── alembic/                       数据库版本迁移
│   ├── versions/
│   │   ├── 0001_auth.py
│   │   ├── 0002_knowledge.py
│   │   ├── 0003_workflow.py
│   │   ├── 0004_notice.py
│   │   ├── 0005_exchange.py
│   │   ├── 0006_report_academic.py
│   │   └── 0007_audit.py
│   └── env.py
│
├── tests/
│   ├── conftest.py                pytest fixtures (async db session, test client)
│   ├── test_auth.py
│   ├── test_knowledge.py
│   ├── test_workflow.py
│   └── test_exchange.py           重点测试整批原子提交回滚
│
├── requirements.txt
├── requirements-dev.txt           pytest, httpx, black, ruff 等
├── alembic.ini
├── .env.example                   环境变量模板（不含真实密钥）
└── README.md
```

---

## 模块 → FR 映射

| 模块包 | 负责 FR | 核心能力 |
|--------|---------|---------|
| `auth` | — | 微信 code2session + 学号绑定、JWT 签发、角色权限加载 |
| `knowledge` | FR-001, 002, 003 | 知识条目 CRUD、标准答案、受控 Claude API 问答、模板文件管理、来源版本化 |
| `workflow` | FR-004, 005, 006, 007, 008 | 党团阶段、节点提醒、理论自测、事务申请、证明 PDF 预览、审批状态机 |
| `notice` | FR-010, 011 | 通知创建、标签管理、受控抓取/手工录入、目标人群圈选、站内/邮件/短信投递 |
| `exchange` | FR-009, 015 | Excel/Word/PDF 导入导出、批次管理、整批原子提交、模板识别、错误报告 |
| `report` | FR-014, 016 | 学业缺口展示（弱结论）、课程类型建议、运营统计看板 |
| `audit` | FR-012, 013 | 字段权限策略、角色-字段矩阵、操作审计日志、敏感访问记录 |

---

## 快速启动（使用 uv 管理依赖）

```bash
# 0. 安装 uv（若未安装）
# Windows PowerShell: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS/Linux:        curl -LsSf https://astral.sh/uv/install.sh | sh

# 1. 启动基础设施
docker compose -f ../deploy/docker-compose.yml up -d

# 2. 同步依赖（会自动创建 .venv）
uv sync                        # 仅运行时依赖
uv sync --extra dev            # 连同开发依赖一起安装

# 3. 配置环境变量
cp .env.example .env           # 按需修改 DATABASE_URL / REDIS_URL / MINIO / JWT_SECRET_KEY / FIELD_ENCRYPTION_KEY

# 4. 初始化数据库
uv run alembic upgrade head

# 5. 启动开发服务器
uv run uvicorn app.main:app --reload --port 8080
# API 文档: http://localhost:8080/docs
```

常用命令:

```bash
uv add <package>               # 新增运行时依赖（自动写入 pyproject.toml）
uv add --dev <package>         # 新增开发依赖
uv lock                        # 生成/更新 uv.lock
uv run alembic revision --autogenerate -m "msg"
uv run pytest
uv run ruff check .
```

---

## 核心依赖（由 pyproject.toml 管理）

| 包 | 作用 |
|---|---|
| fastapi / uvicorn | Web 框架 + ASGI server |
| sqlalchemy[asyncio] + asyncpg | Kingbase / PostgreSQL async ORM |
| alembic | 数据库迁移 |
| redis[hiredis] | 缓存 / 会话 |
| minio | 附件与模板对象存储 |
| python-jose + passlib | JWT 与密码哈希 |
| cryptography | 敏感字段 Fernet 加密（C-04） |
| pydantic + pydantic-settings | Schema 与配置 |
| httpx | 微信 code2session 等外部 HTTP |
| openpyxl / python-docx / weasyprint | Excel/Word/PDF 处理 |
| anthropic | 受控 AI 问答 (FR-002)，由 `AI_QA_ENABLED` 开关控制 |

---

## 关键约束提醒

- **Kingbase 连接串**: `postgresql+asyncpg://user:pass@host:54322/sip_db`（dev docker-compose 端口；真实 Kingbase 生产环境按运维配置）
- **敏感字段加密**: `身份证号`、`手机号` 用 `cryptography.fernet.Fernet` 加密，字段名后缀 `_enc`
- **审计日志**: 审批、导出、权限变更、内容停用必须调用 `audit.service.log_action()`
- **整批原子**: `exchange/service.py` 导入方法用 `async with session.begin()` 包裹全部写操作
- **AI 开关**: `settings.AI_QA_ENABLED = False` 时跳过 Anthropic API，返回关键词匹配结果
