# Feature Specification: Student Service Platform

**Feature Branch**: `main`  
**Created**: 2026-04-13  
**Status**: Draft  
**Input**: User description: "读取 docs/srs/ 下的追踪矩阵和所有 FR/NFR，依据 `.spec-kit/constitution.md` 生成技术规格，按知识库、流程、审批、通知、审计五个核心闭环拆解，补充 Kingbase 数据建模、离线文件流转协议和 FR 追溯标签。"

> 说明：`知识库、流程、审批、通知、审计` 五个闭环是技术拆解主线，不代表范围删减；`需求文档.md` 中提出的受控 AI 匹配问答、理论自测、官方通知汇聚、短信通道、证明 PDF 预览、学业课程建议等能力均已纳入本规格，并分别映射到对应闭环。
> v1.5 / v1.6 补充：`docs/source/additional-request.txt` 中的奖励荣誉展示与学生画像能力已纳入本规格，分别追溯为 `FR-017` 与 `FR-018`，并作为“展示与画像闭环”补充到一期范围。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 官方知识自助闭环 (Priority: P1)

作为学生，我希望在提交任何学院事务前，先通过统一入口找到官方政策、标准答案、模板和办理说明，
这样我可以减少反复咨询并按正确材料和流程办事。

**Why this priority**: 这是整个系统的入口价值，也是减少老师重复答疑的直接手段；没有这一层，
后续流程提交会持续受到错误材料和错误预期影响。

**Independent Test**: 仅实现知识库闭环后，学生仍可独立完成“检索政策 → 查看官方来源 →
下载模板 → 判断是否需要转人工”的完整自助流程，并直接获得业务价值。

**Acceptance Scenarios**:

1. **Given** 学生需要办理证明，**When** 学生搜索对应事项，**Then** 系统展示官方说明、所需材料、办理步骤与模板下载入口。
2. **Given** 某条知识内容处于模糊或敏感场景，**When** 学生查看内容，**Then** 系统展示官方来源并提示转人工咨询路径。
3. **Given** 学生以自然语言输入问题，**When** 系统启用受控 AI 匹配，**Then** 返回内容必须基于标准答案、知识条目或官方链接，不得输出无来源结论。

---

### User Story 2 - 流程与审批闭环 (Priority: P1)

作为学生、班团骨干和审批老师，我希望围绕党团流程与常见事务申请形成统一的状态流转和审批闭环，
这样我可以知道当前阶段、下一动作、审批意见和重提规则。

**Why this priority**: 这是学院事务线上化的核心交付，没有流程与审批闭环，平台只能停留在信息展示层。

**Independent Test**: 仅实现流程与审批闭环后，用户仍可独立完成“查看党团状态 / 提交事务申请 /
老师审核 / 驳回后重提 / 查询历史状态”的主要业务流程。

**Acceptance Scenarios**:

1. **Given** 学生已登录且具有有效身份，**When** 学生查看党团页面，**Then** 系统展示当前阶段、已完成节点和下一动作。
2. **Given** 学生提交一项学院事务申请，**When** 审批老师处理该申请，**Then** 系统保留材料、审批意见、处理状态和时间顺序记录。
3. **Given** 申请被驳回，**When** 学生重新进入申请页面，**Then** 系统保留原始表单内容并允许在规则范围内修改后重提。
4. **Given** 学生发起证明申请，**When** 系统加载标准模板和本人基础信息，**Then** 系统可生成自动填充后的 PDF 预览供学生与审批人查看。
5. **Given** 团委老师导入官方题库，**When** 学生进入理论自测页面，**Then** 系统支持答题、计分和结果留存。

---

### User Story 3 - 通知触达闭环 (Priority: P2)

作为管理员和学生，我希望通知能够按年级、专业、身份和业务标签被精准投递并可回看记录，
这样目标人群能及时收到相关信息，非目标人群不会被无关通知干扰。

**Why this priority**: 通知是学院高频运营动作，精准触达直接影响就业、报名、活动和事务办理效率。

**Independent Test**: 仅实现通知闭环后，管理员仍可创建通知、选择目标范围、发送到站内消息、邮件与短信，
学生也可独立查看属于自己的通知列表。

**Acceptance Scenarios**:

1. **Given** 管理员创建了带标签的通知，**When** 管理员按画像规则选择目标人群，**Then** 系统展示目标范围并发送到对应学生。
2. **Given** 学生属于目标范围，**When** 学生打开通知中心，**Then** 系统展示该通知及其发布时间、标签和状态。
3. **Given** 学校官方公众号或公开网站存在新通知，**When** 管理员执行受控抓取或手工录入，**Then** 系统生成可治理的通知条目并保留来源信息。
4. **Given** 通知开启短信通道，**When** 目标学生存在有效手机号，**Then** 系统记录短信批次、发送状态和失败原因。

---

### User Story 4 - 审计与离线流转闭环 (Priority: P2)

作为管理员和学院业务负责人，我希望所有关键动作都留痕，并且在没有校级 API 的情况下，
仍可以通过 Excel、Word、PDF 实现稳定的离线数据流转。

**Why this priority**: 这是项目宪章中的强约束；没有留痕和离线流转，系统既不可信，也无法在真实环境中运行。

**Independent Test**: 仅实现审计与离线流转闭环后，管理员仍可完成结构化数据导入、导出、校验失败回滚、
日志查询和错误复盘。

**Acceptance Scenarios**:

1. **Given** 管理员上传标准 Excel，**When** 系统完成结构校验和业务校验，**Then** 系统要么一次性提交全部变更，要么整体回滚并输出错误报告。
2. **Given** 管理员执行导出或权限变更，**When** 操作完成，**Then** 系统记录操作者、时间、对象、结果和文件批次。

---

### User Story 5 - 学业分析与预警闭环 (Priority: P3)

作为学生和业务负责人，我希望系统在有结构化培养方案和成绩数据时给出学业风险提示与课程类型级选课建议，
但不会越权给出毕业资格等强结论。

**Why this priority**: 学业模块存在较高数据和责任边界风险，因此安排在后置联调阶段实施；但该模块仍属于一期正式交付范围。

**Independent Test**: 仅实现学业分析与预警闭环后，学生仍可看到缺口模块、人工核验提示和课程类型级建议，而无需依赖毕业判定功能。

**Acceptance Scenarios**:

1. **Given** 学生成绩单与培养方案规则可用，**When** 系统生成学业分析结果，**Then** 页面仅展示缺口、风险提示和人工核验说明。
2. **Given** 成绩或规则数据不完整，**When** 学生访问学业分析页，**Then** 系统明确提示结果不可用于最终资格判断。
3. **Given** 本学期开设课程清单可用，**When** 系统识别学生缺失模块，**Then** 页面可给出课程类型级选课建议，但不展示动态抢课人数或作出毕业结论。

---

### User Story 6 - 荣誉展示与学生画像闭环 (Priority: P3)

作为学生、辅导员、班主任和学院领导，我希望系统集中展示正式荣誉并聚合学生成长画像，
这样先进典型可以被合规公示，学生成长数据也能在权限范围内被完整查看和维护。

**Why this priority**: 荣誉与画像属于学院服务的展示和管理补充闭环，依赖学籍、权限、审计和离线导入能力，
因此安排在核心流程闭合后实施，但仍属于一期正式交付范围。

**Independent Test**: 仅实现展示与画像闭环后，用户仍可独立完成“浏览荣誉榜单 / 查看荣誉详情 /
辅导员查看画像 / 学生查看本人画像并发起纠错申诉”的完整流程。

**Acceptance Scenarios**:

1. **Given** 管理员已导入经审核的校级及以上荣誉，**When** 学生进入荣誉榜单，**Then** 系统按类别和学年展示获奖者、荣誉名称、授予单位、公示日期和事迹摘要。
2. **Given** 荣誉已过期、撤销或归档，**When** 用户浏览荣誉信息，**Then** 系统默认不主动推送该条目，并在历史入口标注“历史荣誉”。
3. **Given** 辅导员具备所带班级权限，**When** 辅导员查看学生画像，**Then** 系统聚合展示学籍静态字段和科研、竞赛、实践、志愿服务、学生干部任职等动态成长字段，并显示来源、录入人和最后更新时间。
4. **Given** 学生本人查看画像，**When** 页面展示本人信息，**Then** 系统隐藏管理元数据，提供纠错申诉入口，并且不得输出自动评分、排名或评价结论。

### Edge Cases

