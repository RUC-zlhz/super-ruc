# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# CLAUDE.md — 信息学院学生综合服务与党团管理平台

> 本文件是 Claude Code Agent 的项目开发指南。每次进入项目时读取此文件以获取上下文。

## 项目概览

**项目名称**: 信息学院学生综合服务与党团管理平台（Student Integrated Platform, SIP）  
**版本**: 一期  
**业务域**: 高校学院级学生事务数字化  
**核心目标**: 一站式学生服务入口——官方知识查询 + 受控智能问答 + 党团流程可视 + 常见事务在线审批 + 精准通知触达 + 学业缺口弱提示 + 奖励荣誉展示 + 学生画像聚合

---

## 目录结构

```
super-ruc/
├── docs/                    需求与架构文档
│   ├── source/              原始需求输入（需求文档.md、需求补充.md、additional-request.txt）
│   ├── templates/           正式文档模板（软件需求规格说明书模板.docx）
│   ├── notes/               过程记录与待确认事项（pending-business-decisions.md、fix.md）
│   ├── srs/                 正式需求规格（FR-001~018, NFR-001~005, traceability-matrix）
│   └── architecture-decision-records/   ADR 技术决策记录（ADR-001-tech-stack.md）
├── specs/                   技术规格（数据模型、用例、UI/UX、分析模型）
│   └── 001-student-service-platform/
│       ├── spec.md, analysis-model.md, use-case-model.md
│       ├── ui-ux-spec.md, traditional-srs-supplement.md
│       └── checklists/
├── output/
│   └── doc/                 SRS 交付件，保留 v1.0 → v1.5 全部版本（含 v1.5-emf/ emf-inkscape 变体）
│
├── backend/                 后端 API 服务（Python 3.11 + FastAPI，uv 管理）
│   ├── app/                 各业务模块（见下文）
│   ├── alembic/             数据库迁移
│   ├── scripts/             运维脚本（seed_initial.py, archive_audit_logs.py, seed/）
│   ├── tests/               pytest（conftest.py + integration/）
│   ├── pyproject.toml       依赖声明（不再用 requirements.txt）
│   └── uv.lock
├── web/                     管理端 PC 网页（Vue 3 + Vite + Ant Design Vue 4.x）
├── miniapp/                 学生端（uni-app → 微信小程序为主，H5 兼容）
├── deploy/                  部署配置（docker-compose.yml + nginx/）
│
├── AGENTS.md                Codex 协作约束
├── CLAUDE.md                ← 本文件（Claude Code 协作约束）
├── README.md                仓库说明
├── pnpm-workspace.yaml      前端 pnpm 工作区（packages: web, miniapp）
├── .gitattributes           跨平台行尾/二进制规则
└── .gitignore
```

---

## 技术选型（已确认）

> 详见 `docs/architecture-decision-records/ADR-001-tech-stack.md`

| 层次 | 技术 | 说明 |
|------|------|------|
| 后端框架 | **Python 3.11 + FastAPI** | 异步、类型安全、开发效率高 |
| ORM | **SQLAlchemy 2.0**（async） | 支持 async/await，Kingbase/PostgreSQL 原生兼容 |
| 数据库迁移 | **Alembic** | 版本化 DDL 管理 |
| 数据库 | **Kingbase ES**（PostgreSQL 兼容） | 甲方强制要求 |
| DB 驱动 | `asyncpg`（异步）/ `psycopg2`（同步备选） | Kingbase 支持 PostgreSQL 协议 |
| 缓存 | **Redis 7.x**（redis-py asyncio） | 会话、权限缓存 |
| 文件存储 | **MinIO**（minio-py） | PDF/Word/Excel 附件存储 |
| 管理前端 | **Vue 3 + Vite + Ant Design Vue (antdv 4.x)** | 企业风格管理台 |
| 学生前端 | **uni-app**（Vue 3 基础） | 主输出微信小程序，H5 作为备用 |
| 构建工具 | **uv**（后端，pyproject.toml + uv.lock）+ **pnpm workspace**（前端 `web` / `miniapp`） | — |
| 受控 AI 问答 | **Anthropic Python SDK**（claude-haiku-4-5） | 需预算开关，默认关闭降级为关键词匹配 |
| Excel 处理 | `openpyxl` | 导入导出批次处理 |
| PDF 生成 | `weasyprint` 或 `reportlab` | 证明 PDF 预览（FR-006） |
| Word 处理 | `python-docx` | 模板文件读取与生成 |
| JWT | `python-jose` + `passlib` | 鉴权 |

