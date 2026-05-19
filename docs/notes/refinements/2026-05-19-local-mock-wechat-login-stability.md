# 2026-05-19 本地 Mock 微信登录稳定性修复

- 状态：`[x] 已完成`
- 关联主计划：`S11.6` 微信小程序登录鉴权与未登录请求治理
- 适用范围：`backend` 本地开发 / 微信开发者工具联调 / `WECHAT_MOCK_ENABLED=true`

## 背景

用户在本地微信开发者工具中，第一次使用学生主档 `2024202721 / 曾翎一` 登录成功；但关闭开发者工具、重新导入项目后再次登录，会收到“该学生已绑定其他微信账号”错误。

排查确认根因不是学生数据异常，而是本地 mock 微信登录策略本身不稳定：

1. 小程序每次重新打开后，`wx.login()` 返回的 `code` 都会变化。
2. 旧 mock 逻辑直接把 `code` 映射成 `mock_{code}` 作为 `openid`。
3. 同一个学生第二次登录时，会被系统视为“一个新的微信账号”，从而与第一次登录时绑定的旧 mock `openid` 冲突。

## 修复目标

1. 让同一个学生在本地 mock 模式下重复登录时，得到稳定且可复用的 mock `openid`。
2. 兼容此前已经写入数据库的历史 `mock_{code}` 绑定，避免要求手工删库或解绑。
3. 不影响真实微信 `code2Session` 流程，也不改变无学号访客态登录边界。

## 实现说明

### 1. 稳定 mock `openid`

- 当本地 mock 登录携带 `student_no` 时，不再使用一次性的 `code` 作为身份主键。
- 新规则改为生成稳定标识：`mock_student_{student_no}`。
- 这样同一个学生在重新导入小程序、重启开发者工具、重新执行 `wx.login()` 后，仍会命中同一个本地 mock 身份。

### 2. 历史 mock 绑定自动迁移

- 若数据库中该学生已经绑定了旧格式 `mock_{code}` 的账号，且当前环境仍为 mock 模式，则本次登录不再直接报冲突。
- 系统会把旧 mock 绑定自动迁移到新的稳定 `mock_student_{student_no}`。
- 这样历史本地测试数据可以无缝延续，不需要手工清库。

### 3. 真实微信与访客态边界保持不变

- `WECHAT_MOCK_ENABLED=false` 时，仍然走真实微信 `code2Session`，本次修复不改变生产/远端鉴权逻辑。
- 未提供 `student_no` 的访客态 mock 登录，仍继续使用基于 `code` 的一次性 mock 身份，不扩大访客权限。

## 代码落点

- `backend/app/auth/service.py`
  - mock `openid` 生成逻辑改为按 `student_no` 稳定化。
  - 本地 mock 登录时，历史 `mock_{code}` 绑定会自动迁移到新稳定 `openid`。
- `backend/tests/integration/test_auth_flow.py`
  - 更新 mock 登录相关回归用例。
  - 补充“同一学生重复登录成功”和“旧 mock 绑定自动迁移成功”断言。

## 验证记录

- 静态校验：
  - `py -m uv run python -m py_compile app/auth/service.py tests/integration/test_auth_flow.py`
- 定向集成测试：
  - `py -m uv run pytest tests/integration/test_auth_flow.py -q -o cache_dir=.tmp/pytest-cache-auth-mock-rebind --basetemp=.tmp/pytest-tmp-auth-mock-rebind`
  - 结果：`17 passed`
- 本地服务复核：
  - 重启 `uvicorn` 后，`http://127.0.0.1:8080/healthz` 返回 `ok`
  - 对本地接口 `POST /api/v1/auth/wx-login` 使用学生 `2024202721 / 曾翎一` 复测，返回 `200`

## 结果

本地微信开发者工具重新导入项目后，同一名学生可以继续使用原学号和姓名完成 mock 登录，不再因为 `wx.login()` 新 `code` 被误判为“已绑定其他微信”。
