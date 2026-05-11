# 2026-05-11 教师管理端默认管理员与初始密码提醒

- 关联主计划条目：`S11.7`
- 状态：`[x]` 已完成
- 背景：临时部署与初始化流程需要一个可预测的教师管理端初始管理员账号，且该账号使用默认密码登录后必须提示尽快改密，避免默认凭据长期留存。

## 范围

- 后端种子新增默认教师管理端账号：`work_no=admin`、初始密码 `admin123`、角色 `SUPER_ADMIN`。
- 种子脚本保持幂等：只在账号不存在或已有账号没有密码时写入初始密码；后续人工改密不被重复 seed 覆盖。
- 登录响应与 `/auth/me` 返回 `must_change_password`，当 `admin` 账号密码仍匹配 `admin123` 时为 `true`。
- 新增 `/auth/change-password`，校验原密码后写入新密码，并禁止继续使用当前密码或 `admin/admin123` 初始密码。
- Web 教师管理端登录后识别 `must_change_password` 并弹窗提醒；个人信息页提供真实改密弹窗，改密成功后同步刷新用户信息。

## 执行拆分

- [x] `S11.7.1` 新增默认管理员种子并纳入 `seed_initial` 顺序。
- [x] `S11.7.2` 扩展认证响应，返回 `must_change_password`。
- [x] `S11.7.3` 新增当前用户改密 API 与审计记录。
- [x] `S11.7.4` Web 登录后提醒初始密码，个人信息页接入改密弹窗。
- [x] `S11.7.5` 补充认证集成测试用例与可运行验证记录。

## 验证结果

- `uv run --extra dev ruff check app/auth scripts/seed tests/integration/test_auth_flow.py` 通过。
- `uv run --extra dev python -m py_compile app/auth/bootstrap.py app/auth/schemas.py app/auth/service.py app/auth/router.py scripts/seed/admin_user.py scripts/seed/__init__.py tests/integration/test_auth_flow.py` 通过。
- `.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p web\tsconfig.json` 通过。
- `pnpm -C web build` 通过。
- `uv run --extra dev pytest tests/integration/test_auth_flow.py -q` 未进入断言；本机 `localhost:54322/sip_db_test` 拒绝连接，且 Docker Desktop daemon 未运行，无法在当前会话拉起 compose 数据库。

## 结论

本轮已完成默认管理员、登录提醒和改密闭环。剩余风险仅在本机会话数据库不可用导致认证集成测试未实跑；测试用例已补齐，待 `54322` 测试数据库或 Docker daemon 可用后可直接复跑。