- 当知识内容已过期但仍被查询时，系统如何阻止其作为最新口径继续展示？
- 当学生重复提交同一事项、同一时间段或同一附件时，系统如何识别重复与冲突？
- 当 Excel 批量导入中存在单行严重错误时，系统是否整批回滚还是部分提交？
- 当 PDF 成绩单无法稳定解析必填字段时，系统如何阻止错误结果进入学业分析？
- 当某事务必须由校级系统正式生效时，学院平台如何展示“仅预检 / 归档 / 跟踪”的边界？
- 当角色权限变化发生在审批中途时，系统如何处理未完成任务与可见范围变更？
- 当荣誉获得者已毕业或撤回授权时，系统如何保留历史记录但隐藏联系方式等敏感信息？
- 当学生画像扩展字段来源不一致或存在争议时，系统如何标注来源并进入纠错申诉流程？

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 提供按关键词、分类、标签检索学院官方政策与流程说明的能力，并支持基于标准答案和官方链接的受控 AI 匹配答复。
- **FR-002**: 系统 MUST 为知识内容显示官方来源、版本、更新时间，并为模糊或敏感场景提供人工兜底提示。
- **FR-003**: 系统 MUST 允许授权管理员创建、更新、停用和版本化管理知识条目与模板文件。
- **FR-004**: 系统 MUST 向学生展示本人党团流程的当前阶段、已完成事项和下一动作。
- **FR-005**: 系统 MUST 允许授权角色维护党团流程节点、提醒规则、官方题库、到期状态、自测记录与完成记录。
- **FR-006**: 系统 MUST 支持学生在线提交请假、盖章、证明、报名与材料提交等常见事务申请，并在证明场景支持基于模板自动生成 PDF 预览。
- **FR-007**: 系统 MUST 为审批人提供查看申请详情、附件、历史流转和当前状态的统一审核视图。
- **FR-008**: 系统 MUST 支持驳回、撤回、重提和受控重批，并保持状态与历史一致。
- **FR-009**: 系统 MUST 支持授权管理员通过 Excel、Word、PDF 导入导出学生主数据、模板、通知和业务记录。
- **FR-010**: 系统 MUST 允许授权角色通过受控抓取或人工录入汇聚官方通知，为通知设置标签并根据画像属性圈定目标范围。
- **FR-011**: 系统 MUST 记录通知发送批次、目标范围、站内消息 / 邮件 / 短信发送结果，并向目标学生展示相关通知。
- **FR-012**: 系统 MUST 按角色与字段粒度控制学生数据、业务记录和导出权限。
- **FR-013**: 系统 MUST 记录审批、配置变更、内容发布停用、导出和敏感访问等审计日志。
- **FR-014**: 系统 MUST 在规则与成绩数据可用时展示学业缺口、风险提示和课程类型级选课建议，而不输出毕业强结论。
- **FR-015**: 系统 MUST 允许授权角色维护培养方案、模块规则、课程等价关系和开课信息。
- **FR-016**: 系统 MUST 为授权领导与业务负责人提供按学期汇总的党团记录、审批进度、通知触达和服务使用情况。
- **FR-017**: 系统 MUST 支持录入或批量导入校级及以上正式荣誉，按类别和学年公示荣誉榜单与详情，展示获奖者基本信息、荣誉名称、授予单位、文号或证书编号、公示日期和事迹摘要，并支持历史荣誉、归档、撤销、维护人和更新时间留痕。
- **FR-018**: 系统 MUST 聚合学生学籍核心字段与科研项目、学科竞赛、社会实践、志愿服务、学生干部任职等动态成长字段，支持授权角色按权限检索、筛选和导出画像快照，学生仅可查看本人画像并提交纠错申诉，且系统不得输出自动评分、排名或评价结论。

### Integration & Compliance Requirements *(mandatory for this project)*

- **ICR-001**: 本特性 MUST 明确依赖 `Excel / Word / PDF` 离线导入导出，不得把校级 API 作为前置条件。
- **ICR-002**: 本特性 MUST 明确识别并保护身份证号、联系方式、处分记录、政治面貌、成绩等敏感或受限字段。
- **ICR-003**: 本特性 MUST 保持前后端分离，所有权限判断、审计记录、数据加密和业务状态变更都在后端执行。
- **ICR-004**: 本特性 MUST 把所有数据表结构、索引和 SQL 约束设计为 Kingbase 兼容。
- **ICR-005**: 本特性 MUST 为导入导出、审批、权限变化和学业分析提供可审计记录与失败恢复说明。
- **ICR-006**: 本特性 MUST 将学业能力限定为弱提示，除非后续获得经过甲方确认的结构化规则与正式责任边界。

