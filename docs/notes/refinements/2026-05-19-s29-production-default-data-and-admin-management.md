# S29 生产默认数据导入与管理入口补强

- 日期：`2026-05-19`
- 关联主计划：`S29.1, S29.2, S29.3, S29.4, S29.5, S29.6`
- 状态：`[x]`

## 背景

S28 按生产口径只执行 Alembic 迁移和 `scripts.seed_initial` 基础种子，不执行 S27 开发冷启动。因此新建的内网生产库中有基础角色、字典和默认 `admin`，但没有默认学生花名册与默认培养方案。

生产容器另有一个实际缺口：`scripts.seed_default_data` 依赖仓库根目录下的 `docs/source/students/students.xlsx` 与 `docs/source/training program/2024_information.md`，但 S28 后端镜像只包含 `backend/` 目录，容器内无法读取默认数据源。

## 任务清单

- [x] `S29.1` 复核生产库状态，确认 `students=0`、`curriculum_plans=0` 来自未导入默认业务数据。
- [x] `S29.2` 为内网生产 Compose 增加 `../../docs:/docs:ro` 只读挂载，使后端容器可读取受控默认数据源。
- [x] `S29.3` 新增 `deploy/intranet-prod/scripts/seed-default-data.sh`，先备份数据库，再执行 `python -m scripts.seed_default_data`，不清空业务数据。
- [x] `S29.4` 在 `10.10.0.13` 执行生产默认数据导入，导入默认学生和 `2024-default` 培养方案。
- [x] `S29.5` 补 Web 管理入口：学生画像页新增“编辑学籍信息”，用户管理页新增“新增单个账号”。
- [x] `S29.6` 重建生产 Web 容器并通过 smoke。

## 验证记录

- 本地 `docker compose --env-file deploy/intranet-prod/.env.example -f deploy/intranet-prod/docker-compose.yml config --quiet` 通过。
- 本地 `bash -n` 覆盖 `deploy/intranet-prod/scripts/*.sh` 通过。
- 本地 `pnpm -C web build` 通过。
- 服务器执行 `bash deploy/intranet-prod/scripts/seed-default-data.sh`，先生成备份 `/opt/super-ruc/backups/super-ruc-20260519-192159-d9060b4.dump`，随后输出 `students inserted=5 updated=0 skipped=0; curriculum inserted=7 updated=0 skipped=0`。
- 服务器数据复核：`students=5`、`curriculum_plans=7`、`curriculum_modules=134`、`users=1`。
- 服务器重建并启动 `web` 后，`bash deploy/intranet-prod/scripts/smoke.sh` 返回 `Smoke passed for http://127.0.0.1`；`http://10.10.0.13/healthz` 与 `http://10.10.0.13/` 均返回 `200`。

## 当前口径

- S28 仍保持生产启动最小口径：迁移 + 基础种子，不自动清空或重建业务数据。
- 如新生产库需要默认演示/验收数据，应显式运行 `seed-default-data.sh`。
- 管理员创建下级账号的入口为 `用户管理 -> 新增单个账号` 或 `用户管理 -> 批量创建账号`。
- 学生主档维护入口为 `用户管理 -> 学生管理 -> 画像 -> 编辑学籍信息`；学籍生命周期状态仍在 `用户管理 -> 学生管理 -> 学籍` 中维护。
