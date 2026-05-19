# S27 开发阶段冷启动脚本

- 日期：`2026-05-18`
- 状态：`[x]`
- 关联主计划：`S27`

## 背景

当前处于开发演示阶段，学生主档不需要依赖数据库中的历史持久化状态。每次本地启动可从 `docs/source/students/students.xlsx` 冷启动学生信息，并创建默认管理员 `admin / admin123`。

正式设计仍保留数据库持久化学生、账号、绑定与业务记录的要求；本细化只约束开发脚本行为，不替代生产部署设计。

## 实施范围

- [x] 新增开发库 schema 重置脚本 `backend/scripts/dev/reset_dev_database.py`。
- [x] 新增一键启动脚本 `scripts/dev/start-dev.ps1`。
- [x] 启动脚本设置 repo-local `UV_CACHE_DIR=.uv-cache-local` 并验证可写。
- [x] 启动脚本执行 Docker 基础设施、Alembic 迁移、基础种子和默认学生/培养方案导入。
- [x] 每次重跑通过重建 schema 清除旧学生数据、微信 `openid/unionid` 与 `student_id` 绑定关系。
- [x] 完成脚本语法与最小冷启动验证。

## 使用口径

```powershell
.\scripts\dev\start-dev.ps1
```

常用参数：

- `-SkipDocker`：跳过 Docker 基础设施启动。
- `-SkipDependencySync`：跳过 `uv sync --extra dev`。
- `-NoLaunch`：只完成数据库冷启动，不启动后端和 Web 开发服务器。

## 设计边界

- 该脚本拒绝在 `APP_ENV=prod` 下执行数据库重置。
- 该脚本是开发便利入口；正式环境仍必须通过数据库持久化保存学生主档、微信绑定与业务数据。

## 验证记录

- PowerShell 解析校验：`scripts/dev/start-dev.ps1` 通过。
- Python 静态校验：`uv run --no-sync python -m py_compile scripts\dev\reset_dev_database.py` 通过。
- 冷启动验证：执行 `.\scripts\dev\start-dev.ps1 -NoLaunch -SkipDependencySync` 通过，完成 Docker 基础设施启动、schema 重置、Alembic `0017` 迁移、基础 seed、默认学生与培养方案导入。
- 重跑验证：执行 `.\scripts\dev\start-dev.ps1 -NoLaunch -SkipDependencySync -SkipDocker` 通过，默认学生导入结果仍为 `students inserted=5`，默认培养方案导入结果为 `curriculum inserted=7`。
- 数据复核：重跑后查询结果为 `students=5`、`users=1`、`bound_users=0`、`openid_users=0`、`admin=admin`、`must_change=True`，确认旧学号与微信绑定不残留。
