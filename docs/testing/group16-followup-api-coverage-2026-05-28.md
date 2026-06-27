# 第 16 组后续接口级覆盖记录（2026-05-28）

- 测试方：`第12组`
- 被测方：`第16组`
- 范围：按后续测试计划执行可自动化的只读/低风险接口覆盖
- 原则：不做高频压测；不对 Web 后台执行新增、删除、审批等写入操作

## 覆盖结果

| 模块 | 检查项 | 结果 | 备注 |
| --- | --- | --- | --- |
| 服务健康 | `GET /api/health` | 通过 | 返回 `code=200`、`系统运行正常` |
| 数据库 | `GET /api/test/db` | 通过 | 返回 `Kingbase connected successfully` |
| 学生登录 | `POST /api/auth/login` | 通过 | `20240001 / 123456 / student` 返回 token |
| 管理员登录 | `POST /api/auth/login` | 通过 | `admin / 123456 / admin` 返回 token |
| 个人中心 | `GET /api/student/info?account=20240001` | 通过 | 返回 `张三`、`计算机科学与技术`、`totalCredits=0.0` |
| 党团流程 | `GET /api/student/party/progress?studentNo=20240001` | 可疑 | 返回 7 条阶段，其中 `未申请` 重复出现 2 次 |
| 通知列表 | `GET /api/student/notice/list?studentNo=20240001` | 通过 | 返回通知列表 |
| 通知附件 | `GET /api/file/download/1779800568686` | 通过 | 附件下载返回 `200`，文件大小约 `17927` 字节 |
| 证明历史 | `GET /api/student/certificate/history?studentNo=20240001` | 通过 | 可返回历史记录；此前已提交日期校验 Logic bug |
| 模板文件 | `GET /api/file/list?businessType=template` | 通过 | 返回空列表，不直接判定为 bug |
| 智能问答 | `POST /api/student/ai/ask` 普通问题 | 通过 | 接口返回 `200`；页面级异常另见 `BUG-G16-003` |
| Web 后台 | 管理员登录 | 通过 | 后台首页和登录接口可用 |

## 新增候选问题

- `BUG-G16-004`：党团流程时间线返回重复“未申请”阶段；建议在微信开发者工具页面补截图后按 Logic bug 提交。

## 不作为 Bug 的项

- Web 后台只读路径不能通过猜测 API 端点判定；未从页面真实操作取得的 `No static resource` 类响应不作为有效 bug。
- 普通智能问答接口本轮可返回 `200`；是否提交 `BUG-G16-003` 仍以微信开发者工具页面级 Network 与恢复性证据为准。
- `file/list?businessType=template` 返回空列表暂不提交，除非页面明确说明应有模板且页面出现功能不可用。

## 下一步人工页面复核

1. 在小程序打开“党团事务流程追踪”，截图是否有两个“未申请”。
2. 在智能问答补齐 `BUG-G16-003` 的 Network/Timing/刷新恢复证据。
3. 在通知页面人工点击附件预览，确认小程序端是否可打开，不只依赖接口下载成功。
4. 在学业分析页面做非 PDF/空文件页面级校验，观察是否有前端提示或白屏。

