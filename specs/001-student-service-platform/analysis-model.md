# Analysis Model

**Feature**: `specs/001-student-service-platform/spec.md`  
**Created**: 2026-04-13  
**Updated**: 2026-04-15  
**Purpose**: 为传统软件需求规格说明书补充七模块核心业务分析类图与新增模块代表性时序图

## 1. 核心业务分析类图

```mermaid
%%{
  init: {
    "theme": "base",
    "themeVariables": {
      "fontFamily": "Times New Roman, SimSun, serif",
      "primaryColor": "#ffffff",
      "primaryBorderColor": "#000000",
      "primaryTextColor": "#000000",
      "lineColor": "#000000",
      "clusterBkg": "#f0f0f0",
      "clusterBorder": "#7f8c8d",
      "fontSize": "16px",
      "lineWidth": "2px"
    }
  }
}%%
classDiagram
    direction TB

    class StudentProfile {
        +student_id
        +student_no
        +grade_code
        +major_code
    }

    class KnowledgeSource {
        +source_id
        +source_name
        +version_label
    }

    class KnowledgeEntry {
        +knowledge_id
        +title
        +status
    }

    class TemplateAsset {
        +template_id
        +template_name
        +template_type
    }

    class PartyMemberStatus {
        +status_id
        +current_stage_code
        +next_due_at
    }

    class PartyWorkflowEvent {
        +event_id
        +event_type
        +event_status
    }

    class CommonRequest {
        +request_id
        +request_type
        +current_status
        +formal_boundary_flag
    }

    class CommonRequestAttachment {
        +attachment_id
        +file_name
        +confidential_flag
    }

    class ApprovalTask {
        +task_id
        +approver_role
        +task_status
    }

    class ApprovalAction {
        +action_id
        +action_type
        +action_at
    }

    class NoticeMessage {
        +notice_id
        +title
        +published_at
    }

    class NoticeDelivery {
        +delivery_id
        +channel_code
        +delivery_status
    }

    class ImportBatch {
        +batch_id
        +batch_type
        +batch_status
    }

    class CurriculumRuleSet {
        +rule_set_id
        +major_code
        +version_label
    }

    class TermCourseOffering {
        +offering_id
        +term_code
        +course_type
    }

    class AcademicGapResult {
        +gap_result_id
        +result_status
        +missing_credit
        +manual_review_required
    }

    class DocumentAuditLog {
        +audit_id
        +event_type
        +result_code
    }

    KnowledgeSource "1" --> "0..*" KnowledgeEntry : governs
    KnowledgeEntry "0..*" --> "0..*" TemplateAsset : references

    StudentProfile "1" --> "0..1" PartyMemberStatus : current_stage
    PartyMemberStatus "1" --> "0..*" PartyWorkflowEvent : timeline

    StudentProfile "1" --> "0..*" CommonRequest : submits
    CommonRequest "1" *-- "0..*" CommonRequestAttachment : contains
    CommonRequest "1" *-- "0..*" ApprovalTask : creates
    ApprovalTask "1" *-- "0..*" ApprovalAction : records

    NoticeMessage "1" o-- "0..*" NoticeDelivery : delivers
    StudentProfile "1" --> "0..*" NoticeDelivery : receives

    CurriculumRuleSet "1" o-- "0..*" AcademicGapResult : generates
    TermCourseOffering "0..*" --> "0..*" AcademicGapResult : supports
    StudentProfile "1" --> "0..*" AcademicGapResult : owns

    KnowledgeEntry "1" --> "0..*" DocumentAuditLog : audited_by
    CommonRequest "1" --> "0..*" DocumentAuditLog : audited_by
    ApprovalAction "1" --> "0..*" DocumentAuditLog : audited_by
    NoticeMessage "1" --> "0..*" DocumentAuditLog : audited_by
    ImportBatch "1" --> "0..*" DocumentAuditLog : audited_by
    AcademicGapResult "1" --> "0..*" DocumentAuditLog : audited_by
```

## 2. 奖励荣誉与学生画像扩展类图

