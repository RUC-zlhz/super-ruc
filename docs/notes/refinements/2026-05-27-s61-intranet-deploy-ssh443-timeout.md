# S61 生产部署 GitHub SSH 443 与超时治理

- 状态：`[x]` 已完成
- 日期：`2026-05-27`
- 目标：修复生产 self-hosted runner 在 GitHub SSH 连接超时或抖动时长时间卡住/单次失败的问题，确保后续 `main` push 部署能更稳定拉取 GitHub。

## 问题

- `S60` 生产代码部署完成后，追加的文档-only 提交触发第二次自动部署。
- 第二次部署卡在生产机 `git ls-remote origin`，进程树显示 `deploy-from-github.sh -> git ls-remote -> ssh git@github.com`。
- 生产机到 `github.com:22` 超时；同一 deploy key 访问 `ssh://git@ssh.github.com:443/RUC-zlhz/super-ruc.git` 可正常返回 HEAD。
- 后续复测发现 `ssh.github.com:443` 也存在间歇性单次超时，因此 deploy 脚本需要对远端 Git 操作做重试。

## 修复内容

- `.github/workflows/intranet-prod-deploy.yml` 的 `DEPLOY_GIT_REMOTE` 改为 `ssh://git@ssh.github.com:443/RUC-zlhz/super-ruc.git`。
- `deploy/intranet-prod/scripts/common.sh` 的 `GIT_SSH_COMMAND` 增加 `BatchMode=yes`、`ConnectTimeout=10`、`ServerAliveInterval=5`、`ServerAliveCountMax=1`。
- `deploy/intranet-prod/scripts/deploy-from-github.sh` 对 `git ls-remote` 和 `git fetch` 增加重试封装，默认最多 6 次；workflow 生产环境显式配置为最多 8 次、间隔 8 秒。

## 验证

- 生产机手动验证 SSH 443 remote：`git ls-remote --exit-code ssh://git@ssh.github.com:443/RUC-zlhz/super-ruc.git HEAD` 成功返回 `496f6fb`。
- 推送后需确认生产 `.deploy/current_commit` 到最新提交，runner job completed，backend/web/db/redis/minio 保持 healthy。
