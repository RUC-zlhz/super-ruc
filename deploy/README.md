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

## 生产部署

> 生产部署脚本待编写，参考以下流程：

1. 替换 docker-compose.yml 中的占位镜像为 Kingbase 官方镜像
2. 将所有密码/密钥改为环境变量或 Docker Secrets
3. 开启 HTTPS（Nginx SSL 配置）
4. 配置 MinIO 持久化存储和备份策略
5. 配置 Redis 持久化（AOF）

## 目录说明

```
deploy/
├── docker-compose.yml   本地开发环境编排
├── nginx/
│   └── nginx.conf       Nginx 反向代理配置
└── README.md
```