```mermaid
%%{
  init: {
    "theme": "base",
    "themeVariables": {
      "fontFamily": "Times New Roman, SimSun, serif",
      "primaryColor": "#ffffff",
      "primaryBorderColor": "#000000",
      "primaryTextColor": "#000000",
      "lineColor": "#000000",
      "clusterBkg": "#f0f0f0",
      "clusterBorder": "#7f8c8d",
      "fontSize": "16px",
      "lineWidth": "2px"
    }
  }
}%%
classDiagram
    direction TB

    class StudentProfile {
        +student_id
        +student_no
        +full_name
        +major_code
        +grade_code
    }

    class HonorCategory {
        +category_id
        +category_name
    }

    class HonorDisplayConfig {
        +config_id
        +display_scope
        +history_visible_flag
    }

    class HonorRecord {
        +honor_id
        +honor_name
        +display_subject_name
        +recipient_scope
        +award_unit
        +document_ref
        +publicity_date
        +authorization_status
        +review_status
        +identity_verified_flag
        +story_summary
        +testimonial
        +display_until
        +display_status
    }

    class StudentProfileExtension {
        +extension_id
        +volunteer_service_hours
        +cadre_position_summary
        +data_source
        +entered_by
        +updated_at
    }

    class ResearchExperience {
        +research_id
        +project_name
        +data_source
        +entered_by
        +updated_at
    }

    class CompetitionAward {
        +award_id
        +award_name
        +award_level
        +data_source
        +entered_by
        +updated_at
    }

    class SocialPractice {
        +practice_id
        +practice_name
        +practice_period
        +data_source
        +entered_by
        +updated_at
    }

    class ImportBatch {
        +batch_id
        +batch_type
        +batch_status
    }

    class DocumentAuditLog {
        +audit_id
        +event_type
        +result_code
    }

    StudentProfile "0..*" <-- "0..*" HonorRecord : individual_or_collective_members
    HonorCategory "1" --> "0..*" HonorRecord : classifies
    HonorDisplayConfig "1" --> "0..*" HonorRecord : governs
    ImportBatch "1" --> "0..*" HonorRecord : imports_and_verifies

    StudentProfile "1" o-- "0..1" StudentProfileExtension : extends
    StudentProfileExtension "1" *-- "0..*" ResearchExperience : research_records
    StudentProfileExtension "1" *-- "0..*" CompetitionAward : competition_records
    StudentProfileExtension "1" *-- "0..*" SocialPractice : practice_records

    HonorRecord "1" --> "0..*" DocumentAuditLog : audited_by
    StudentProfileExtension "1" --> "0..*" DocumentAuditLog : audited_by
```

## 3. 时序图：浏览荣誉榜单并查看榜样事迹

```mermaid
%%{
  init: {
    "theme": "base",
    "themeVariables": {
      "fontFamily": "Times New Roman, SimSun, serif",
      "primaryColor": "#ffffff",
      "primaryBorderColor": "#000000",
      "primaryTextColor": "#000000",
      "lineColor": "#000000",
      "clusterBkg": "#f0f0f0",
      "clusterBorder": "#7f8c8d",
      "fontSize": "16px",
      "lineWidth": "2px"
    }
  }
}%%
sequenceDiagram
    autonumber
    actor Student as 学生
    participant StudentApp as 学生端
    participant HonorService as 荣誉展示服务
    participant HonorRepo as 荣誉记录库
    participant ProfileRepo as 学籍信息
    participant VisitLog as 访问日志/热度统计

    rect rgb(245,245,245)
        Student->>StudentApp: 进入荣誉展示模块首页
        StudentApp->>HonorService: 请求荣誉榜单(category, year)
        HonorService->>HonorRepo: 查询已授权、已审核、已核验的有效荣誉与历史标记
        HonorRepo-->>HonorService: 返回荣誉条目
        HonorService->>ProfileRepo: 读取获奖者或集体展示主体
        ProfileRepo-->>HonorService: 返回姓名 / 集体名称、专业、年级等公开字段
        HonorService-->>StudentApp: 返回榜单与筛选结果
        StudentApp-->>Student: 展示荣誉卡片
    end

    rect rgb(250,250,250)
        Student->>StudentApp: 点击荣誉条目
        StudentApp->>HonorService: 请求荣誉详情
        HonorService->>HonorRepo: 加载详情、展示有效期与归档状态
        alt 荣誉已过期或归档
            HonorRepo-->>HonorService: 标记为历史荣誉
            HonorService-->>StudentApp: 返回详情并标注“历史荣誉”
        else 当前有效荣誉
            HonorRepo-->>HonorService: 返回正式荣誉详情、事迹摘要与获奖感言
            alt 集体荣誉
                HonorService-->>StudentApp: 返回集体名称与公开展示字段
            else 个人荣誉
                alt 获奖者已毕业
                    HonorService-->>StudentApp: 返回详情并隐藏联系方式
                else 在读学生
                    HonorService-->>StudentApp: 返回公开展示字段
                end
            end
        end
        HonorService->>VisitLog: 记录访问行为
        VisitLog-->>HonorService: 记录完成
        StudentApp-->>Student: 展示榜样事迹详情
    end
```

