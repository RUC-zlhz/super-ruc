# 第 14 组 Web 互测执行结果

- 测试方：第 12 组
- 被测方：第 14 组
- 测试日期：`2026-05-28`
- 测试入口：`http://10.10.0.14/`
- 依据资料：`tmp/docs/group14/platform-documents/group14-extra.md`
- 测试方式：低风险接口级烟测 + 前端分包接口核对 + 权限/导出/异常参数深测；未执行批量导入、删除、撤销等高影响写操作

## 资料与环境

| 项目 | 结果 | 证据 |
| --- | --- | --- |
| 首页访问 | 通过，`GET /` 返回 `200` | `tmp/docs/group14/web-test-results/smoke-results.json` |
| 健康检查 | 通过，`GET /api/health` 返回 `student-services-backend`、`status=ok` | 命令输出与 `docs/testing/group14-web-test-summary.md` |
| 前端资源 | 已下载 Vite 分包并提取接口 | `tmp/docs/group14/web14/` |
| 账号资料 | 五类 `demo.* / demo1234` 账号均可登录 | `tmp/docs/group14/web-test-results/smoke-results.json` |

## 登录测试

| 角色 | 账号 | 结果 |
| --- | --- | --- |
| 管理员 | `demo.admin` | 通过，返回角色 `admin` |
| 教师 | `demo.teacher` | 通过，返回角色 `teacher` |
| 学生 | `demo.student` | 通过，返回角色 `student` |
| 班团骨干 | `demo.secretary` | 通过，返回角色 `league_secretary` |
| 领导 | `demo.leader` | 通过，返回角色 `leader` |
| 错误密码 | `demo.student / wrong-password` | 通过，返回 `401 Invalid credentials` |
| 未登录访问 `/api/auth/me` | 无 token | 通过，返回 `401 Unauthorized` |

## 学生端烟测

| 接口 | 结果 |
| --- | --- |
| `GET /api/students/me` | 通过，返回学生 `李明`、学号 `20230001` 等信息 |
| `GET /api/students/me/profile` | 通过，返回公开画像数据 |
| `GET /api/students/me/profile-requests` | 通过，返回列表 |
| `GET /api/processes/my` | 通过，返回党团流程信息 |
| `GET /api/notices/my` | 通过，返回通知列表 |
| `GET /api/policies` | 通过，返回政策列表 |
| `GET /api/policies/ask?q=奖学金` | 通过，返回奖助学金相关回答与来源 |
| `GET /api/approvals` | 通过，返回审批列表 |

## 管理端烟测

| 接口 | 管理员 | 教师 | 结论 |
| --- | --- | --- | --- |
| `GET /api/students` | `200` | `200` | 学生台账可查询 |
| `GET /api/students/profile-requests` | `200` | `200` | 画像申请列表可查询 |
| `GET /api/policies?includeInactive=true` | `200` | `200` | 政策列表可查询 |
| `GET /api/notices/published?limit=8` | `200` | `200` | 通知发布列表可查询 |
| `GET /api/certificates/templates` | `200` | `200` | 证明模板可查询 |
| `GET /api/certificates` | `200` | `200` | 证明记录可查询 |
| `GET /api/league-branches` | `200` | `200` | 班团组织可查询 |
| `GET /api/business-templates?includeDisabled=true` | `200` | `200` | 业务模板可查询 |
| `GET /api/logs?page=1&pageSize=10` | `400` | `400` | 发现 `BUG-G14-002` |
| `GET /api/logs/export` | `400` | `400` | 发现 `BUG-G14-002` |

## 权限边界

| 场景 | 结果 |
| --- | --- |
| 学生访问 `/api/students` | 通过，返回 `403` |
| 学生访问 `/api/logs` | 通过，返回 `403` |
| 学生访问 `/api/notices/published?limit=8` | 通过，返回 `403` |
| 学生访问 `/api/certificates/templates` | 通过，返回 `403` |
| 领导访问 `/api/students` | 通过，返回 `403` |
| 班团骨干访问 `/api/students` | 通过，返回 `403` |
| 班团骨干访问 `/api/league-branches` | 通过，返回本人负责组织列表 |

