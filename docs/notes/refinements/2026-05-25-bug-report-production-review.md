# S40 bug-report 生产事实审查

- 状态：`[x]` 已完成
- 主计划引用：`docs/notes/current-implementation-plan.md`
- 输入材料：`bug-report.md`
- 审查日期：`2026-05-25`

## 生产基线

- 生产主机：`user@10.10.0.13`
- 应用目录：`/opt/super-ruc/app`
- 实际提交：`a558c61ea2493368c03a1fb871b82998ffde1fec`
- 服务状态：`PostgreSQL / Redis / MinIO / backend / web` 均为 healthy。
- 运行验证：`bash deploy/intranet-prod/scripts/smoke.sh` 通过，`http://127.0.0.1/healthz` 返回 `{"status":"ok"}`。
- 运行配置：`APP_ENV=prod`、`APP_DEBUG=False`、`WECHAT_MOCK_ENABLED=False`、`WECHAT_GUEST_LOGIN_ENABLED=False`、`AI_QA_ENABLED=False`。

## 审查结论

| 编号 | 结论 | 依据 | 后续建议 |
| --- | --- | --- | --- |
| Bug #1 | 否定为生产 bug | 生产环境密钥已配置，Mock 与 AI QA 均关闭，backend 已启动并 healthy；该校验是上线防护。 | 保留现状。 |
| Bug #2 | 否定为应用 bug | 数据库是核心依赖，当前 DB healthy；配置错误或 DB 不可用时 fail fast 属于部署前置条件，不应降级为可用服务。 | 后续可增强运维提示，但不是当前故障。 |
| Bug #3 | 确认为可修复风险 | `openMiniappPage()` 对非 tabBar 页直接 `uni.navigateTo`，`workflow/index.vue` 的详情与理论自测入口无节流。 | 增加统一跳转锁或同页去重。 |
| Bug #4 | 否定为当前死循环 bug | `/login` 与 `/error/403` 均为 public；`fetchMe()` 失败后 `logout()` 清空 token，守卫只重定向一次。 | 无需作为缺陷处理。 |
| Bug #5 | 确认为可修复风险 | 附件与成绩单上传入口均先 `await file.read()` 形成 bytes，再检查 `UPLOAD_MAX_SIZE_MB=30`。 | 在 router 层按流式读取或 Content-Length 前置限制。 |
| Bug #6 | 否定为生产 bug | 生产 `WECHAT_MOCK_ENABLED=False`；开发 Mock 是受控本地能力。 | 防止开发环境暴露公网即可。 |
| Bug #7 | 确认为潜在逻辑缺陷 | `compute_academic_gap()` 将一条已修课程展开到所有等价目标，多个白名单模块可重复消耗同一学分。生产当前 active 等价规则为 `0`，未触发。 | 增加等价学分一次性消耗模型和回归测试。 |
| Bug #8 | 待业务确认 | 当前排序明确为风险等级优先、再按缺口降序；报告提出的是业务偏好变化，不是代码错误。 | 若确认按缺口优先，新增排序参数或调整默认口径。 |
| Bug #9 | 否定为当前导入崩溃 | `_parse_courses("") -> None` 后续会作为无白名单模块处理，不会直接遍历 `None` 崩溃。 | 可将语义文档化，不必优先修。 |
| Bug #10 | 确认为兼容性缺口 | `_parse_date()` 仅支持 `YYYY-MM-DD`，生产容器验证 ISO 时区日期返回 `None`。 | 支持 ISO 日期时间和斜杠日期。 |
| Bug #11 | 确认为潜在一致性缺陷 | 列表入口过滤 `deleted_at is null`，但 `compute_academic_gap(student_id)` 自身未过滤软删除，详情接口可传任意 ID。生产当前 deleted 学生为 `0`，未触发。 | 在详情计算入口过滤软删除。 |
| Bug #12 | 否定为角色包含 bug | `_approver_has_role()` 使用集合交集，不是字符串包含；生产 active request types 均配置审批角色。 | 保留现状。 |
| Bug #13 | 确认为兼容性缺口 | `_parse_date("2024/01/01") -> None`。 | 与 Bug #10 合并修复。 |
| Bug #14 | 当前实现未复现报告描述 | 无白名单模块使用 `flexible_credit_balance` 递减，不会把同一余额同时分配给两个无白名单模块；但白名单/等价路径仍有 Bug #7 的重复消耗风险。 | 归入 Bug #7 的学分消耗模型统一修。 |
| Bug #15 | 证据不足 | 当前报告指向 `exchange/service.py`，但荣誉记录排序与展示主要在 `honor` 模块；生产当前荣誉记录为 `0`。 | 需要具体导入样例再定性。 |
| Bug #16 | 确认为参数校验缺口 | `admin_academic_gap_list` 的 `page/page_size` 没有 FastAPI `Query(ge/le)` 约束，service 仅对 page 做 `max(page - 1, 0)`。 | 补 `Query(default=1, ge=1)` 与 `page_size` 上限。 |
| Bug #17 | 低风险可加固 | `_safe_filename()` 只替换路径分隔符并截断；MinIO object key 缓解路径遍历，但特殊字符仍不干净。 | 使用统一文件名清洗 helper。 |
| Bug #18 | 否定为当前数据 bug | 生产 `curriculum_module_types` 只有 `ELECTIVE,GENERAL,PRACTICE,REQUIRED`，均在映射内。 | 自定义模块类型出现前不处理。 |

## 优先级建议

- P1：Bug #5、Bug #7、Bug #10/#13、Bug #16。
- P2：Bug #3、Bug #11、Bug #17。
- 待业务确认：Bug #8。
- 待样例确认：Bug #15。

## 验证命令

- `ssh user@10.10.0.13 "cd /opt/super-ruc/app; git rev-parse HEAD; docker compose -f deploy/intranet-prod/docker-compose.yml ps"`
- `ssh user@10.10.0.13 "cd /opt/super-ruc/app; bash deploy/intranet-prod/scripts/smoke.sh; curl -fsS http://127.0.0.1/healthz"`
- `docker compose -f deploy/intranet-prod/docker-compose.yml exec -T backend python - <<'PY' ...`
- `docker compose -f deploy/intranet-prod/docker-compose.yml exec -T db psql -U sip_app -d sip_db -At`
