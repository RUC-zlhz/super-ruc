# S36 EDR Agent Production Install

- 日期：`2026-05-24`
- 状态：`[x]` 已完成
- 关联主计划条目：`S36.1, S36.2, S36.3, S36.4`
- 目标主机：`user@10.10.0.13`
- 来源文档：`D:\Documents\xwechat_files\wxid_d3gc7wjxuoja22_a84b\msg\file\2026-05\EDR安全软件安装方法及回退方案-服务器业务组(2025).docx`

## 执行范围

- 按来源文档的 Linux 服务器业务组参数安装 Titan EDR Agent。
- 不改动 `super-ruc` 应用代码、数据库数据、Docker Compose 配置或生产服务部署脚本。
- 不执行卸载、重装、清理或其他破坏性操作。

## 安装前检查

- SSH 目标：`ssh user@10.10.0.13`
- 系统：`Ubuntu 24.04.3 LTS`
- 架构：`x86_64`
- 权限：`sudo -n true` 可用
- 安装前 `/titan/agent`：不存在
- 安装前控制中心 `10.21.8.187` 端口连通性：
  - `80`、`8001`、`8002`、`6677`、`7788`、`8443` 可连
  - `443` 拒绝连接；来源文档写作 `80(443)`，实际安装使用 `8001` 下载与上报

## 执行命令

下载脚本留档：

```bash
mkdir -p /home/user/edr-install-logs
curl -fsSL 'http://10.21.8.187:8001/agent/download?k=38487b0b51848ef0dc3f163a7e20d5d1260ba4d8&group=11&protocol=0&root=true&runAccount=root&userAdd=false&app=0&container=0' \
  -o /home/user/edr-install-logs/titan_agent_install.sh
```

执行安装：

```bash
sudo bash /home/user/edr-install-logs/titan_agent_install.sh 2>&1 \
  | tee /home/user/edr-install-logs/install-20260524-215338.log
```

## 完成证据

- 安装输出包含：`Agent installation success.`
- 安装目录：`/titan/agent` 已存在
- 运行进程：`/titan/agent/titanagent -d -b /etc/titanagent`
- root crontab 已写入：
  - `/etc/titanagent/agent_update_cron.sh`
  - `/etc/titanagent/agent_update_exception_cron.sh`
  - `/etc/titanagent/agent_monitor_cron.sh`
- 安装日志：`/var/log/titanagent/install.log`
- 留档日志：`/home/user/edr-install-logs/install-20260524-215338.log`
- 控制中心上报接口返回：`{"code":{"retcode":0}}`
- 业务服务复核：
  - `super-ruc-intranet-prod-web-1`、`backend`、`db`、`redis`、`minio` 均保持 `healthy`
  - `curl http://127.0.0.1/healthz` 返回 `{"code":0,"message":"ok","data":{"status":"ok"}}`

## 回退方法

来源文档给出的 Linux agent 本机卸载命令：

```bash
sudo bash /titan/agent/install_agent.sh disclean
```

仅在 EDR 安装后确认影响业务或用户明确要求回退时执行。