## 后续深测结果

| 场景 | 结果 | 结论 |
| --- | --- | --- |
| 学生访问 `/api/students/export` | 返回 `403` | 通过，学生不能导出全量学生台账 |
| 学生访问 `/api/approvals/export` | 返回 `200`，CSV 仅包含本人 `李明 / 20230001` 的审批 | 暂不作为 bug，属于本人审批导出 |
| 学生访问他人证明 `/api/certificates/student/{otherId}` | 返回 `403` | 通过，未发现他人证明泄露 |
| 领导访问 `/api/policies?includeInactive=true` | 返回 `200`，包含 2 条 `INACTIVE` 已停用政策 | 发现 `BUG-G14-004` 候选/建议提交 |
| 领导访问 `/api/policies/export` | 返回 `200`，下载政策台账 Excel，含已停用政策和摘要 | 发现 `BUG-G14-004` 候选/建议提交 |
| 政策检索 `/api/policies?keyword=%00` | 学生、管理员、领导均返回 `500` | 发现 `BUG-G14-003`，建议提交 |
| 政策检索异常后再查正常关键词 | 返回 `200` | 服务可恢复，但异常输入仍稳定触发 500 |

## 发现问题

| 编号 | 类型 | 问题 | 状态 |
| --- | --- | --- | --- |
| `BUG-G14-001` | 崩溃类 bug 候选 | PDF 声称可用微信开发者工具打开小程序，但平台与补充 Markdown 均未提供小程序源码包 | 候选，若要测“小程序端”建议提交 |
| `BUG-G14-002` | Logic bug | 管理员和教师访问操作日志列表、筛选、导出接口均返回 `400`，操作日志功能不可用 | 建议提交 |
| `BUG-G14-003` | 崩溃类 bug | 政策检索接口遇到 `%00` 空字符查询参数返回 `500 Internal Server Error` | 建议提交 |
| `BUG-G14-004` | Logic bug | 领导账号可直接导出管理端政策台账，并通过 `includeInactive=true` 查看已停用政策 | 建议提交；若对方声明领导有该权限则降级为候选 |

## 证据文件

- 总体烟测：`tmp/docs/group14/web-test-results/smoke-results.json`
- 权限矩阵：`tmp/docs/group14/web-test-results/permission-matrix.json`
- 操作日志 bug 复现：`tmp/docs/group14/web-test-results/logs-bug-repro.json`
- 后续权限与导出深测：`tmp/docs/group14/web-test-results/followup-permission-export-results.json`
- 政策异常参数深测：`tmp/docs/group14/web-test-results/followup-boundary-fuzz-results.json`
- 政策 `%00` 最小复现：`tmp/docs/group14/web-test-results/policy-null-keyword-bug-repro.json`
- 领导账号政策台账导出：`tmp/docs/group14/web-test-results/followup-leader-api_policies_export.xlsx`
- 前端分包：`tmp/docs/group14/web14/`
- Bug 草稿：`docs/testing/group14-bug-report-drafts.md`

## 后续建议

1. 优先提交 `BUG-G14-003` 和 `BUG-G14-002`，二者证据充分且稳定复现。
2. 可提交 `BUG-G14-004` 作为权限边界问题；若第 14 组后续说明领导具备政策台账权限，再降级处理。
3. 若互评平台允许提交文档/运行资料类问题，可提交 `BUG-G14-001`；若第 14 组确认 Web 项目为唯一交付，则将其作为文档不一致问题而非小程序运行问题。
4. 若继续深测，可在页面侧补截图后测试通知、政策、画像、证明、审批中的跨角色闭环，但写操作会在对方测试环境留下数据。