### Modular Technical Decomposition

#### 1. 知识库闭环

- **Knowledge Catalog Component**: 维护政策条目、标准答案、主题分类、搜索索引和受控 AI 匹配依据，支撑学生在提交事务前完成自助查询。 [FR-001][FR-002]
- **Source Governance Component**: 记录知识来源、版本、更新时间、停用状态和人工兜底标记，防止过期内容继续作为权威答复。 [FR-002][FR-003]
- **Template Asset Component**: 管理 Word / Excel 模板文件、适用场景与可下载版本，支撑学生和老师统一材料口径。 [FR-003]

#### 2. 流程闭环

- **Party Workflow Tracker**: 维护学生党团阶段、节点完成情况、下一动作与提醒状态，支持学生自查和组织侧跟踪。 [FR-004][FR-005]
- **Common Request Intake**: 统一受理请假、盖章、证明、报名和材料提交流程，按事项类型约束表单与附件要求。 [FR-006]
- **Theory Self-Test Component**: 管理党团理论题库、自测记录与成绩留存，作为党团事务流程的辅助学习能力。 [FR-005]
- **Risk Boundary Guard**: 对必须走校级正式生效链路的事项显示“仅预检 / 归档 / 跟踪”边界，避免学院平台越权表述。 [FR-006][FR-008]

#### 3. 审批闭环

- **Approval Workbench**: 为老师与业务审批人提供单页审核视图，聚合申请详情、附件、意见、历史状态和待办队列。 [FR-007]
- **Proof Preview Generator**: 在证明申请场景基于标准模板和学生主数据生成 PDF 预览，供学生与审批人查看。 [FR-006][FR-007]
- **Decision State Machine**: 管理通过、驳回、撤回、重提、重批等状态迁移及约束，保证状态一致且可追溯。 [FR-008]
- **Attachment Review Gateway**: 对涉密或不宜线上查看的文件给出线下处理标记和审计记录，避免附件与审批链脱节。 [FR-007][FR-008]

#### 4. 通知闭环

- **Notice Authoring Component**: 维护通知正文、官方来源、标签、发布时间和目标范围，支持学院面向不同学生群体的差异化发布。 [FR-010]
- **Audience Resolution Component**: 根据年级、专业、班级、角色、毕业状态等画像条件确定通知目标人群。 [FR-010][FR-011]
- **Delivery Tracking Component**: 记录站内通知、邮件和短信发送结果、回看状态和批次汇总，形成通知闭环。 [FR-011][FR-016]

#### 5. 审计闭环

- **Role and Field Policy Component**: 管理角色、字段显示策略、导出限制和授权范围，确保敏感数据最小暴露。 [FR-012]
- **Document Audit Component**: 记录审批、配置、知识维护、导出、导入与敏感访问等关键动作，支持学期级追溯。 [FR-013]
- **Offline Exchange Controller**: 管理 Excel / Word / PDF 文件的上传、模板识别、校验、回滚和批次记录。 [FR-009][FR-013]
- **Academic Hint Component**: 基于结构化成绩、培养方案和开课信息生成缺口、风险提示与课程类型级建议，并在数据不足时强制降级为人工核验提示。 [FR-014][FR-015][FR-016]

#### 6. 展示与画像闭环

- **Honor Showcase Component**: 公开展示经官方红头文件或证书确认的校级及以上荣誉，支持类别、学年和历史荣誉筛选。 [FR-017]
- **Honor Governance Component**: 支持荣誉记录批量导入、人工维护、归档、撤销、授权状态、维护人和更新时间留痕。 [FR-017][FR-012][FR-013]
- **Student Growth Profile Component**: 聚合学籍静态字段与科研、竞赛、实践、志愿服务、学生干部任职等动态成长记录，支持授权检索、筛选和画像快照导出。 [FR-018][FR-012]
- **Profile Correction and Privacy Guard**: 为学生端提供本人画像查看和纠错申诉入口，隐藏管理元数据与未授权敏感字段，并禁止自动评分、排名或评价结论输出。 [FR-018][FR-012][FR-013]

### Offline File Exchange Protocol

#### A. 文件分类

- **Excel**: 用于学生主数据、培养方案规则、标签名单、通知目标名单、运营汇总导出。
- **Word**: 用于模板文件、证明草稿模板、标准表单与打印底稿。
- **PDF**: 用于申请附件、证明预览、成绩单上传与归档导出。

