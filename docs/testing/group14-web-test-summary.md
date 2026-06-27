# 第 14 组 Web 互测补充资料摘要

- 测试方：第 12 组
- 被测方：第 14 组
- 新增资料：`http://183.174.61.212:8001/uploads/784ad38352564ddcb562ebdd2c9f4ae7.md`
- 本地保存：`tmp/docs/group14/platform-documents/group14-extra.md`
- 结论：该 Markdown 提供的是 Web 互测指南，不是微信小程序源码包。

## 可访问入口

- 本地测试默认地址：`http://127.0.0.1:5173/`
- 服务器测试地址：`http://10.10.0.14/`
- 实测服务器首页：`GET http://10.10.0.14/` 返回 `200`
- 实测健康检查：`GET http://10.10.0.14/api/health` 返回 `student-services-backend`、`status=ok`

## 演示账号烟测

| 角色 | 账号 | 密码 | 登录烟测 |
| --- | --- | --- | --- |
| 管理员 | `demo.admin` | `demo1234` | 成功，角色 `admin` |
| 教师 | `demo.teacher` | `demo1234` | 成功，角色 `teacher` |
| 学生 | `demo.student` | `demo1234` | 成功，角色 `student` |
| 班团骨干 | `demo.secretary` | `demo1234` | 成功，角色 `league_secretary` |
| 领导 | `demo.leader` | `demo1234` | 成功，角色 `leader` |

## Web 功能范围

- 通用功能：首页访问、统一登录、退出登录、侧边栏、响应式布局。
- 学生端：学生工作台、党团流程、政策检索、线上审批、画像变更申请、电子证明、通知与提醒、权限边界。
- 管理端：学生导入与画像审核、班团组织维护、政策知识库、通知发布、业务模板配置、电子证明、操作日志。
- 领导端：统计概览、审批队列、处理审批、附件下载、审批台账导出、运行统计。
- 专项闭环：通知、政策、画像变更、电子证明、审批。

## 对“小程序配置”的影响

- 新增 Markdown 没有提供 `project.config.json`、`app.json`、`pages.json`、`manifest.json`、`package.json` 或源码包下载地址。
- 新增 Markdown 的入口是浏览器 Web 地址 `http://10.10.0.14/`，不是微信开发者工具可导入的小程序项目。
- 因此第 14 组当前可以继续做 Web 互测，但仍不能完成“本地配置微信小程序”。

