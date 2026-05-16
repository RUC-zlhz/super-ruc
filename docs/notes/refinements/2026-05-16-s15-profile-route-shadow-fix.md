# S15 Web 管理端学生画像路由遮蔽缺陷修复

- 日期：`2026-05-16`
- 关联主计划：`S15.1, S15.2, S15.3, S15.4`
- 当前状态：`DONE`

## 问题

- 用户反馈 `http://127.0.0.1:5174/profile/student/4` 学生画像异常。
- 浏览器控制台显示 `StudentProfile.vue` mounted 阶段的并发请求中 `/admin/profile/corrections` 返回 `422`，导致页面加载链路被打断。

## 根因

- `backend/app/profile/router.py` 中 `GET /admin/profile/{student_id}` 注册在 `GET /admin/profile/corrections` 之前。
- FastAPI 对未显式使用 path converter 的动态段会先匹配 `/corrections` 到 `{student_id}`，再由请求校验把非整数路径段判为 `422`。

## 修复

- [x] `S15.1` 复现 `profile/student/4` 页面错误，确认 `422` 来源为画像纠错列表接口。
- [x] `S15.2` 将 `/admin/profile/corrections` 与 `/admin/profile/corrections/{correction_id}/decision` 移到 `/{student_id}` 动态详情路由之前。
- [x] `S15.3` 新增 `backend/tests/test_profile_admin_route_order.py`，直接断言 `/admin/profile/corrections` 不再被学生详情路由遮蔽。
- [x] `S15.4` 完成静态校验、定向测试和本地页面/API 复核。

## 验证

- `backend` 下设置 repo-local `UV_CACHE_DIR=.uv-cache-local` 后执行：
  - `uv run --no-sync pytest tests/test_profile_admin_route_order.py -q -o cache_dir=.tmp/pytest-cache-profile-route --basetemp=.tmp/pytest-tmp-profile-route` -> `2 passed`
  - `uv run --no-sync python -m py_compile app/profile/router.py tests/test_profile_admin_route_order.py` -> 通过
  - `uv run --no-sync ruff check app/profile/router.py tests/test_profile_admin_route_order.py` -> `All checks passed`
- 本地运行服务复核：
  - 无 token 请求 `http://127.0.0.1:5174/api/v1/admin/profile/corrections?student_id=4&status=PENDING&page=1&size=1` 返回 `401 缺少 Authorization Bearer token`，不再返回 `422`。
  - 刷新 `http://127.0.0.1:5174/profile/student/4` 后，页面可渲染学生 `2024201517 / 李明蔚` 的学籍信息、成长事实和待审核区域。