#### B. 导入处理总流程

1. **批次登记**：创建 `import_batch` 记录，写入批次号、文件名、文件摘要、上传人、业务类型和模板版本。  
2. **文件落盘**：原始文件写入受控文件存储，文件引用写入批次记录。  
3. **模板识别**：根据模板版本、文件后缀、页签或元数据判断导入类型。  
4. **结构校验**：检查必需 sheet、页眉、列名、行级关键字段、文件大小和编码。  
5. **解析入暂存区**：把每一行或每一条文档解析结果写入 `import_batch_row` 暂存记录。  
6. **业务校验**：检查重复学号、未知年级、非法状态、缺失节点、课程规则冲突、权限越界等问题。  
7. **提交策略**：  
   - 主数据、培养方案、权限配置、通知目标名单采用**整批原子提交**；  
   - 若存在任一 `fatal` 错误，正式表不落库，整批回滚；  
   - 仅当所有 `fatal` 错误清零后，才把暂存结果合并进正式表。  
8. **结果输出**：生成成功数、警告数、失败数、错误明细和可下载错误报告。  
9. **审计留痕**：写入 `document_audit_log`，记录批次、操作者、处理结果和影响对象。  

#### C. Excel 批量导入逻辑

- Excel 必须匹配预定义模板版本；若列头不匹配，批次直接标记为 `FAILED`。
- 每一行在解析后进入暂存区，不直接写正式表。
- 对主数据和规则数据执行“结构校验 + 业务校验 + 权限校验”三级检查。
- 如果同一批次内存在重复主键、非法枚举或关键外键缺失，则整批回滚。
- 如果仅存在非关键警告，例如冗余空列或可忽略备注缺失，则允许继续提交并在结果中提示。

#### D. PDF 导入逻辑

- PDF 成绩单和证明附件分开处理：  
  - **成绩单 PDF**：先解析文本层，再映射到成绩暂存结构；若关键字段缺失或解析置信度不足，
    批次标记为 `REVIEW_REQUIRED`，不得更新学业提示结果；  
  - **申请附件 PDF**：作为业务附件归档，不参与结构化规则写入。  
- PDF 解析失败不会导致已有正式业务数据被部分覆盖。
- 成绩单 PDF 若失败，系统必须输出“需人工核验”的明确结果，而不是写入空白或默认值。

#### E. 导出逻辑

1. 根据角色与字段策略生成可导出的数据视图。
2. 对敏感字段执行隐藏、脱敏或拒绝导出规则。
3. 生成对应模板的 Excel / PDF / Word 输出文件。
4. 记录 `export_job` 与 `document_audit_log`，包含导出人、导出范围、文件摘要、字段脱敏策略和完成状态。

#### F. 回滚与恢复策略

- **批次级回滚**：主数据、流程规则、培养方案规则导入失败时整批回滚。  
- **对象级隔离**：附件归档允许按对象隔离失败，不影响其他已成功归档的附件引用。  
- **恢复依据**：所有正式提交前的解析结果、错误明细和影响对象都保留在批次记录中，用于复盘与重新导入。  
- **禁止部分成功误导**：任何失败批次都不得在界面显示为“已成功同步”。 [FR-009][FR-013][FR-014][FR-015]

### Key Entities *(include if feature involves data)*

> 以下字段类型均采用 Kingbase / KingbaseES 兼容写法；为降低兼容风险，枚举状态优先使用
> `varchar(n)` + 约束策略，而非依赖未验证的数据库扩展类型。

#### Knowledge Loop Tables

- **knowledge_entry**: 存储知识条目主记录。关键字段：`knowledge_id bigserial`、`entry_code varchar(64)`、
  `title varchar(255)`、`category_code varchar(64)`、`content_text text`、`status varchar(32)`、
  `ambiguity_flag boolean`、`source_id bigint`、`published_at timestamp`、`updated_at timestamp`。 [FR-001][FR-002]
- **knowledge_source**: 存储官方来源、链接和版本元数据。关键字段：`source_id bigserial`、
  `source_name varchar(255)`、`source_type varchar(32)`、`official_url varchar(1024)`、
  `version_label varchar(64)`、`effective_date date`、`expired_date date`。 [FR-002]
- **template_asset**: 存储模板文件和适用范围。关键字段：`template_id bigserial`、
  `template_name varchar(255)`、`template_type varchar(32)`、`business_scope varchar(64)`、
  `file_store_key varchar(255)`、`file_hash varchar(128)`、`version_label varchar(64)`、
  `active_flag boolean`。 [FR-003]

