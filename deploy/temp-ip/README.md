# 临时 IP 直连部署

本目录用于 `123.57.54.195` 迁移前的临时联调部署：

- 数据库：PostgreSQL 15（通用 PostgreSQL 兼容口径，用于临时验证）
- 缓存：Redis 7
- 对象存储：MinIO
- 后端：FastAPI，容器内监听 `8080`
- Web 管理端：Nginx 监听 `80`，并反代 `/api/v1/` 到后端

正式密钥不落仓库。服务器侧需在部署目录创建 `.env`，至少包含：

```env
POSTGRES_DB=sip_db
POSTGRES_USER=sip_app
POSTGRES_PASSWORD=...
REDIS_PASSWORD=...
MINIO_ROOT_USER=sip_minio
MINIO_ROOT_PASSWORD=...
JWT_SECRET_KEY=...
FIELD_ENCRYPTION_KEY=...
WECHAT_APPID=...
WECHAT_SECRET=...
WECHAT_MOCK_ENABLED=false
```

`WECHAT_MOCK_ENABLED=true` 只允许本地或临时 mock smoke 使用。接入真实微信小程序时必须配置
`WECHAT_SECRET` 并关闭 mock；否则 `wx.login()` 返回的 code 不会按微信官方 `code2Session`
流程换取 OpenID。

临时验收地址：

- Web 管理端：`http://123.57.54.195/`
- 后端健康检查：`http://123.57.54.195/healthz`
- API 基址：`http://123.57.54.195/api/v1`

微信小程序临时 IP 出包需显式注入 API 基址：

```powershell
& .\deploy\temp-ip\build-miniapp.ps1
```

该脚本会设置 `VITE_MINIAPP_API_BASE_URL=http://123.57.54.195/api/v1` 后执行
`pnpm -C miniapp build:mp-weixin`，并校验生成的
`miniapp/dist/build/mp-weixin/utils/request.js` 已包含临时 API 基址。
