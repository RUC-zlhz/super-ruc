# Customer Needs: 信息学院学生综合服务与党团管理平台

**Version:** 1.1 | **Created:** 2026-04-13 | **Last Updated:** 2026-05-12

## Needs Summary

- **Information:** 8
- **Control:** 4
- **Construction:** 3
- **Entertainment:** 0

### CN-001: 官方政策与流程自助知悉

**Statement:** 学生需要平台提供基于官方来源的政策、资格、材料与流程说明，并在办理常见事务前可随时查询。  
**Outcome Class:** Information  
**Traces to:** CP-001, CP-002, CP-010

### CN-002: 知识与模板的持续维护

**Statement:** 管理员需要平台创建和更新知识条目、模板文件与来源版本，并在政策调整后能够持续修订。  
**Outcome Class:** Construction  
**Traces to:** CP-001, CP-006, CP-010

### CN-003: 党团阶段与下一动作可见

**Statement:** 学生需要平台提供本人党团流程中的当前阶段、已完成事项与下一节点信息，并可在任意时间查看。  
**Outcome Class:** Information  
**Traces to:** CP-003

### CN-004: 党团流程节点持续管理

**Statement:** 党团老师与团支书需要平台管理党团流程节点、提醒规则与完成记录，并按阶段持续跟踪。  
**Outcome Class:** Control  
**Traces to:** CP-003, CP-004

### CN-005: 常见事务在线发起

**Statement:** 学生需要平台创建请假、盖章、证明、报名与材料提交等常见事务申请，并在提交时附带所需信息或附件。  
**Outcome Class:** Construction  
**Traces to:** CP-002, CP-005

### CN-006: 审批前完整获知材料与历史

**Statement:** 审批老师需要平台提供申请材料、流转历史与附件内容，并在作出处理前完整查看。  
**Outcome Class:** Information  
**Traces to:** CP-004, CP-005

### CN-007: 驳回、撤回与重提的规则管理

**Statement:** 审批老师与管理员需要平台管理驳回、撤回、重提、重批与留痕规则，并在至少一个学期内保持可追溯。  
**Outcome Class:** Control  
**Traces to:** CP-004, CP-005

### CN-008: 文件交换与主数据维护

**Statement:** 数据管理员需要平台创建和更新学生主数据、模板文件与业务台账，并通过 Excel、Word、PDF 文件交换保持一致。  
**Outcome Class:** Construction  
**Traces to:** CP-006

### CN-009: 标签化通知任务管理

**Statement:** 管理员需要平台管理带标签的通知任务与目标人群规则，并按年级、专业、身份等条件分发。  
**Outcome Class:** Control  
**Traces to:** CP-008

### CN-010: 与本人相关的通知及时可见

**Statement:** 学生需要平台提供与本人画像匹配的通知与办理提醒，并在重要变化发生后及时获知。  
**Outcome Class:** Information  
**Traces to:** CP-008

### CN-011: 敏感字段与导出权限受控

**Statement:** 班主任、辅导员和超级管理员需要平台控制敏感字段可见性、导出权限与访问审计，并按角色范围最小授权。  
**Outcome Class:** Control  
**Traces to:** CP-004, CP-007

### CN-012: 弱结论学业风险提示

**Statement:** 学生需要平台提供学业完成缺口与风险提示，并仅基于可核验的数据做展示而不直接给出毕业结论。  
**Outcome Class:** Information  
**Traces to:** CP-009

### CN-013: 学院运营统计汇总

**Statement:** 学院领导与业务负责人需要平台提供党团工作量、审批进度、通知触达与服务使用情况统计，并按学期汇总查看。  
**Outcome Class:** Information  
**Traces to:** CP-004, CP-008

### CN-014: 校级及以上荣誉集中公示

**Statement:** 学生与学院需要平台提供校级及以上正式荣誉的集中榜单、详情与授权状态，并在按类别、学年或级别筛选后可查看。  
**Outcome Class:** Information  
**Traces to:** CP-011

### CN-015: 学籍与成长数据聚合画像

**Statement:** 学院需要平台提供聚合后的学籍与成长数据画像，并在职责范围内共享查看与核对。  
**Outcome Class:** Information  
**Traces to:** CP-012

## Zigzag Validation: CP → CN

### Coverage Table

| Customer Problem | Covered by Customer Needs | Completeness | Notes |
|------------------|---------------------------|--------------|-------|
| CP-001 | CN-001, CN-002 | Complete | 自助答疑与后台维护共同支撑统一口径 |
| CP-002 | CN-001, CN-005 | Complete | 同时覆盖办理前说明与在线申请 |
| CP-003 | CN-003, CN-004 | Complete | 同时覆盖学生可见与管理跟踪 |
| CP-004 | CN-004, CN-006, CN-007, CN-011, CN-013 | Complete | 覆盖留痕、审批依据、权限与统计 |
| CP-005 | CN-005, CN-006, CN-007 | Complete | 覆盖申请、审批查看与状态管理 |
| CP-006 | CN-002, CN-008 | Complete | 兼顾内容维护与文件交换 |
| CP-007 | CN-011 | Complete | 字段权限、导出与审计集中承接 |
| CP-008 | CN-009, CN-010, CN-013 | Complete | 同时覆盖管理侧分发与学生侧接收 |
| CP-009 | CN-012 | Complete | 保持弱结论边界 |
| CP-010 | CN-001, CN-002 | Complete | 内容可信与版本治理共同承接 |
| CP-011 | CN-014 | Complete | 集中公示、授权状态与筛选查看共同承接 |
| CP-012 | CN-015 | Complete | 学籍与成长信息聚合后形成共享视图 |

### Orphan Check

| Item | Status | Notes |
|------|--------|-------|
| Uncovered CPs | None | 12/12 个 CP 均至少映射到 1 个 CN |
| Orphan CNs | None | 15/15 个 CN 均可回溯到至少 1 个 CP |
| Cross-boundary Risks | 2 | CN-005/007 与校级正式流程边界；CN-012 与学业强结论边界，已保留为约束说明 |

### Validation Notes

- `CP-005` 的正式效力边界未在原始资料中完全拍板，因此后续 FR 需把“引导/归档/学院内部审批”与“校级正式生效”明确分开。
- `CN-012` 明确限定为风险提示而非毕业判断；该能力已纳入一期正式范围，但必须以弱结论边界、规则维护和样例数据兜底实施。
- `CN-011` 已由 `S4A.1` 形成默认字段策略基线；后续仍可在业务最终确认后扩展角色-字段矩阵细节，但不再构成上游 CN 缺口。
- `CN-008` 的 S12 增量默认导入仅消费仓库登记的数据源；学生默认导入不推断专业、年级、班级，培养方案默认导入仅生成并维护 `2024-default` 演示版本，不覆盖教师后续维护版本。
- `CN-001 / CN-002 / CN-010 / CN-012` 的 S12/S13 增量分别收口为结构化官方来源标识优先与模板下载权限、公众号手工录入和公开 URL/RSS 受控抓取并只生成草稿通知、SMS mock/local provider + retry/receipt、成绩单 PDF 候选批次与教师核验提交后写正式记录。
