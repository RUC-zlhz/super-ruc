# S28 内网生产部署

本目录用于 `10.10.0.13` 内网生产首阶段部署。该阶段只承诺内网 HTTP 访问，不处理公网域名、HTTPS、微信正式合法域名。

## 架构

- `web`：多阶段 Docker 构建 `web/dist`，Nginx 监听 `80`。
- `backend`：复用 `backend/Dockerfile`，FastAPI 容器内监听 `8080`。
- `db`：PostgreSQL 15 兼容数据库，持久化 volume。
- `redis`：Redis 7，开启 AOF。
- `minio`：附件、模板、导出文件对象存储。

对外入口：

- Web 管理端：`http://10.10.0.13/`
- 后端健康检查：`http://10.10.0.13/healthz`
- API 基址：`http://10.10.0.13/api/v1`

## 服务器初始化

首次在服务器执行：

```bash
ssh user@10.10.0.13
sudo -n true
bash deploy/intranet-prod/scripts/bootstrap-server.sh
```

如果服务器暂时无法访问 Ubuntu 官方源，需要先选择现场可访问的镜像源：

```bash
UBUNTU_MIRROR=https://mirrors.tuna.tsinghua.edu.cn bash deploy/intranet-prod/scripts/bootstrap-server.sh
```

如果服务器本身没有公网出口，可以先在本机起一个临时代理，再把它通过 SSH 反向转发到服务器：

```bash
# 在本机保持该 SSH 连接打开，服务器侧会得到 127.0.0.1:18080 SOCKS 代理
ssh -N -R 127.0.0.1:18080 user@10.10.0.13

# 在服务器的另一个 SSH 会话里执行
PROXY_URL=socks5h://127.0.0.1:18080 bash deploy/intranet-prod/scripts/bootstrap-server.sh
```

该方式会把 Docker daemon 的代理持久配置为 `socks5h://127.0.0.1:18080`，后续拉镜像时需要保持对应 SSH 反向隧道打开，或改为正式代理/正式出网。

Docker build 阶段还需要容器内的 `apt / pip / corepack / pnpm` 能访问公网。服务器没有直接出网时，在服务器上启动本目录内的 HTTP-to-SOCKS 转发代理：

```bash
cd /opt/super-ruc/app
nohup python3 -u deploy/intranet-prod/scripts/http_proxy.py \
  >/tmp/super-ruc-build-proxy.log 2>&1 &
```

默认 `.env.example` 已将 `BUILD_HTTP_PROXY / BUILD_HTTPS_PROXY` 指到 `http://127.0.0.1:18081`，Compose build 会使用 host network 访问该代理。

如果仓库尚未放到 `/opt/super-ruc/app`，在 `git` 可用后执行：

```bash
git clone https://github.com/RUC-zlhz/super-ruc.git /opt/super-ruc/app
cd /opt/super-ruc/app
```

## 生产环境变量

创建服务器侧 `.env`，真实密钥只保存在服务器，不写入 Git：

```bash
cd /opt/super-ruc/app
cp deploy/intranet-prod/.env.example deploy/intranet-prod/.env
vi deploy/intranet-prod/.env
```

生成密钥示例：

```bash
openssl rand -base64 48
python3 - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
```

注意：

- `JWT_SECRET_KEY`、`FIELD_ENCRYPTION_KEY`、`WECHAT_APPID`、`WECHAT_SECRET` 必须替换。
- `DATABASE_URL` 与 `REDIS_URL` 中的密码需要 URL encode，或仅使用字母数字安全字符。
- S28 不使用 S27 开发冷启动，不清空学生、账号、微信绑定和业务数据。

## 部署

部署指定分支或 commit：

```bash
cd /opt/super-ruc/app
bash deploy/intranet-prod/scripts/deploy.sh main
bash deploy/intranet-prod/scripts/migrate-and-seed.sh
bash deploy/intranet-prod/scripts/smoke.sh
```

如果服务器没有 GitHub 凭据，且仓库内容是从本机同步到 `/opt/super-ruc/app` 的，可以直接用当前工作树部署：

```bash
cd /opt/super-ruc/app
bash deploy/intranet-prod/scripts/deploy.sh local
bash deploy/intranet-prod/scripts/migrate-and-seed.sh
bash deploy/intranet-prod/scripts/smoke.sh
```

更新到指定 commit：

```bash
bash deploy/intranet-prod/scripts/backup-db.sh
bash deploy/intranet-prod/scripts/deploy.sh <commit-sha>
bash deploy/intranet-prod/scripts/migrate-and-seed.sh
bash deploy/intranet-prod/scripts/smoke.sh
```

## 默认学生与培养方案导入

S28 生产初始化默认只执行迁移与基础字典种子，不会清空或重建业务数据。若新生产库需要导入仓库内受控的默认学生花名册和 `2024-default` 培养方案，执行：

```bash
cd /opt/super-ruc/app
bash deploy/intranet-prod/scripts/seed-default-data.sh
```

脚本会先执行数据库备份，再调用 `python -m scripts.seed_default_data`。该导入是幂等的：学生按学号 upsert，培养方案只维护 `version_label=2024-default` 的默认版本，不执行 S27 开发冷启动，也不会清空学生、账号、微信绑定或业务数据。

默认数据源通过 Compose 只读挂载到后端容器的 `/docs`：

- `docs/source/students/students.xlsx`
- `docs/source/training program/2024_information.md`

## 管理入口

- 学生数据：`用户管理 -> 学生管理` 可查询学生、查看画像，并可变更学籍状态；学生画像页可新增/删除成长事实、处理补录/纠错、导出 PDF/XLSX 快照。
- 后台账号：`用户管理 -> 批量创建账号` 可下载模板、上传预检并创建下级管理员账号；初始密码只在提交结果中展示一次。
- 培养方案：`培养方案管理` 可新增、编辑、删除方案、模块和课程；`导入导出中心` 也保留默认学生和默认培养方案导入入口。

## 备份与恢复

生成备份：

```bash
bash deploy/intranet-prod/scripts/backup-db.sh
```

恢复备份需要显式确认：

```bash
CONFIRM_RESTORE=YES bash deploy/intranet-prod/scripts/restore-db.sh /opt/super-ruc/backups/<backup>.dump
```

## 回滚

回滚到上一次部署前的 commit：

```bash
bash deploy/intranet-prod/scripts/rollback.sh
```

回滚到指定 commit：

```bash
bash deploy/intranet-prod/scripts/rollback.sh <commit-sha>
```

回滚脚本会重建服务并自动运行 smoke；数据库结构回滚不自动执行，如迁移已改动 schema，应先通过备份恢复评估。

## 日志与运维

```bash
docker compose --env-file deploy/intranet-prod/.env -f deploy/intranet-prod/docker-compose.yml ps
docker compose --env-file deploy/intranet-prod/.env -f deploy/intranet-prod/docker-compose.yml logs backend --tail 200
docker compose --env-file deploy/intranet-prod/.env -f deploy/intranet-prod/docker-compose.yml logs web --tail 100
```

## 小程序内网联调包

在本机生成指向内网 API 的微信小程序包：

```powershell
& .\deploy\intranet-prod\build-miniapp.ps1
```

脚本会设置 `VITE_MINIAPP_API_BASE_URL=http://10.10.0.13/api/v1` 并执行 `pnpm -C miniapp build:mp-weixin`。