---

## 核心闭环 → FR 映射

开发任务以六个闭环组织。**所有 18 个 FR 都是正式范围，不是每个闭环各自独立交付。**

| 闭环 | 对应 FR | 后端模块 | 前端模块 |
|------|---------|---------|---------|
| **知识库闭环** | FR-001, FR-002, FR-003 | `app/knowledge/` | 学生：知识查询页；管理：知识条目管理、模板管理 |
| **流程闭环** | FR-004, FR-005, FR-006 | `app/workflow/` | 学生：党团进度、事务申请；管理：党团阶段维护 |
| **审批闭环** | FR-007, FR-008 | `app/workflow/approval/` | 管理：审批工作台 |
| **通知闭环** | FR-010, FR-011 | `app/notice/` | 学生：通知中心；管理：通知发布、发送记录 |
| **审计闭环** | FR-009, FR-012, FR-013, FR-014, FR-015, FR-016 | `app/exchange/` + `app/audit/` + `app/report/` | 管理：导入导出、权限设置、审计日志、统计看板、学业分析 |
| **展示与画像闭环** | FR-017, FR-018 | `app/honor/` + `app/profile/` | 学生：荣誉榜单、本人画像；管理：荣誉维护、学生画像聚合视图 |

---

## 后端模块职责（`backend/app/`）

```
core/          配置、数据库连接、依赖注入、安全工具、对象存储、两个后台调度器
auth/          身份绑定、JWT 鉴权、角色加载（微信 code 换 openid + 学号绑定）
admin_users/   管理端账号（work_no 登录）的增删改查与角色分配
knowledge/     知识条目、标准答案、模板文件、受控 AI 匹配（Claude API）、来源治理
workflow/      党团阶段、节点提醒、自测题库（quiz_*）、事务申请、证明 PDF 预览（pdf_generator）、审批状态机（state_machine）
progress/      学生侧党团进度 / 申请进度的聚合只读视图
notice/        通知内容、标签、受控抓取/手工录入、目标人群、站内/邮件/短信发送
exchange/      Excel/Word/PDF 导入导出、批次管理、模板识别、校验与整批回滚（validators/ 按主数据类型分文件）
report/        统计看板、学业缺口展示、课程类型建议（弱结论）、成绩单 PDF
honor/         奖励荣誉公示（校级及以上）、榜样风采、归档/撤销
profile/       学生画像聚合（学籍 + 动态成长）、纠错申诉、敏感字段治理
audit/         操作日志、敏感访问记录、字段权限策略（policies / enforcement）
pdf_assets/    PDF 生成所需的字体 / 品牌素材（无代码逻辑，配合 core/pdf_branding）
```

> 注意：CLAUDE.md 闭环表里写的 `app/workflow/approval/` 是逻辑归类，实际审批状态机就在 `workflow/state_machine.py` + `workflow/service.py`，没有独立的 `approval/` 子包。

每个模块内部结构：
```
{module}/
├── router.py       FastAPI APIRouter，挂载路由
├── service.py      业务逻辑（调用 repo）
├── repository.py   数据库操作（SQLAlchemy）
├── models.py       SQLAlchemy ORM 模型
├── schemas.py      Pydantic 请求/响应 schema
└── deps.py         模块级依赖（可选）
```

### 新增接口的标准构件（跨文件约定）

