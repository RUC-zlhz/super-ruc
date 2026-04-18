# 信息学院学生综合服务与党团管理平台

单仓仓库，包含需求规格、技术规格、交付文档，以及后端、管理端、学生端和部署配置。

## 仓库结构

```text
super-ruc/
├── backend/                     FastAPI 后端（uv 管理）
├── web/                         Vue 3 管理端
├── miniapp/                     uni-app 学生端
├── deploy/                      Docker Compose / Nginx 等部署配置
├── docs/
│   ├── source/                  原始需求输入与补充材料
│   ├── templates/               文档模板
│   ├── notes/                   过程记录与问题备注
│   ├── srs/                     正式 SRS 文档
│   └── architecture-decision-records/
├── specs/                       技术规格、分析模型、用例与 UI/UX 规格
├── output/
│   └── doc/                     SRS 交付件，保留全部版本
├── AGENTS.md                    Codex 协作约束
├── CLAUDE.md                    Claude Code 协作约束
├── pnpm-workspace.yaml          前端工作区定义
└── .gitattributes               跨平台行尾与二进制文件规则
```

## 快速开始

### 1. 启动基础设施

```powershell
docker compose -f deploy/docker-compose.yml up -d
```

### 2. 启动后端

```powershell
cd backend
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8080
```

### 3. 安装前端依赖

```powershell
pnpm install -r
```

### 4. 启动管理端 / 学生端

```powershell
pnpm -C web dev
pnpm -C miniapp dev:h5
```

## 文档约定

- `docs/source/` 保存需求输入原文与补充说明。
- `docs/templates/` 保存正式模板文件。
- `docs/notes/` 保存排版、修订和待确认事项。
- `output/doc/` 保留全部 SRS 版本，便于交付追溯。

## 提交约定

- 后端依赖与命令统一使用 `uv`。
- 前端依赖统一使用 `pnpm` 工作区。
- 严禁提交真实密钥、环境私密配置、Word 锁文件和临时构建目录。
