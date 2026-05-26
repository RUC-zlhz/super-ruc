# S57 生产证明 PDF 预览验证与使用说明校正

- 状态：`[x]` 已完成
- 日期：`2026-05-26`
- 目标：验证生产环境中证明 PDF 预览的真实开放条件，并将 `docs/source/user-manual.md` 的说明改为与后端行为、小程序展示和生产验证一致。

## 验证结论

- 生产当前存在 1 个有效证明模板：`CERTIFICATE_IN_SCHOOL_V1`，绑定申请类型 `CERTIFICATE_IN_SCHOOL`，申请类型分类为 `CERTIFICATE`。
- 验证前生产 `requests_total=0`；本轮通过学生账号创建了 1 条带 `[验证]` 标记的在读证明申请。
- 新建草稿状态 `DRAFT` 请求 `/api/v1/workflow/proof-preview/{id}` 返回 `40029`，提示“仅已批准的申请可预览证明 PDF，当前状态 DRAFT”。
- 提交后状态 `SUBMITTED` 请求同一预览接口仍返回 `40029`，提示“仅已批准的申请可预览证明 PDF，当前状态 SUBMITTED”。
- 申请审批为 `APPROVED` 后，学生侧请求预览接口返回 `200`、`content-type=application/pdf`，响应体以 `%PDF-1.7` 开头，证明 PDF 生成与下载链路可用。

## 生产事实

- 生产当前只有 `SUPER_ADMIN` 与 1 个学生账号。
- `CERTIFICATE_IN_SCHOOL` 的 `approver_roles` 为 `COUNSELOR`；使用 `admin / SUPER_ADMIN` 登录态审批该申请会返回 `40304` “无权审批该类型申请”。
- 本轮为验证 PDF 生成链路，使用生产后端签发的临时 `COUNSELOR` claim 调用审批接口完成审批；这不改变用户角色表，但说明正式使用时需要具备 `COUNSELOR` 角色的教师账号，或后续调整证明类申请的审批角色配置。

## 文档修正

- `docs/source/user-manual.md` 模块四说明已从“提交前生成 PDF 证明预览”改为“申请审批通过后生成可在申请详情中预览的 PDF 证明”。
- 当前权威口径：证明类申请不是“发起后即可预览”，而是“审批通过后开放 PDF 预览”。