- **路由注册**：一个模块通常导出多个 router（如 `router` 学生侧 / `admin_router` 管理侧 / `request_router` / `quiz_router`），**全部**在 [`app/main.py`](backend/app/main.py) 的 `create_app()` 里以 `settings.API_V1_PREFIX` 挂载。新加路由后必须回到 `main.py` `include_router`，否则不会生效。
- **统一响应**：返回类型用 `ApiResponse[T]`，正常路径用 [`app/core/response.py`](backend/app/core/response.py) 的 `ok(data)`；不要手写 `{code,message,data}`。
- **异常**：抛 `app/core/exceptions.py` 的 `BizError` / `AuthError`（401）/ `PermissionError`（403，可带自定义 `code` 如 `40311`），全局 handler 自动封装成统一包装体。不要直接 `raise HTTPException`。
- **鉴权与会话依赖**（来自 [`app/core/dependencies.py`](backend/app/core/dependencies.py)）：
  - `DBDep` = `Annotated[AsyncSession, Depends(get_db)]`
  - `CurrentUserDep` / `get_current_user`：解析 JWT，校验 `token_version`（改密 / 踢下线靠它失效旧 token）
  - `require_role("COUNSELOR", ...)`：角色门禁（C-03，权限只在后端判）
  - `ActiveStudentDep` / `require_active_enrollment`：**学生端写操作专用**，非在读学籍（休学/毕业/转出/归档）只读拦截
- **ORM 模型注册**：新建 `models.py` 后，须在 [`tests/conftest.py`](backend/tests/conftest.py) 与 `alembic/env.py` 的「导入所有模型」段落里 import，否则 `Base.metadata` 不含该表，建表 / TRUNCATE 都会漏。
- **两个后台调度器**：审计归档 + 党团节点提醒，定义在 `app/core/*_scheduler.py`，由 `lifespan` 按 `AUDIT_ARCHIVE_ENABLED` / `WORKFLOW_REMINDER_ENABLED` 开关启动（默认关）。
- **种子数据**：`scripts/seed/` 是一个包，导出 `SEEDERS` 列表（roles / audit_policies / request_types / workflow_templates / …）。`scripts/seed_initial.py` 和测试 conftest 都消费它；新增字典种子加到该列表即可同时覆盖运行期与测试。

---

## 已确认的关键业务决策

| 问题 | 确认结果 |
|------|---------|
| **Q-01** 请假/证明/盖章是否允许学院平台正式生效 | **是** — 学院平台审批即正式生效，无需跳转校级系统 |
| **Q-07** 甲方是否能提供结构化培养方案 Excel | **是** — 甲方可提供；FR-014/FR-015 按原计划落地 |
| **微信小程序 AppID** | 尚未申请，但可申请到；开发阶段用测试 AppID 推进 |

---

## 关键约束（每位开发者必读）

### C-01: 数据库只用 Kingbase
所有 DDL 必须兼容 Kingbase ES（PostgreSQL 协议）。不使用 MySQL 专有语法。  
本地开发阶段用 PostgreSQL 15 替代；上线前必须在真实 Kingbase 环境回归。  
Alembic migration 使用 `postgresql+asyncpg://` 连接串（Kingbase 兼容）。

### C-02: 不依赖校级 API
系统不能以校级"微人大"接口为前置条件。所有主数据通过 Excel 导入维护。

### C-03: 权限与审计必须在后端执行
所有权限判断（`Depends(require_role(...))`）、字段可见性控制、审计日志写入在 FastAPI 服务端完成，不得依赖前端隐藏。

### C-04: 敏感字段最小暴露
`身份证号`、`联系方式`、`处分记录`、`政治面貌`、`成绩` 等字段：
- 存储必须加密（`cryptography` 库 AES-256 或 Fernet）
- Pydantic schema 返回时按角色脱敏
- 所有访问写审计日志（`audit_log` 表）

### C-05: 学业模块只做弱结论
FR-014/FR-015 的任何分析结果**不得**输出"可以毕业"/"学分已满足"等强结论。  
前端必须显示边界提示：
> 本结果仅为辅助提示，不构成毕业资格、课程替代或教务最终结论；请以学院/学校正式审核结果为准。

### C-06: 文件导入整批原子提交
Excel 主数据导入：存在任一 `fatal` 级错误 → 整批回滚（使用 SQLAlchemy `async with session.begin()` 事务），正式表不落库。

