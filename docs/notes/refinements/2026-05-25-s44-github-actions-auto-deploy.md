# S44 GitHub Actions 自动部署底座

- 状态：`[!]` 外部 GitHub 登记待完成
- 主计划引用：`docs/notes/current-implementation-plan.md`
- 触发问题：用户希望本地、GitHub、服务器三端同步，并实现提交到 GitHub 后自动部署，避免反复手动部署。
- 日期：`2026-05-25`

## 方案结论

- `10.10.0.13` 是内网地址，GitHub-hosted runner 通常无法直接访问，因此自动部署采用 GitHub self-hosted runner。
- runner 安装在 `10.10.0.13`，workflow 在服务器本机执行部署脚本。
- 服务器从 GitHub 拉取私有仓库使用 read-only deploy key，不使用长期 PAT，不给写权限。
- 网络防回退通过部署前后 `preflight-network.sh` 固化：禁止常驻 `18080 / 18081` 构建代理、检查 Docker daemon 无有效代理、检查微信与 TUNA 源出口。

## 范围

- [x] `S44.1` 选择 self-hosted runner + read-only deploy key 方案。
- [x] `S44.2` 在服务器生成 deploy key：`/opt/super-ruc/.ssh/super-ruc-prod-deploy-ed25519`。
- [x] `S44.3` 新增 `deploy/intranet-prod/scripts/preflight-network.sh`。
- [x] `S44.4` 新增 `deploy/intranet-prod/scripts/deploy-from-github.sh`。
- [x] `S44.5` 新增 `deploy/intranet-prod/scripts/install-github-runner.sh`。
- [x] `S44.6` 新增 `.github/workflows/intranet-prod-deploy.yml`。
- [x] `S44.7` 更新 `deploy/intranet-prod/README.md` 的 deploy key、runner 和自动部署说明。
- [!] `S44.8` 将 deploy key 公钥登记到 GitHub 仓库 Deploy keys。
- [!] `S44.9` 使用 GitHub 一次性 runner token 注册 self-hosted runner 并实跑首轮 workflow。

## 当前服务器 Deploy Key 公钥

> 私钥只保存在服务器，不写入仓库。

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHdYy2do7Y6WGPUJVNI2zcGEJ8hoTlCjHeZOpx3Id3D9 super-ruc-prod-10.10.0.13-20260525
```

GitHub 登记要求：

- Repository -> Settings -> Deploy keys -> Add deploy key
- Title：`super-ruc-prod-10.10.0.13`
- 不勾选 `Allow write access`

## 新增文件

- `.github/workflows/intranet-prod-deploy.yml`
- `deploy/intranet-prod/scripts/preflight-network.sh`
- `deploy/intranet-prod/scripts/deploy-from-github.sh`
- `deploy/intranet-prod/scripts/install-github-runner.sh`

## 验收口径

- GitHub Deploy Key 登记后，服务器执行 `git ls-remote --exit-code origin` 成功。
- GitHub self-hosted runner 页面显示 `super-ruc-prod-*` 在线，且带 `super-ruc-prod` 标签。
- push 到 `main` 后，workflow 在 self-hosted runner 上运行。
- workflow 完成数据库备份、构建、迁移、种子、服务启动、smoke 和网络复检。
- 部署后 `10.10.0.13` 五服务 healthy，`18080 / 18081` 无监听，`wx-login` 无效 code 继续返回微信凭证错误 `401` 而非 `50201`。
