# Customer Problems: 信息学院学生综合服务与党团管理平台

**Version:** 1.0 | **Created:** 2026-04-13 | **Last Updated:** 2026-04-13

## Problem Summary

- **Obligations:** 4
- **Expectations:** 6
- **Hopes:** 0
- **Input Basis:** `docs/srs/00-business-context.md`、`需求文档.md`、`需求补充.md`

### CP-001: 高频答疑一致性不足

**Statement:** 学院学生工作团队 expects 高频政策与流程问题得到一致且及时的答复 otherwise 老师会持续消耗在重复解释上且学生会收到相互矛盾的指引。  
**Classification:** Expectation  
**Subject:** 学院学生工作团队、学生  
**Consequence if Unsolved:**
- 老师被大量低价值重复答疑占用时间
- 学生对资格、流程、材料理解不一致
- 错办、漏办与投诉风险持续存在
**Benefit if Solved:**
- 常见问题可由统一口径自助消化
- 老师集中精力处理复杂个案
- 学生获取更稳定的办事体验

### CP-002: 学生缺少清晰办事路径

**Statement:** 学生 expect 在办理常见事务前明确知道资格、材料、步骤与时间节点 otherwise 会反复咨询老师、提交错误材料或错过办理期限。  
**Classification:** Expectation  
**Subject:** 学生  
**Consequence if Unsolved:**
- 学生因不熟悉流程而误办或漏办
- 办理前的确认沟通被不断放大
- 时间敏感事务容易错过节点
**Benefit if Solved:**
- 学生能在办理前完成自查与准备
- 办理效率和一次性通过率提升
- 管理端前置沟通压力下降

### CP-003: 党团流程节点缺少持续跟踪

**Statement:** 党团工作负责人 must 跟踪每名学生在党团流程中的当前阶段、已完成动作与关键时间节点 otherwise 必要材料、汇报或阶段转换会被遗漏且组织记录不完整。  
**Classification:** Obligation  
**Subject:** 党团老师、团支书、党支部书记等流程负责人  
**Consequence if Unsolved:**
- 关键节点依赖人工记忆，遗漏概率高
- 学生无法判断自己处于哪个阶段
- 党团工作记录不连续，后续核验困难
**Benefit if Solved:**
- 流程节点透明且可追踪
- 关键动作能在正确时间触发
- 组织工作更规范、可审查

### CP-004: 学院缺少客观留痕与工作记录

**Statement:** 学院管理方 must 保留审批、配置、通知与党团工作的完整留痕 otherwise 无法有效追责、复盘纠错或客观衡量工作量。  
**Classification:** Obligation  
**Subject:** 学院管理方、学院领导  
**Consequence if Unsolved:**
- 责任链条模糊，纠错成本高
- 工作量统计与绩效佐证不足
- 关键历史记录难以回溯
**Benefit if Solved:**
- 管理动作可审计、可追溯
- 工作记录可用于统计与复盘
- 管理流程更透明、可问责

### CP-005: 常见事项仍依赖碎片化线下审批

**Statement:** 学生与审批老师 expect 请假、盖章、证明、报名与材料提交等常见事务在线完成并可跟踪状态 otherwise 线下往返、材料分散与状态不透明会持续降低效率。  
**Classification:** Expectation  
**Subject:** 学生、审批老师  
**Consequence if Unsolved:**
- 学生需要重复往返或多轮沟通
- 审批老师难以统一查看材料与历史
- 学院平台与正式流程边界容易被误解
**Benefit if Solved:**
- 常见事务能形成可追踪的处理闭环
- 审批依据更集中，效率更高
- 学生知道哪些环节可线上处理、哪些需转正式链路

### CP-006: 无法依赖校级接口导致数据交换效率低

**Statement:** 学院数据管理员 must 在无法直连校级系统接口的情况下持续交换并维护业务数据 otherwise 学生基础数据、模板和业务台账会重复录入、版本失控或中断更新。  
**Classification:** Obligation  
**Subject:** 超级管理员、数据维护老师  
**Consequence if Unsolved:**
- 数据只能靠零散人工搬运
- 各类模板与台账版本不一致
- 平台内容与真实业务状态脱节
**Benefit if Solved:**
- 学院在接口受限场景下仍能保持业务连续性
- 模板与数据版本更可控
- 导入导出成为稳定运营能力

### CP-007: 敏感学生信息存在越权风险

**Statement:** 学院 must 保护敏感学生字段并限制字段级可见性与导出权限 otherwise 会发生隐私泄露、越权访问与管理责任风险。  
**Classification:** Obligation  
**Subject:** 学院、数据治理责任人  
**Consequence if Unsolved:**
- 身份证号、生源地等敏感信息暴露
- 非授权角色看到不应访问的数据
- 学院面临信任和合规压力
**Benefit if Solved:**
- 敏感数据在最小范围内使用
- 字段访问更符合职责边界
- 数据治理能力可持续演进

### CP-008: 通知触达不精准且来源分散

**Statement:** 学生与负责老师 expect 重要通知及时到达正确人群 otherwise 相关机会和要求会被错过且无差别群发会制造高噪音。  
**Classification:** Expectation  
**Subject:** 学生、班主任、辅导员、学院老师  
**Consequence if Unsolved:**
- 就业、实习、活动等通知容易漏达
- 非目标学生接收大量无关信息
- 老师仍需手工筛选与多轮转发
**Benefit if Solved:**
- 目标通知更快触达目标对象
- 信息噪音减少，阅读意愿提升
- 通知运营效率更高

### CP-009: 学业风险识别滞后且误导成本高

**Statement:** 学生 expect 尽早识别学业完成缺口和潜在风险 otherwise 选课与修读安排会持续被动且临近毕业时才暴露问题。  
**Classification:** Expectation  
**Subject:** 学生  
**Consequence if Unsolved:**
- 学分缺口或课程类型不匹配发现过晚
- 学生持续依赖人工解释和手工比对
- 错误结论可能直接影响毕业判断
**Benefit if Solved:**
- 学生更早看到风险信号
- 学业规划从被动补救转向前置提醒
- 学院可在不做强结论的前提下提供辅助服务

### CP-010: 官方内容缺少持续治理

**Statement:** 学院内容维护方 must 确保咨询内容、通知与模板基于官方且最新版本 otherwise 过期信息或不准确回复会误导学生处理敏感事务。  
**Classification:** Expectation  
**Subject:** 知识库维护老师、管理员  
**Consequence if Unsolved:**
- 平台问答与文件链接可能引用旧口径
- 学生对平台可信度下降
- 复杂或敏感场景更容易被误导
**Benefit if Solved:**
- 平台内容保持权威性与时效性
- 学生能据此进行准确自助判断
- AI 或搜索能力有可靠边界和来源支撑

## Classification Overview

| Class | Count | CP IDs |
|------|-------|--------|
| Obligation | 4 | CP-003, CP-004, CP-006, CP-007 |
| Expectation | 6 | CP-001, CP-002, CP-005, CP-008, CP-009, CP-010 |
| Hope | 0 | None |

## Notes

- 已刻意去除“采用何种技术实现”的描述，保留业务后果与管理痛点。
- “正式校级流程是否可被学院平台替代”被视为边界问题，不直接写成解决方案，而在后续 CN/FR 中约束为引导与留痕能力。
- 学业模块虽具有较高数据与责任边界风险，但已按弱结论能力纳入一期正式范围。