### C-07: 受控 AI 问答必须有来源
知识查询的 AI 匹配返回内容必须携带 `knowledge_entry_id` 和官方来源链接。  
由配置开关 `settings.AI_QA_ENABLED` 控制，`False` 时降级为关键词匹配，不调用 Claude API。  
注意：`config.py` 的生产守卫 `_enforce_prod_invariants` 目前**强制** `AI_QA_ENABLED=False`（一期仅检索式），改这个开关会让 Settings 启动即报错。同类被守卫的开关还有 `WORKFLOW_REMINDER_CHANNEL` 仅 `IN_APP`、prod 下禁用 `WECHAT_MOCK_ENABLED` 等。

### C-08: 持久化实现计划（每次会话必读 / 必回写）
> 与 `AGENTS.md` 一致——这是工作记录的权威纪律，不是可选项。

- 全局实现计划唯一权威主文件：[`docs/notes/current-implementation-plan.md`](docs/notes/current-implementation-plan.md)。**新会话开始先读它**；有关联细化文件一并读。
- 任何新确认的细化方案 / 范围调整 / 阶段拆分，**新增独立文件**放 `docs/notes/refinements/`，并在主计划登记关联与状态。
- 每完成一段实质工作，回写主计划与相关细化文件，状态标记：`[ ]` 未开始 / `[-]` 进行中 / `[x]` 已完成 / `[!]` 阻塞。
- 不得静默丢弃旧计划；被替换的只能标「已替代/已失效」并留引用。未在主计划登记的笔记（`fix.md`、`pending-business-decisions.md` 等）默认是参考材料，不能直接当执行依据。

---

## 角色权限层级

| 级别 | 角色 | 典型操作 |
|------|------|---------|
| L1 | 超级管理员 | 全量配置、导入导出、权限管理、审计查看 |
| L2 | 学院领导 | 关键审批、统计看板查看 |
| L3 | 辅导员/班主任/团委老师/党建老师 | 审批、知识维护、通知发布、党团阶段维护 |
| L4 | 班团骨干（党支部书记/团支书/班长） | 职责范围内的流程初审、汇总查看 |
| L5 | 学生 | 查询、申请、查看本人状态、接收通知 |

> 助教不进入审批责任链（业务约束）。

---

## 审批边界（已确认：学院平台正式生效）

一期范围内，**请假、证明、盖章** 在学院平台审批通过即为正式生效，无需跳转校级系统。  
审批状态机终点：`APPROVED`（正式生效）/ `REJECTED`（驳回，允许重提）。

---

## API 规范

- RESTful，版本前缀 `/api/v1/`
- 所有接口返回统一包装体：`{ "code": 0, "message": "ok", "data": {...} }`
- 分页参数：`?page=1&size=20`（1-based，FastAPI `Query` 参数）
- 文件上传：`UploadFile`（FastAPI 原生），限制 30MB
- JWT 放 `Authorization: Bearer <token>` header
- 异常：FastAPI `HTTPException` + 全局 `exception_handler`

---

## 数据库命名规范（Kingbase/PostgreSQL）

| 规则 | 示例 |
|------|------|
| 表名 snake_case 复数 | `knowledge_entries`, `party_member_statuses` |
| 主键 | `id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)` |
| 外键 | `student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))` |
| 时间戳 | `created_at: Mapped[datetime]`（`server_default=func.now()`）, `updated_at` |
| 软删除 | `deleted_at: Mapped[datetime \| None]`（NULL = 存活） |
| 敏感字段 | 后缀 `_enc`（如 `id_card_enc`）表示加密存储，类型 `Text` |

---

## 开发环境快速启动

```bash
# 启动基础设施（在仓库根目录）
docker compose -f deploy/docker-compose.yml up -d

# 后端（统一用 uv）
cd backend
uv sync --extra dev            # 安装 runtime + dev 依赖（pytest/ruff/black/mypy 等）
uv run alembic upgrade head    # 初始化数据库表结构
uv run uvicorn app.main:app --reload --port 8080

# 前端（根目录即可，pnpm workspace）
pnpm install -r
pnpm -C web dev                # 管理端 http://localhost:5173
pnpm -C miniapp dev:h5         # 学生端 H5 调试
pnpm -C miniapp dev:mp-weixin  # 学生端 微信小程序（需 HBuilderX 或微信开发者工具）
```

