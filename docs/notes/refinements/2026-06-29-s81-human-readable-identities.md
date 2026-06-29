# S81 审批与导出可读身份展示修复

- 关联主计划：`S81.1 ~ S81.5`
- 状态：`[-]` 进行中
- 日期：`2026-06-29`
- 范围：修复用户反馈的审批详情、审批列表和成绩单导出中直接展示内部 `user_id/student_id/operator_id`，导致无法判断具体人员的问题。

## 问题结论

- 管理端审批详情把 `applicant_user_id`、`applicant_student_id`、`decided_by` 原样展示给老师；小程序申请详情的审批时间线也显示“操作人 ID”。这些是数据库内部键，不适合业务人员识别。
- 成绩单导出 Excel 以 `student_id` 作为首列，缺少学生姓名和学号；这会让导出文件脱离数据库后不可读。
- 审批工作台搜索框写着“单号 / 申请人 / 标题”，但后端关键字查询没有匹配学生姓名和学号。

## 执行拆分

- [x] `S81.1` 后端申请列表和详情响应补申请人姓名、学号、申请账号名。
- [x] `S81.2` 后端审批详情补审批人姓名/工号和审批记录操作人姓名/工号/学生姓名/学号。
- [x] `S81.3` Web 审批详情、审批工作台和 Miniapp 申请详情改为展示可读身份，不再面向用户显示裸 ID。
- [x] `S81.4` 成绩单导出首列改为 `student_no/full_name`，移除 `student_id` 导出识别列。
- [-] `S81.5` 补定向回归并完成后端、Web、小程序验证。

## 代码范围

- 后端：`backend/app/workflow/{models,repository,schemas,service}.py`、`backend/app/exchange/router.py`
- Web：`web/src/api/workflow.ts`、`web/src/views/approval/{ApprovalDetail,WorkbenchList}.vue`
- Miniapp：`miniapp/src/api/workflow.ts`、`miniapp/src/pages/request/detail.vue`
- 测试：`backend/tests/integration/test_request_flow.py`、`backend/tests/integration/test_exchange_flow.py`

## 验证计划

- 后端静态：`ruff`、`py_compile`
- 后端定向 DB 集成：申请流身份字段回归、成绩单导出列回归
- 前端：Web `vue-tsc` / build，Miniapp `vue-tsc` / `mp-weixin` build
