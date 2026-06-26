# S74 教师审批附件下载入口补齐

- 状态：`[-]` 代码已完成，DB 集成回归待本机 Docker / `localhost:54322` 测试库恢复后补跑
- 日期：`2026-06-13`
- 关联主计划：`S74.1 ~ S74.5`

## 问题

- 教师在管理端审批详情页可以看到“附件列表”，但附件行只展示文件名、类型、大小和上传时间，没有下载按钮。
- 后端已有申请附件上传与对象存储元数据，但缺少受权限保护的申请附件下载接口。
- 用户在截图中的材料提交申请 `MATE-260613114430-C418B0` 已显示附件 `tmp_2462d30d02c1de83d61a8f74951df088ca00d5a3836ce580fc35dbadaa92d84a.docx`，教师需要在审批详情页直接下载。

## 实施内容

- 后端新增 `GET /api/v1/requests/{request_id}/attachments/{attachment_id}/download`。
- 下载接口复用申请详情可见性校验：学生本人、全局审批角色、以及具备学生范围权限的协同/审批角色可下载；越权访问写入拒绝审计。
- 下载成功写入 `REQUEST_ATTACHMENT / DOWNLOAD_ATTACHMENT` 审计，保留 `request_id`、`attachment_id` 与文件名引用。
- Web 管理端 `审批详情 -> 附件列表` 每个附件行新增“下载”按钮，复用既有 `downloadFile` blob 下载工具。
- 回归测试扩展 `test_request_detail_contract_uses_canonical_attachment_and_approval_fields`，覆盖学生本人和辅导员下载同一附件的文件内容与响应文件名。

## 验证

- `uv run --extra dev ruff check app/workflow/router.py app/workflow/service.py tests/integration/test_request_flow.py` 通过。
- `uv run --extra dev python -m py_compile app/workflow/router.py app/workflow/service.py` 通过。
- `corepack pnpm -C web build` 通过。
- `uv run --extra dev pytest tests/integration/test_request_flow.py::test_request_detail_contract_uses_canonical_attachment_and_approval_fields -q` 未进入业务断言：本机 Docker Desktop 未运行，测试库 `localhost:54322/sip_db_test` 连接被拒绝，错误为 `ConnectionRefusedError: [WinError 1225]`。

## 后续

- [ ] Docker / 测试库恢复后补跑上述定向 DB 集成测试。
- [ ] 部署到生产后，在教师管理端审批详情页点击附件“下载”做一次真实浏览器验收。