**端口映射** — docker-compose 默认值均避让本机同名服务：
| 服务 | 容器内 | 宿主机 |
|------|--------|--------|
| Kingbase/PG | 5432 | **54322**（本机 54321 已被真实 Kingbase 服务占用） |
| Redis | 6379 | 6379 |
| MinIO API | 9000 | **9010** |
| MinIO Console | 9001 | **9011** |
| MailHog SMTP / UI | 1025 / 8025 | 1025 / 8025 |

### 代码质量命令（提交前自检）

```bash
# 后端（cd backend）— ruff/black/mypy 配置都在 pyproject.toml
uv run ruff check app tests       # lint（line-length=110，已选 E/F/I/B/UP/N/S）
uv run ruff check --fix app tests # 自动修复
uv run black app tests            # 格式化
uv run mypy app                   # 类型检查

# 前端
pnpm -C web lint                  # eslint（.ts/.vue）
pnpm -C web build                 # vue-tsc --noEmit 类型检查 + vite 构建
```

### 集成测试
测试库与开发库共用同一 docker-compose Postgres 实例，但使用独立 database（`sip_db_test`）：

```bash
# 首次：创建测试库
python -c "import asyncio, asyncpg; asyncio.run(asyncpg.connect(dsn='postgresql://sip_user:sip_pass_dev@localhost:54322/postgres').close())"
# 或手动 CREATE DATABASE sip_db_test;

cd backend
uv run pytest                       # 跑全部（testpaths = tests + unit_tests）
uv run pytest tests/integration -v  # 只跑集成测试
uv run pytest unit_tests -v         # 只跑纯单元测试（无需 DB）

# 单个文件 / 单个用例
uv run pytest tests/integration/test_request_flow.py -v
uv run pytest tests/integration/test_request_flow.py::test_某用例 -v
uv run pytest -k "request and reject" -v   # 按名字过滤
```

- `pyproject.toml` 的 `testpaths = ["tests", "unit_tests"]`，`asyncio_mode = "auto"`，临时文件落在 `.tmp/`。
- `tests/conftest.py`：session 级 drop+create schema 并塞种子；**每个 test 前** TRUNCATE 全部业务表 + 重塞种子，避免 service 层自 commit 与 SAVEPOINT-rollback 冲突。新增 ORM 模型记得在此 import（见上文「标准构件」）。
- 关键 fixtures：`client`（进程内 ASGI，不起端口）、`admin_client`（带 SUPER_ADMIN token）、`counselor_headers`（COUNSELOR，按请求独立携带避免覆盖 Authorization）、`db`（直连 DB 做 arrange/assert）。
- 目录：`tests/integration/`（各闭环 happy-path + 回归）、`unit_tests/`（纯函数 / 校验器 / 模板引擎，离线）、`tests/performance/`（导入基准）。
- `scripts/seed_initial.py`：初始化种子数据；`scripts/archive_audit_logs.py`：审计日志归档脚本；`scripts/dev/`：本地 Kingbase bootstrap / 库重置 / S4·S14 验收闸门脚本。

---

## 参考文件

- 需求源文件：`docs/source/需求文档.md`，`docs/source/需求补充.md`，`docs/source/additional-request.txt`
- 文档模板：`docs/templates/软件需求规格说明书模板.docx`
- 正式需求规格：`docs/srs/` 目录（FR-001~018, NFR-001~005, `traceability-matrix.md`）
- 技术规格：`specs/001-student-service-platform/spec.md`
- UI/UX 规格：`specs/001-student-service-platform/ui-ux-spec.md`
- 数据模型：`specs/001-student-service-platform/analysis-model.md`
- 用例模型：`specs/001-student-service-platform/use-case-model.md`
- SRS 补充：`specs/001-student-service-platform/traditional-srs-supplement.md`
- 待确认决策：`docs/notes/pending-business-decisions.md`
- 过程备注：`docs/notes/fix.md`
- 技术选型 ADR：`docs/architecture-decision-records/ADR-001-tech-stack.md`
- SRS 最新交付件：`output/doc/软件需求规格说明书-信息学院学生综合服务与党团管理平台-v1.5.docx`（及 v1.5-emf / v1.5-emf-inkscape 变体）