#### Workflow Loop Tables

- **party_member_status**: 存储学生当前党团阶段。关键字段：`status_id bigserial`、
  `student_id bigint`、`organization_type varchar(32)`、`current_stage_code varchar(64)`、
  `stage_entered_at timestamp`、`next_due_at timestamp`、`status_note text`。 [FR-004]
- **party_workflow_node**: 存储党团流程节点定义。关键字段：`node_id bigserial`、
  `organization_type varchar(32)`、`node_code varchar(64)`、`node_name varchar(255)`、
  `sequence_no integer`、`due_rule_text text`、`active_flag boolean`。 [FR-005]
- **party_workflow_event**: 存储节点完成与提醒事件。关键字段：`event_id bigserial`、
  `student_id bigint`、`node_id bigint`、`event_type varchar(32)`、`event_status varchar(32)`、
  `occurred_at timestamp`、`operator_id bigint`、`remark text`。 [FR-004][FR-005]
- **reminder_schedule**: 存储待提醒计划。关键字段：`schedule_id bigserial`、
  `target_type varchar(32)`、`target_id bigint`、`trigger_at timestamp`、`channel_code varchar(32)`、
  `delivery_status varchar(32)`、`retry_count smallint`。 [FR-005][FR-011]
- **theory_quiz_question**: 存储理论自测题库。关键字段：`question_id bigserial`、
  `question_bank_code varchar(64)`、`question_type varchar(32)`、`question_text text`、
  `standard_answer text`、`score numeric(5,2)`、`active_flag boolean`。 [FR-005]
- **theory_quiz_record**: 存储学生理论自测结果。关键字段：`record_id bigserial`、
  `student_id bigint`、`question_bank_code varchar(64)`、`total_score numeric(5,2)`、
  `submitted_at timestamp`、`result_payload text`。 [FR-005]

#### Approval Loop Tables

- **common_request**: 存储学生申请主单。关键字段：`request_id bigserial`、
  `request_no varchar(64)`、`request_type varchar(64)`、`student_id bigint`、`current_status varchar(32)`、
  `submission_payload text`、`submitted_at timestamp`、`formal_boundary_flag boolean`、`preview_file_key varchar(255)`。 [FR-006][FR-008]
- **common_request_attachment**: 存储申请附件。关键字段：`attachment_id bigserial`、
  `request_id bigint`、`file_name varchar(255)`、`file_type varchar(32)`、`file_store_key varchar(255)`、
  `file_hash varchar(128)`、`confidential_flag boolean`、`uploaded_at timestamp`。 [FR-006][FR-007]
- **approval_task**: 存储当前审批任务。关键字段：`task_id bigserial`、`request_id bigint`、
  `approver_role varchar(64)`、`approver_id bigint`、`task_status varchar(32)`、
  `assigned_at timestamp`、`due_at timestamp`。 [FR-007]
- **approval_action**: 存储审批动作明细。关键字段：`action_id bigserial`、`request_id bigint`、
  `task_id bigint`、`action_type varchar(32)`、`action_comment text`、`action_at timestamp`、
  `actor_id bigint`。 [FR-007][FR-008]
- **resubmission_snapshot**: 存储驳回 / 撤回后的表单快照。关键字段：`snapshot_id bigserial`、
  `request_id bigint`、`version_no integer`、`snapshot_payload text`、`snapshot_reason varchar(64)`、
  `created_at timestamp`。 [FR-008]

#### Notification Loop Tables

- **notice_message**: 存储通知主记录。关键字段：`notice_id bigserial`、`title varchar(255)`、
  `body_text text`、`source_channel varchar(32)`、`published_at timestamp`、`expires_at timestamp`、
  `created_by bigint`。 [FR-010][FR-011]
- **official_notice_source**: 存储官方通知来源与抓取记录。关键字段：`source_feed_id bigserial`、
  `source_name varchar(255)`、`source_url varchar(1024)`、`capture_mode varchar(32)`、
  `captured_at timestamp`、`status varchar(32)`。 [FR-010]
- **notice_tag_link**: 存储通知与标签关系。关键字段：`link_id bigserial`、`notice_id bigint`、
  `tag_code varchar(64)`、`created_at timestamp`。 [FR-010]