## 4. 时序图：查看学生画像与提交纠错 / 成长补录申请

```mermaid
%%{
  init: {
    "theme": "base",
    "themeVariables": {
      "fontFamily": "Times New Roman, SimSun, serif",
      "primaryColor": "#ffffff",
      "primaryBorderColor": "#000000",
      "primaryTextColor": "#000000",
      "lineColor": "#000000",
      "clusterBkg": "#f0f0f0",
      "clusterBorder": "#7f8c8d",
      "fontSize": "16px",
      "lineWidth": "2px"
    }
  }
}%%
sequenceDiagram
    autonumber
    actor Advisor as 辅导员
    actor Student as 学生
    participant ManagePortal as 管理端
    participant StudentApp as 学生端
    participant ProfileService as 学生画像服务
    participant ProfileRepo as 学籍与画像数据
    participant UpdateService as 纠错 / 补录服务
    participant AuditLog as 审计日志

    rect rgb(245,245,245)
        Advisor->>ManagePortal: 搜索并进入目标学生画像页
        ManagePortal->>ProfileService: 请求学生画像详情
        ProfileService->>ProfileRepo: 聚合学籍静态字段与带来源留痕的动态成长字段
        alt 越权查看非管辖学生
            ProfileService->>AuditLog: 记录越权尝试
            AuditLog-->>ProfileService: 留痕完成
            ProfileService-->>ManagePortal: 拒绝访问
            ManagePortal-->>Advisor: 展示无权限提示
        else 权限校验通过
            ProfileService->>AuditLog: 记录查看行为
            AuditLog-->>ProfileService: 留痕完成
            ProfileService-->>ManagePortal: 返回全景画像与脱敏字段
            ManagePortal-->>Advisor: 展示画像与导出入口
        end
    end

    rect rgb(250,250,250)
        Student->>StudentApp: 查看本人画像
        StudentApp->>ProfileService: 请求本人画像
        ProfileService->>ProfileRepo: 读取本人静态字段与动态记录
        ProfileService-->>StudentApp: 返回本人画像并隐藏管理元数据
        StudentApp-->>Student: 展示画像、纠错申诉与成长补录入口
        Student->>StudentApp: 提交信息纠错或成长补录申请
        StudentApp->>UpdateService: 提交申诉说明或补录内容
        UpdateService->>ProfileRepo: 保存待审核申请与来源信息
        ProfileRepo-->>UpdateService: 保存成功
        UpdateService->>AuditLog: 记录申请提交
        AuditLog-->>UpdateService: 留痕完成
        UpdateService-->>StudentApp: 返回提交成功
        StudentApp-->>Student: 提示已提交至辅导员审核
    end
```

## 5. 模型说明

- 本次将分析模型拆分为“核心业务分析类图”和“奖励荣誉与学生画像扩展类图”，避免单图横向过宽导致 Word 中不可读。
- `HonorRecord / HonorCategory / HonorDisplayConfig` 仅表达正式荣誉、个人/集体展示主体、授权审核、学籍核验、归档与展示边界，不扩展到文档未定义的评分或推荐逻辑。
- `StudentProfileExtension / ResearchExperience / CompetitionAward / SocialPractice` 仅表达成长数据聚合、来源留痕、学生补录后审核入库和权限展示，不表达自动评分、排名或评价结论。
- 原有知识问答、党团流程、通知推送、电子证明审批和学业分析的动态图继续沿用现有图稿；本文件补充一张扩展类图和两张新增模块代表性时序图以完成七模块覆盖。
