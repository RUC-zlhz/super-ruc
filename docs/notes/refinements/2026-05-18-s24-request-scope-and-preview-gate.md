# 拉取后请求权限范围与公开预览门禁收口

- 创建日期：`2026-05-18`
- 状态：`[x]`
- 关联主计划：`S24.1, S24.2`
- 关联审计：`git pull` 后审查发现的权限与发布门禁缺陷

## 目标

对刚从上游拉取进来的两处真实问题做收口：

- 班团骨干等协同角色进入 `/api/v1/admin/requests` 时，必须按其 `scope_code` 限定到班级 / 专业 / 年级范围，不能看到全量申请。
- 公开的 `/preview/requirements` 仅保留在开发或显式开关环境中，生产包默认不注册该路由。

## 实施清单

- [x] `S24.1` 管理端申请列表与详情按 scope 收口
  - 后端按用户角色与 `UserRole.scope_code` 推导可见范围。
  - 申请列表只返回同班级 / 同专业 / 同年级范围内的记录。
  - 申请详情、认领、审批、转线下与重开动作在执行前补可见性校验。
  - 回归测试覆盖有 scope、无 scope、跨范围不可见，以及本人申请不能绕过协同 scope 执行管理动作。
- [x] `S24.2` 公开前端预览路由门禁
  - Web 仅在 `import.meta.env.DEV` 或显式开启 `VITE_ENABLE_REQUIREMENT_PREVIEW=true` 时注册 `/preview/requirements`。
  - 修正预览页标题为正常中文。

## 验证

- [x] `ruff check` 通过
- [x] `python -m py_compile` 通过
- [x] `pytest tests/integration/test_request_flow.py -q` 通过，结果 `14 passed`
- [x] `pnpm -C web build` 通过

## 结果

- 班团骨干协同入口不再越权读取全量申请，公开预览页也不再随生产包默认暴露。