- **notice_target_rule**: 存储目标人群筛选规则。关键字段：`rule_id bigserial`、`notice_id bigint`、
  `grade_code varchar(32)`、`major_code varchar(64)`、`class_code varchar(64)`、
  `role_code varchar(64)`、`graduation_flag boolean`。 [FR-010]
- **notice_delivery**: 存储通知发送与查看结果。关键字段：`delivery_id bigserial`、`notice_id bigint`、
  `student_id bigint`、`channel_code varchar(32)`、`delivery_status varchar(32)`、
  `sent_at timestamp`、`read_at timestamp`。 [FR-011][FR-016]

#### Audit and Governance Tables

- **student_profile**: 存储学院学生主数据。关键字段：`student_id bigserial`、
  `student_no varchar(32)`、`full_name varchar(128)`、`grade_code varchar(32)`、
  `major_code varchar(64)`、`class_code varchar(64)`、`political_status varchar(64)`、
  `contact_mobile_enc bytea`、`id_card_enc bytea`、`discipline_flag boolean`、
  `status_payload text`、`updated_at timestamp`。 [FR-009][FR-012]
- **role_permission_policy**: 存储角色权限策略。关键字段：`policy_id bigserial`、
  `role_code varchar(64)`、`resource_code varchar(64)`、`action_code varchar(64)`、
  `scope_rule text`、`active_flag boolean`。 [FR-012]
- **field_visibility_policy**: 存储字段级展示与导出策略。关键字段：`visibility_id bigserial`、
  `role_code varchar(64)`、`entity_code varchar(64)`、`field_code varchar(64)`、
  `view_mode varchar(32)`、`export_mode varchar(32)`。 [FR-012]
- **document_audit_log**: 存储关键审计事件。关键字段：`audit_id bigserial`、
  `event_type varchar(64)`、`entity_code varchar(64)`、`entity_id bigint`、
  `actor_id bigint`、`actor_role varchar(64)`、`result_code varchar(32)`、
  `event_detail text`、`occurred_at timestamp`。 [FR-013]
- **import_batch**: 存储导入批次头。关键字段：`batch_id bigserial`、`batch_no varchar(64)`、
  `batch_type varchar(64)`、`template_version varchar(64)`、`file_hash varchar(128)`、
  `batch_status varchar(32)`、`uploaded_by bigint`、`uploaded_at timestamp`。 [FR-009][FR-013]
- **import_batch_row**: 存储导入暂存行。关键字段：`row_id bigserial`、`batch_id bigint`、
  `row_no integer`、`raw_payload text`、`validation_level varchar(16)`、
  `validation_message text`、`resolved_flag boolean`。 [FR-009]
- **export_job**: 存储导出任务。关键字段：`export_id bigserial`、`export_type varchar(64)`、
  `scope_text text`、`masking_policy text`、`file_store_key varchar(255)`、
  `export_status varchar(32)`、`requested_by bigint`、`requested_at timestamp`。 [FR-009][FR-013]

#### Display and Profile Tables

- **honor_category**: 存储荣誉类别。关键字段：`category_id bigserial`、`category_code varchar(64)`、
  `category_name varchar(255)`、`level_code varchar(64)`、`display_order integer`、
  `active_flag boolean`。 [FR-017]
- **honor_record**: 存储荣誉公示记录。关键字段：`honor_id bigserial`、`honor_name varchar(255)`、
  `honor_level varchar(64)`、`category_id bigint`、`awardee_type varchar(32)`、
  `student_id bigint`、`team_name varchar(255)`、`awarding_unit varchar(255)`、
  `document_no varchar(128)`、`certificate_no varchar(128)`、`public_date date`、
  `effective_until date`、`story_summary text`、`award_statement text`、`status varchar(32)`、
  `is_historical boolean`、`history_reason text`、`consent_flag boolean`、`created_by bigint`、
  `updated_by bigint`、`updated_at timestamp`。 [FR-017][FR-012][FR-013]
- **student_profile_extension**: 存储学生画像扩展字段。关键字段：`extension_id bigserial`、
  `student_id bigint`、`dimension_code varchar(64)`、`title varchar(255)`、`description text`、
  `source_type varchar(64)`、`source_name varchar(255)`、`entered_by bigint`、
  `last_updated_at timestamp`、`review_status varchar(32)`、`sensitive_flag boolean`。 [FR-018][FR-012]
