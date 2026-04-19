# S2 核心用户闭环二次收口细化

- 日期：`2026-04-19`
- 关联主计划：`S2A.1, S2A.2, S2A.3, S2A.4, S2A.5, S2B.1, S2B.2, S2B.3, S2B.4, S2B.5, S2C.1, S2C.2, S2C.3, S2C.4, S2C.5`
- 当前状态：`DONE`
- 替代关系：本文件是 `S2` 的当前生效收口细化；[2026-04-18-s2-core-user-loops-refinement.md](D:/Codes/super-ruc/docs/notes/refinements/2026-04-18-s2-core-user-loops-refinement.md) 保留为初版拆分记录，不再作为当前完成态判断依据。

## 目标

- 基于 `S1` 已冻结的 canonical contract，把通知、事务申请/证明、学业分析/运营看板三条用户闭环收口到“可操作、可验证、可回写”的完成态。
- 本轮不回退 `S1` 命名，不新增旧路径/旧字段兼容层，只补闭环缺口。

## 已完成收口

### [x] S2A 通知闭环

- 管理端 `NoticeList` 已扩成单页闭环，包含圈人规则编辑、命中预览、发布、发送、批次查看和投递明细抽屉。
- 后端学生详情权限已收紧为“当前学生存在投递记录才能查看”，已读写入继续按本人 `delivery_id` 生效。
- 管理端治理字段已固定可见：`source_type`、`channels`、`batch status`、`failed_count`、`error_code`、`error_message`、`read_at`。
- `backend/tests/integration/test_notice_flow.py` 已补本人可见性、本人已读写入、管理端治理视图断言。

### [x] S2B 事务申请与证明闭环

- Miniapp `request/create` 已切为“两步式”草稿 -> 附件上传 -> 提交/重提；`request/detail` 已补证明 PDF 预览与草稿/驳回继续编辑入口。
- Web `ApprovalDetail` 已升级为四段式结构化视图：申请信息、附件、历史流转、当前动作。
- Web / Miniapp 的 request canonical 文案已收口到共享 helper，覆盖 `SUBMITTED / IN_REVIEW / REJECTED / WITHDRAWN / OFFLINE_HANDLE / RESUBMIT`。
- `backend/tests/integration/test_request_flow.py` 已锁定附件 canonical 字段、proof-preview PDF stream、`OFFLINE_HANDLE`、proof-preview 越权失败等关键路径。

### [x] S2C 学业分析与运营看板闭环

- 学生端学业页已稳定消费 canonical `AcademicGapResult`，持续显示 `disclaimer` 与 `data_warnings`。
- 后端已新增 `GET /admin/report/academic-gap` 聚合查询，返回 `items + meta`，支持 `keyword / grade_code / major_code / risk_level / page / page_size`。
- Web `OperationDashboard` 已基于 canonical `overview` 完成轻量图表、空态、弱结论提示，并接入 academic-gap 聚合筛选、列表和明细抽屉。
- `backend/tests/integration/test_report_contract_flow.py` 已补聚合查询 contract smoke、风险过滤和 detail drilldown 断言。

## 验证证据

- `D:\Codes\super-ruc\backend`：`uv run pytest tests/integration -q` -> `47 passed, 1 warning in 133.12s`
- `D:\Codes\super-ruc\web`：`pnpm -C web build` 通过
- `D:\Codes\super-ruc\miniapp`：`pnpm -C miniapp build:mp-weixin` 通过
- 页面范围收口到固定联调清单：
  - Web：`NoticeList`、`ApprovalDetail`、`OperationDashboard`
  - Miniapp：`notice`、`academic`、`request/create`、`request/detail`

## 备注

- `request/index` 额外补做了 canonical 状态文案收口，避免列表页与详情页展示分叉。
- 本轮未吸收 `S3 / S4` 需求；唯一保留风险是 `honor` 模块仍存在既有 `utcnow()` 弃用 warning，与 `S2` 无直接关联。
