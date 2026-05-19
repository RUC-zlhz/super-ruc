# deploy — 部署配置

## 本地开发环境

```bash
# 启动基础设施（Kingbase/PostgreSQL、Redis、MinIO、MailHog）
docker compose up -d

# 查看服务状态
docker compose ps

# 停止
docker compose down
```

服务端口汇总：

| 服务 | 端口 | 说明 |
|------|------|------|
| Kingbase (dev: PostgreSQL) | `54322` | JDBC URL: `jdbc:postgresql://localhost:54322/sip_db`（避让本机 54321 上已有的 Kingbase 服务） |
| Redis | `6379` | 密码: `sip_redis_dev` |
| MinIO API | `9010` | AccessKey: `sip_minio` / SecretKey: `sip_minio_dev`（外部映射 9010→9000，避让本机 9000 可能的 Python 服务） |
| MinIO Console | `9011` | 浏览器管理界面（外部 9011→9001） |
| MailHog SMTP | `1025` | 本地邮件捕获 |
| MailHog UI | `8025` | 查看捕获邮件：http://localhost:8025 |

## 内网生产部署（S28）

`deploy/intranet-prod/` 是当前内网生产首阶段入口，目标服务器为 `10.10.0.13`：

- Docker Compose 编排 PostgreSQL 15、Redis、MinIO、FastAPI 后端与 Web 管理端。
- 服务目录固定为 `/opt/super-ruc/app`，备份目录固定为 `/opt/super-ruc/backups`。
- 真实密钥只写入服务器侧 `deploy/intranet-prod/.env`，不落仓库。
- 本阶段仅承诺内网 HTTP 访问，不处理公网域名、HTTPS、微信正式合法域名。

入口文档：`deploy/intranet-prod/README.md`

## 旧临时 IP 部署

`deploy/temp-ip/` 保留为 `123.57.54.195` 临时直连部署记录。后续新部署优先使用 `deploy/intranet-prod/`。

## 目录说明

```
deploy/
├── docker-compose.yml   本地开发环境编排
├── intranet-prod/       S28 内网生产部署与持续交付底座
├── nginx/
│   └── nginx.conf       Nginx 反向代理配置
├── temp-ip/             旧临时 IP 直连部署资产
└── README.md
```