- **profile_correction_request**: 存储学生画像纠错申诉。关键字段：`correction_id bigserial`、
  `student_id bigint`、`target_field varchar(128)`、`request_reason text`、
  `request_status varchar(32)`、`submitted_at timestamp`、`handled_by bigint`、
  `handled_at timestamp`、`handle_comment text`。 [FR-018][FR-013]

#### Academic Hint Tables

- **curriculum_rule_set**: 存储培养方案规则头。关键字段：`rule_set_id bigserial`、
  `grade_code varchar(32)`、`major_code varchar(64)`、`version_label varchar(64)`、
  `effective_year smallint`、`active_flag boolean`。 [FR-015]
- **curriculum_module_rule**: 存储培养方案模块规则。关键字段：`module_rule_id bigserial`、
  `rule_set_id bigint`、`module_code varchar(64)`、`module_name varchar(255)`、
  `required_credit numeric(6,2)`、`elective_flag boolean`。 [FR-015]
- **course_equivalence_rule**: 存储课程替代或等价关系。关键字段：`equivalence_id bigserial`、
  `rule_set_id bigint`、`source_course_code varchar(64)`、`target_course_code varchar(64)`、
  `rule_type varchar(32)`、`remark text`。 [FR-015]
- **term_course_offering**: 存储学期开课信息。关键字段：`offering_id bigserial`、
  `term_code varchar(32)`、`course_code varchar(64)`、`course_name varchar(255)`、
  `course_type varchar(64)`、`grade_scope varchar(64)`、`major_scope varchar(128)`。 [FR-015]
- **academic_gap_result**: 存储学生学业分析结果。关键字段：`gap_result_id bigserial`、
  `student_id bigint`、`rule_set_id bigint`、`result_status varchar(32)`、
  `missing_credit numeric(6,2)`、`risk_summary text`、`recommendation_text text`、`manual_review_required boolean`、
  `generated_at timestamp`。 [FR-014][FR-016]

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 90% 的学生能够在 2 分钟内定位到目标政策、模板或办理说明，并确认下一步动作。
- **SC-002**: 80% 以上的学院高频事务能够通过统一入口完成提交、审核、驳回 / 重提和状态查询闭环。
- **SC-003**: 100% 的关键审批、导入导出、权限变化和知识发布操作都能被追溯到操作者、时间和对象。
- **SC-004**: 结构化 Excel 主数据导入的失败批次不会对正式数据造成部分污染，错误报告可在一次导入结束后立即获取。
- **SC-005**: 95% 的通知批次能够明确展示目标范围和投递结果，学生可在统一入口查看与本人相关的通知。
- **SC-006**: 学业分析页面 100% 显示“仅供风险提示”边界文案，且在数据不足时不会输出最终资格结论。
- **SC-007**: 90% 的标准证明申请可基于模板自动生成 PDF 预览，并在审批链中保持同一份预览引用。
- **SC-008**: 当学期开课信息可用时，100% 的选课建议仅输出课程类型级推荐，不输出动态选课人数或毕业资格结论。
- **SC-009**: 荣誉榜单能够按类别和学年准确筛选，随机抽检 10 条正式荣誉均能展示授予单位、文号或证书编号、公示日期和事迹摘要，且历史或撤销荣誉不会被默认主动推送。
- **SC-010**: 学生画像能够按权限聚合静态学籍字段与动态成长字段；学生本人仅可查看本人画像并可提交纠错申诉，未授权角色无法查看高敏字段、管理元数据或画像导出内容。

## Assumptions

- 学生端可能同时存在小程序与 Web，但二者共享同一后端业务边界和权限规则。
- 当前阶段不假设存在可调用的校级 API，所有跨系统数据交换默认依赖受控的 Excel / Word / PDF 文件流转。
- Kingbase 是唯一受支持的生产数据库，设计中所有表结构和查询都必须以其兼容性为前提。
- 敏感字段默认受限，未经甲方明确授权不开放明文展示或原始导出。
- 学业模块默认处于弱提示模式；当培养方案、成绩数据和替代规则均结构化可用时生成完整分析结果，否则必须展示数据不足提示、保留规则维护入口，并允许使用甲方确认的样例数据完成演示与验收。
- 荣誉展示仅覆盖经官方文件、证书或学院审核确认的正式荣誉；口头表扬、临时奖励或非官方评选结果不进入默认公示范围。
- 学生画像仅作为信息聚合与展示工具，不作为综合素质自动评价、排名或奖惩决策依据。
