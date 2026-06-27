# S28 模块 5/6/7 本地联调验收记录

- 日期：`2026-05-21`
- 状态：`[!]` 模块 5 与模块 7 本地接口级验收通过；模块 6 审批状态闭环通过，但电子证明 PDF 预览受本机 `weasyprint + GTK` 运行时缺失阻塞；PostgreSQL 集成测试受 Docker 镜像缺失阻塞。
- 关联主计划：`S28`

## 自动化回归执行

- [!] 已尝试运行模块 5/6/7 相关 pytest 集成测试：`test_notice_flow.py`、`test_request_flow.py`、`test_s12_gap_closure.py` 指定用例、`test_report_contract_flow.py` 指定用例。
- [!] pytest 未进入业务断言阶段，阻塞原因是 `tests/conftest.py` 默认连接 `postgresql+asyncpg://sip_user:sip_pass_dev@localhost:54322/sip_db_test`，当前 `54322` 无 Postgres 服务；Docker 本地无 `postgres:15-alpine`、`redis:7-alpine`、`minio/minio` 镜像，完整 Docker 栈仍受 Docker Hub 网络/代理阻塞。

## 本地接口级验收

- [x] 本地服务状态：后端 `http://127.0.0.1:18080/healthz` 返回 `code=0`，教师 Web `http://127.0.0.1:4173` 返回 `200`。
- [x] 模块 5：创建 `LOCAL_ACCEPTANCE` 通知、发布并站内投递；最新通知 `id=3`，批次 `COMPLETED`，目标 `2`，成功 `2`，学生 `2024201534` 收件箱可读取且已读状态可回写。
- [x] 模块 6：学生 `2024201534` 创建并提交请假申请与在读证明申请；本地辅导员 `local_counselor / counselor123` 可在教师端工作台看到、认领并审批；申请 `id=2` 与 `id=3` 均已 `APPROVED`，学生端 `/requests/my` 可看到状态回流。
- [!] 模块 6 电子证明 PDF：在读证明申请 `id=3` 已审批通过，但 `GET /workflow/proof-preview/3` 返回 `50003`，错误为 `PDF 生成依赖未就绪（weasyprint + GTK 运行时）`；该项需要人工安装 GTK/WeasyPrint 运行时后复测。
- [x] 模块 7：已给学生 `2024201534` 绑定现有 `2024 / 计算机科学与技术` 培养方案；成绩单 PDF 上传返回待人工复核记录，提交复核后写入 `student_course_records=1`；学业缺口接口显示 `total_credits_required=155.0`、`total_credits_earned=1.0`、推荐课程数 `30`、预警/数据提示数 `5`。
- [x] 教师端代理复核：通过 `http://127.0.0.1:4173/api/v1/admin/requests` 可读到本地后端申请总数 `3`。

## 本地测试数据变更

- [x] 已备份本地 SQLite：`backend/tmp/local-miniapp-before-module567-20260521-114439.db`。
- [x] 新增/更新本地辅导员账号：`local_counselor / counselor123`，角色 `COUNSELOR`。
- [x] 更新测试学生 `2024201534 / 胡晓锋` 的 `grade_code=2024`、`major_code=计算机科学与技术`，用于模块 7 培养方案比对。
- [x] 新增本地验收通知、申请、成绩单复核与正式成绩记录；当前本地计数为 `notices=5`、`notice_deliveries=8`、`requests=3`、`request_approval_records=7`、`import_batches=1`、`student_course_records=1`。

## 剩余人工项

- [!] 若要完成模块 6 电子证明 PDF 的本机验收，需要安装 WeasyPrint 所需 GTK 运行时，然后复测 `GET /api/v1/workflow/proof-preview/3`。
- [!] 若要完成 pytest 集成回归，需要先恢复 Docker Hub 镜像拉取或手工导入 Postgres/Redis/MinIO 镜像，并启动 `localhost:54322` 测试库。