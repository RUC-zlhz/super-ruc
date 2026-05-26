"""将“党团平台文件 2”整理为可检索知识条目并直接发布。

该脚本不并入基础 `seed_initial.py`，避免改变仓库默认“知识正文为空”的基线；
需要时由开发/老师显式执行，以把当前 4 份 PDF 中的常见问答导入知识库。
"""
from __future__ import annotations

import asyncio
import logging
import sys
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import build_audit_detail, log_action
from app.auth.models import User
from app.core.database import AsyncSessionLocal
from app.knowledge import repository as repo
from app.knowledge.models import (
    ENTRY_STATUS_PUBLISHED,
    KnowledgeEntry,
    KnowledgeSource,
    REVISION_PUBLISH,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("import-party-platform-file2-knowledge")


@dataclass(frozen=True)
class SourceSeed:
    key: str
    source_name: str
    issuing_org: str
    version_label: str
    source_url: str | None = None
    is_official: bool = False


@dataclass(frozen=True)
class EntrySeed:
    slug: str
    title: str
    summary: str
    category_code: str
    source_key: str
    tags: tuple[str, ...]
    body_md: str
    applicable_condition: str | None = None
    required_materials: str | None = None
    process_steps: str | None = None
    manual_consult_hint: str | None = None
    ambiguity_flag: bool = False
    version_label: str | None = None


def _faq_body(source_file: str, questions: tuple[str, ...], answers: tuple[str, ...], note: str | None = None) -> str:
    lines = [f"来源文件：《{source_file}》", ""]
    if questions:
        lines.append("常见问法：")
        lines.extend(f"- {question}" for question in questions)
        lines.append("")
    lines.append("标准答复：")
    lines.extend(f"{idx}. {answer}" for idx, answer in enumerate(answers, 1))
    if note:
        lines.extend(["", f"补充说明：{note}"])
    return "\n".join(lines)


_SOURCES: tuple[SourceSeed, ...] = (
    SourceSeed(
        key="scholarship_2025",
        source_name="【正式】中国人民大学信息学院2025年综合类.pdf",
        issuing_org="中国人民大学信息学院",
        version_label="2025年综合类奖学金评审方案",
    ),
    SourceSeed(
        key="leave_guide",
        source_name="学生线上办理教学活动请假手续指南.pdf",
        issuing_org="中国人民大学",
        version_label="教学活动请假指南",
    ),
    SourceSeed(
        key="curriculum_2025",
        source_name="1 2025级 大类培养方案.pdf",
        issuing_org="中国人民大学教务处",
        version_label="2025级本科生培养方案",
    ),
    SourceSeed(
        key="curriculum_2024",
        source_name="【1】2024级大类培养方案（含辅修）.pdf",
        issuing_org="中国人民大学教务处",
        version_label="2024级本科生培养方案（含辅修）",
    ),
    SourceSeed(
        key="curriculum_compare_2024_2025",
        source_name="1 2025级 大类培养方案.pdf / 【1】2024级大类培养方案（含辅修）.pdf",
        issuing_org="中国人民大学教务处",
        version_label="2024-2025培养方案对照",
    ),
)


_ENTRIES: tuple[EntrySeed, ...] = (
    EntrySeed(
        slug="info-scholarship-2025-amounts",
        title="2025年信息学院综合类奖学金有哪些、金额是多少",
        summary=(
            "2025年信息学院综合类奖学金包括国家奖学金、国家励志奖学金、研究生国家奖学金和宝钢/京东特等奖学金/"
            "燕宝/比亚迪/京东·求是未来学者等。金额分别为：本科国家奖学金10000元、国家励志奖学金6000元、"
            "硕士国家奖学金20000元、博士国家奖学金30000元；多数捐赠类奖学金10000元，比亚迪研究生20000元。"
        ),
        category_code="SCHOLARSHIP",
        source_key="scholarship_2025",
        tags=(
            "奖学金",
            "国家奖学金",
            "国家励志奖学金",
            "研究生国家奖学金",
            "比亚迪奖学金",
            "燕宝奖学金",
            "京东特等奖学金",
            "宝钢优秀学生奖",
            "京东求是未来学者",
            "金额",
            "名额",
        ),
        body_md=_faq_body(
            "【正式】中国人民大学信息学院2025年综合类.pdf",
            (
                "国家奖学金多少钱",
                "国家励志奖学金多少钱",
                "研究生国家奖学金多少钱",
                "信息学院2025年有哪些综合类奖学金",
                "比亚迪奖学金和燕宝奖学金金额是多少",
            ),
            (
                "2025年信息学院综合类奖学金包含国家奖学金和捐赠类奖学金两大类。",
                "本科生国家奖学金奖励标准为10000元/人，国家励志奖学金奖励标准为6000元/人。",
                "硕士研究生国家奖学金奖励标准为20000元/人，博士研究生国家奖学金奖励标准为30000元/人。",
                "宝钢优秀学生奖、京东特等奖学金、燕宝奖学金和“京东·求是未来学者”学生科研创新奖学金均为10000元/人；比亚迪奖学金为本科生10000元/人、研究生20000元/人。",
                "附件名额表显示：本科国家奖学金10个、本科国家励志奖学金18个、硕士国家奖学金7个、博士国家奖学金7个；比亚迪奖学金本科1个、硕士2个、博士2个，燕宝1个，京东·求是未来学者1个。",
            ),
            note="综合类各项奖学金不可兼得，综合类和智育类奖学金也不可兼得。",
        ),
        manual_consult_hint="奖项金额和名额以当年学院正式评审方案为准，如文件更新请以最新通知为准。",
        version_label="2025奖学金",
    ),
    EntrySeed(
        slug="info-scholarship-2025-eligibility",
        title="2025年信息学院综合类奖学金参评对象和基本条件",
        summary=(
            "参评对象应为二年级及以上、具有我校学籍的全日制非定向学生。港澳台学生、国际学生、来校交流交换学生不在范围内。"
            "延期毕业学生原则上不在范围内，但因公派出国、挂职锻炼、参军入伍、西部支教等原因延期者，在延长学习期内有正常参评机会。"
            "基础条件包括热爱祖国、遵守校纪校规、上一学年未受处分和通报批评、诚实守信。"
        ),
        category_code="SCHOLARSHIP",
        source_key="scholarship_2025",
        tags=(
            "参评对象",
            "谁能报",
            "二年级及以上",
            "全日制非定向",
            "港澳台学生",
            "国际学生",
            "交流交换学生",
            "延期毕业",
            "基础条件",
        ),
        body_md=_faq_body(
            "【正式】中国人民大学信息学院2025年综合类.pdf",
            (
                "哪些学生能报综合类奖学金",
                "大一能不能报",
                "港澳台学生和国际学生能不能报",
                "延期毕业还能不能报",
                "参评的基础条件是什么",
            ),
            (
                "参评对象应为二年级及以上、具有我校学籍的全日制非定向学生。",
                "港澳台学生、国际学生、来校交流交换学生不在此类参评范围内。",
                "延期毕业学生原则上不在范围内；但因公派出国、挂职锻炼、参军入伍、西部支教等原因延期的学生，在延长学习期内有正常参评机会。",
                "基础条件包括热爱祖国、拥护中国共产党的领导，遵守宪法和法律，遵守学校规章制度，上一学年未受过违纪处分和通报批评处理。",
                "参评学生还应诚实守信、道德品质优良，并在德智体美劳等方面全面发展，或在学习学术、实践创新、社会服务等方面表现特别突出。",
            ),
        ),
        manual_consult_hint="涉及身份类别、延期原因或上一学年纪律处分认定等特殊情形时，请联系学院老师确认。",
        version_label="2025奖学金",
    ),
    EntrySeed(
        slug="info-scholarship-2025-undergraduate-rules",
        title="2025年本科国家奖学金和国家励志奖学金怎么评",
        summary=(
            "本科国家奖学金要求上一学年学习成绩排名和综合测评成绩排名均位于本专业前10%；如有特别突出表现，可放宽到前30%。"
            "有出国（境）学习经历者，所修学分量须达到培养方案该学年应修学分量的80%。"
            "国家励志奖学金要求上一学年属于学校认定的家庭经济困难学生。"
        ),
        category_code="SCHOLARSHIP",
        source_key="scholarship_2025",
        tags=(
            "本科国家奖学金",
            "国家励志奖学金",
            "前10%",
            "前30%",
            "综测",
            "家庭经济困难",
            "出国学分80%",
            "放宽条件",
        ),
        body_md=_faq_body(
            "【正式】中国人民大学信息学院2025年综合类.pdf",
            (
                "本科国家奖学金要前几名",
                "有突出成果能不能放宽到前30%",
                "国家励志奖学金怎么认定",
                "出国交换后奖学金成绩怎么要求",
            ),
            (
                "本科生国家奖学金要求上一学年学习成绩排名与综合测评成绩排名均位于本专业前10%。",
                "如果在精神文明、学术研究、学科竞赛、创新发明、体育竞赛、重要文艺比赛、全国性荣誉称号等方面有特别优秀表现，经学院和学校评审同意，可放宽至本专业前30%。",
                "上一学年有出国（境）学习经历的，所修学分量（含在校获得学分和经学校认定转换后的学分）须达到其培养方案该学年应修学分量的80%。",
                "国家励志奖学金要求参评学生上一学年应属于学校认定的家庭经济困难学生。",
            ),
            note="研究生国家奖学金原则上学术型更看重科研，专业型综合考虑学习、科研、实践等情况。",
        ),
        manual_consult_hint="放宽条件、出国学分换算和家庭经济困难认定口径均以当年学院审核结果为准。",
        version_label="2025奖学金",
    ),
    EntrySeed(
        slug="info-scholarship-2025-process-materials",
        title="2025年信息学院综合类奖学金报名时间、材料和答辩安排",
        summary=(
            "综合类奖学金报名截止到2025年9月21日24:00，材料提交邮箱为hh20240101@ruc.edu.cn。"
            "学院先进行材料初筛，预计9月24日左右组织答辩。通过初审者需提前准备PPT和发言稿，展示约5分钟、答辩3分钟。"
        ),
        category_code="SCHOLARSHIP",
        source_key="scholarship_2025",
        tags=(
            "报名时间",
            "申请时间",
            "材料",
            "邮箱",
            "答辩",
            "初筛",
            "PPT",
            "奖学金申请",
        ),
        required_materials=(
            "本科生提交上一学年学习成绩排名与综测排名（或低年级提交学习成绩排名）、上一学年成绩单、"
            "2024-09-11至2025-09-10期间正式发表/出版的学术科研成果；有出国（境）学习经历者还需提交80%学分说明。"
            "研究生提交自评表、上一学年成绩单、论文全文、专利、实习实践证明和其他突出成果。"
        ),
        process_steps=(
            "1. 2025-09-21 24:00前将材料发送至hh20240101@ruc.edu.cn；"
            "2. 学院组织初筛；3. 预计9月24日左右参加答辩；"
            "4. 学院按推荐次序和资格复核结果确定推荐；5. 公示无异议后上报学校。"
        ),
        body_md=_faq_body(
            "【正式】中国人民大学信息学院2025年综合类.pdf",
            (
                "奖学金什么时候截止报名",
                "奖学金材料发到哪里",
                "本科生要交哪些材料",
                "研究生要交哪些材料",
                "答辩怎么安排",
            ),
            (
                "报名截止时间是2025年9月21日（周日）24:00，参评材料发送到邮箱hh20240101@ruc.edu.cn。",
                "学院会先组织专人审查材料，视规定条件对候选人进行筛选，再确定入选名单。",
                "本科生初筛材料包括上一学年学习成绩排名与综测排名、成绩单、规定时间范围内正式发表或出版的成果；如有出国（境）学习经历，还需提交达到80%学分量的说明。",
                "研究生初筛材料包括《中国人民大学信息学院优秀研究生论坛论文情况自评表》、成绩单、论文全文、专利、实习实践证明和其他成果；已获过研究生国家奖学金者，需提交上次获评后的成果，且不可重复使用已参评成果。",
                "预计9月24日左右组织答辩。通过初审者需准备PPT、发言稿等材料，展示时间约5分钟，答辩约3分钟。国家励志奖学金不参与展评，入选同学按学分绩排序推荐。",
            ),
            note="综合类奖学金设置候补1名，同推荐名单一起上报评审工作委员会审核。",
        ),
        manual_consult_hint="材料口径、成果作者顺序和论文类型认定较细，提交前建议对照原通知再核对一遍。",
        version_label="2025奖学金",
    ),
    EntrySeed(
        slug="teaching-leave-approval-rules",
        title="教学活动请假审批规则：病假、事假分别怎么批",
        summary=(
            "学生因病或其他原因不能参加教育教学计划规定的活动时，须事先申请并获批准，否则按旷课处理。"
            "病假3日（含）以内本科生由班主任或专职辅导员审批、研究生由导师或专职辅导员审批；病假超过3日由学院（系）主管领导审批。"
            "事假1日（含）以内由班主任/辅导员或导师/辅导员审批，1日以上1周（含）以内由学院（系）主管领导审批，1周以上本科生还需教务处审批、研究生还需研究生院审批，国际学生还需国际合作与交流处审批。"
        ),
        category_code="LEAVE",
        source_key="leave_guide",
        tags=(
            "请假规则",
            "病假",
            "事假",
            "谁审批",
            "三日以内",
            "一周以上",
            "国际学生",
            "诊断证明",
            "旷课",
            "补办",
        ),
        applicable_condition="学生因病或其他原因不能参加教育教学计划规定的活动时，须事先申请并获批准。",
        required_materials="病假须持校医院或二级甲等以上医院诊断证明。",
        body_md=_faq_body(
            "学生线上办理教学活动请假手续指南.pdf",
            (
                "病假三天以内谁审批",
                "病假超过三天谁审批",
                "事假一周以上谁审批",
                "国际学生请假多一层审批吗",
                "没请假会不会算旷课",
                "突发急病能不能补办",
            ),
            (
                "学生因病或其他原因不能参加教育教学计划规定的活动时，须事先提出请假申请并获得批准，否则按旷课处理。",
                "病假3日（含）以内，本科生由班主任或专职辅导员审批，研究生由导师或专职辅导员审批；病假超过3日，须经学院（系）主管领导审批。",
                "事假一般不得请；如确有特殊情况，1日（含）以内由班主任/专职辅导员或导师/专职辅导员审批，1日以上1周（含）以内须学院（系）主管领导审批。",
                "事假1周以上的，学院（系）审批后，研究生还需研究生院审批，本科生还需教务处审批，国际学生还须经国际合作与交流处审批。",
                "如遇突发急病等不可抗力特殊情况，不能事前请假的，应及时持相关证明补办请假手续。",
            ),
        ),
        manual_consult_hint="涉及离京离校、国际学生或突发急病补办等特殊情形时，建议同步联系学院老师确认。",
        version_label="请假指南",
    ),
    EntrySeed(
        slug="teaching-leave-online-process",
        title="教学活动请假线上怎么办理、在哪填、怎么销假",
        summary=(
            "手机端可在微信通讯录进入“中国人民大学”→“综合服务中心网上办事大厅”；电脑端可在“微人大”→“校务”中搜索“综合服务中心网上办事大厅”。"
            "在办事大厅搜索“请假”，选择“学生教学活动请假”并立即申请，按要求填写时间、课程、原因、离京离校信息和第一级审批人职工号后正式提交。"
            "请假涉及离京离校的，返校后需回到原请假表单办理销假登记。"
        ),
        category_code="LEAVE",
        source_key="leave_guide",
        tags=(
            "请假流程",
            "请假怎么请",
            "网上办事大厅",
            "微人大",
            "学生教学活动请假",
            "销假",
            "离京离校",
            "第一级审批人",
            "企业微信推送",
        ),
        process_steps=(
            "1. 进入综合服务中心网上办事大厅；2. 搜索“请假”并选择“学生教学活动请假”；"
            "3. 立即申请并确认请假须知；4. 核对个人信息、填写手机号、请假时间和课程；"
            "5. 选择因事/因病、填写原因或上传附件；6. 填写离京离校信息和第一级审批人职工号后正式提交；"
            "7. 在“我的申请”查看进度；8. 审批通过后打印表单交任课教师备案；9. 返校后在原表单销假。"
        ),
        body_md=_faq_body(
            "学生线上办理教学活动请假手续指南.pdf",
            (
                "请假在哪个系统里办",
                "微人大怎么找请假入口",
                "请假表怎么填",
                "审批进度在哪看",
                "批完之后还要做什么",
                "返校后怎么销假",
            ),
            (
                "手机端入口是微信通讯录中的“中国人民大学”→“综合服务中心网上办事大厅”；电脑端入口是“微人大”→“校务”→搜索“综合服务中心网上办事大厅”。",
                "在办事大厅首页搜索栏输入“请假”，选择“学生教学活动请假”，点击“立即申请”，阅读请假须知后选择“我已确认，继续填写”。",
                "表单中需核对个人信息、填写手机号、选择连续的请假时间并勾选请假课程；再选择因事或因病，填写原因或上传附件。",
                "如有离京或离校2日以上情况，还需填写离京离校信息；第一级审批人栏需要填写签批人职工号，本科生优先班主任，研究生优先导师。",
                "提交后流程会按班主任或导师→学院（书院）主管领导→国际合作与交流处（仅国际学生）→教务处/研究生院依次审批，审批进度可在“我的申请”查看。",
                "审批通过后，请假信息会通过“中国人民大学”企业微信推送；学生需打印表单交任课教师备案。涉及离京离校的，返校后要回到原表单完成销假登记，销假信息同样会通过企业微信推送。",
            ),
        ),
        manual_consult_hint="请假类事项仍应以学校正式系统和学院老师通知为准，尤其是离京离校和销假环节。",
        version_label="请假指南",
    ),
    EntrySeed(
        slug="info-school-2025-curriculum-overview",
        title="2025级信息学院大类培养方案总览",
        summary=(
            "2025级信息学院位于理工学科大类，包含计算机科学与技术、信息管理与信息系统、信息安全、数据科学与大数据技术4个专业。"
            "2025级本科培养方案总体分为立本模块、专业模块、卓越模块。立本模块包括思想政治理论课、基础技能"
            "（含公共外语、公共数学、人工智能与数据技术平台课）和素质教育；专业模块包括部类核心课、专业核心课、专业选修课；"
            "卓越模块包括研究训练、专业特色创新训练、专业实习、毕业论文（设计）、国际性学习课程和公共选修课。"
        ),
        category_code="ACADEMIC",
        source_key="curriculum_compare_2024_2025",
        tags=(
            "2025级",
            "2025培养方案",
            "信息学院专业",
            "理工学科大类",
            "立本模块",
            "专业模块",
            "卓越模块",
            "人工智能与数据技术平台课",
            "信息学院",
        ),
        body_md=_faq_body(
            "1 2025级 大类培养方案.pdf",
            (
                "2025级信息学院有哪些专业",
                "2025培养方案分几个模块",
                "立本模块是什么",
                "卓越模块是什么",
                "人工智能与数据技术基础是不是平台课",
            ),
            (
                "2025级理工学科大类中的信息学院专业包括计算机科学与技术、信息管理与信息系统、信息安全、数据科学与大数据技术。",
                "2025级本科培养方案总体分为三大模块：立本模块、专业模块、卓越模块。",
                "立本模块包括思想政治理论课，基础技能（公共外语课、公共数学课、人工智能与数据技术平台课），以及新生引导课、科学与人文素养课、公共体育课、美育课程、劳动教育、心理健康教育、职业生涯教育、军事课、志愿服务等素质教育内容。",
                "专业模块包括部类核心课、专业核心课和专业选修课；卓越模块包括研究训练、专业特色创新训练、专业实习、毕业论文（设计）、国际性学习课程、公共选修课。",
                "理工学科大类课程体系页明确写明：人工智能与数据技术平台课中的必修课程为《人工智能与数据技术基础》，计2学分。",
            ),
            note="培养方案说明强调“应修尽修”，即各类必修课程应按开设学期修读，无特殊原因不提前、延后或乱序修读。",
        ),
        manual_consult_hint="具体课程安排、先修关系和开课学期请以教务系统与学院当年通知为准。",
        version_label="2025级",
    ),
    EntrySeed(
        slug="info-school-2025-major-credit-overview",
        title="2025级信息学院各专业学位与总学分",
        summary=(
            "2025级信息学院专业中，计算机科学与技术152学分、信息管理与信息系统152学分、信息安全152学分、数据科学与大数据技术154学分；"
            "四个专业的学制均为四年，授予工学学士学位。"
        ),
        category_code="ACADEMIC",
        source_key="curriculum_2025",
        tags=(
            "总学分",
            "学位",
            "工学学士",
            "计算机科学与技术",
            "信息管理与信息系统",
            "信息安全",
            "数据科学与大数据技术",
            "2025级专业学分",
        ),
        body_md=_faq_body(
            "1 2025级 大类培养方案.pdf",
            (
                "2025级计算机多少学分",
                "2025级信管多少学分",
                "2025级信息安全多少学分",
                "2025级大数据多少学分",
                "这些专业授什么学位",
            ),
            (
                "计算机科学与技术专业学制四年，授予工学学士学位，总学分152学分。",
                "信息管理与信息系统专业学制四年，授予工学学士学位，总学分152学分。",
                "信息安全专业学制四年，授予工学学士学位，总学分152学分。",
                "数据科学与大数据技术专业学制四年，授予工学学士学位，总学分154学分。",
                "从专业修读要求看，计算机、信息管理与信息系统、信息安全的总学分一致，但数据科学与大数据技术的总学分更高。",
            ),
            note="专业模块和专业选修要求各不相同，例如信息管理与信息系统更强调信息管理理论基础/信息系统技术基础等模块，信息安全强调信息安全技术和信息安全应用模块，数据科学与大数据技术强调大数据技术和创研课程。",
        ),
        manual_consult_hint="总学分和课程模块以当年正式培养方案与教务系统为准，如涉及培养方案调整请看最新版。",
        version_label="2025级",
    ),
    EntrySeed(
        slug="info-school-2024-curriculum-overview",
        title="2024级信息学院大类培养方案总览（含辅修）",
        summary=(
            "2024级信息学院专业包括计算机科学与技术、信息管理与信息系统、信息安全、软件工程；统计学院与信息学院联合设置数据科学与大数据技术。"
            "2024级本科培养方案总体分为通识模块、专业模块、创新训练与科学研究、素质拓展与发展指导4个模块。"
        ),
        category_code="ACADEMIC",
        source_key="curriculum_2024",
        tags=(
            "2024级",
            "2024培养方案",
            "软件工程",
            "信息学院专业",
            "通识模块",
            "创新训练与科学研究",
            "素质拓展与发展指导",
            "数据科学与大数据技术",
            "辅修",
        ),
        body_md=_faq_body(
            "【1】2024级大类培养方案（含辅修）.pdf",
            (
                "2024级信息学院有哪些专业",
                "2024级有没有软件工程",
                "2024级培养方案分几个模块",
                "2024级数据科学与大数据技术归谁",
            ),
            (
                "2024级理工学科大类中，信息学院专业包括计算机科学与技术、信息管理与信息系统、信息安全、软件工程。",
                "数据科学与大数据技术由统计学院、信息学院联合设置。",
                "2024级本科培养方案总体分为四大模块：通识模块、专业模块、创新训练与科学研究、素质拓展与发展指导。",
                "通识模块包括思想政治理论课、基础技能（公共外语、公共数学、数据与信息技术平台课）、公共体育、通识课程群和国际暑期学校全英文课；专业模块包括部类核心课、专业核心课、个性化选修课。",
                "创新训练与科学研究模块包括研究训练、专业实习、毕业论文（设计）等；素质拓展与发展指导模块包括公共选修课、劳动教育、军事课、职业生涯规划、志愿服务。",
            ),
        ),
        manual_consult_hint="如果你要核对某个专业的具体课程和总学分，请继续查看该专业的修读指导计划页。",
        version_label="2024级",
    ),
    EntrySeed(
        slug="info-school-2024-minor-and-platform-course",
        title="2024级信息学院辅修与数据与信息技术平台课",
        summary=(
            "2024级辅修目录中，信息学院提供计算机科学与技术、信息管理与信息系统、软件工程、信息安全、"
            "数据科学与大数据技术专业（工学）的辅修学位和辅修专业。数据与信息技术平台课为《数据与信息技术基础》，"
            "2学分，1—2学期开设，必修，由信息学院统一组织授课。"
        ),
        category_code="ACADEMIC",
        source_key="curriculum_2024",
        tags=(
            "辅修",
            "辅修学位",
            "辅修专业",
            "双学位",
            "数据与信息技术基础",
            "平台课",
            "2学分",
            "信息学院统一组织",
        ),
        body_md=_faq_body(
            "【1】2024级大类培养方案（含辅修）.pdf",
            (
                "2024级信息学院能辅修什么",
                "2024级有没有软件工程辅修",
                "数据与信息技术基础是不是必修",
                "平台课谁组织授课",
            ),
            (
                "2024级辅修目录中，信息学院提供计算机科学与技术、信息管理与信息系统、软件工程、信息安全、数据科学与大数据技术专业（工学）的辅修学位和辅修专业。",
                "课程体系页明确写明：数据与信息技术平台课中的《数据与信息技术基础》课程编码为BMSECT0001，2学分，1—2学期开设，修读要求是必修。",
                "该页注释写明：数据与信息技术平台课由信息学院统一组织授课。",
                "如果你问的是2024级是否有数据科学与大数据技术专业（理学）辅修，目录中列在统计学院名下；信息学院目录中列的是数据科学与大数据技术专业（工学）辅修。",
            ),
        ),
        manual_consult_hint="辅修项目和平台课开课安排可能按学院当年通知微调，最终以教务系统和官方通知为准。",
        version_label="2024级",
    ),
    EntrySeed(
        slug="info-school-2024-2025-diff",
        title="2024级和2025级信息学院培养方案有什么主要差别",
        summary=(
            "2024级信息学院大类方案是4模块：通识模块、专业模块、创新训练与科学研究、素质拓展与发展指导；"
            "2025级改为3模块：立本模块、专业模块、卓越模块。2024级信息学院专业中包含软件工程，数据科学与大数据技术为统计学院与信息学院联合设置；"
            "2025级信息学院专业调整为计算机科学与技术、信息管理与信息系统、信息安全、数据科学与大数据技术。"
            "平台课口径也从《数据与信息技术基础》调整为《人工智能与数据技术基础》。"
        ),
        category_code="ACADEMIC",
        source_key="curriculum_compare_2024_2025",
        tags=(
            "2024和2025区别",
            "培养方案变化",
            "软件工程",
            "数据与信息技术基础",
            "人工智能与数据技术基础",
            "模块变化",
            "信息学院调整",
        ),
        body_md=_faq_body(
            "1 2025级 大类培养方案.pdf / 【1】2024级大类培养方案（含辅修）.pdf",
            (
                "2024和2025培养方案有什么区别",
                "软件工程去哪了",
                "平台课为什么不一样",
                "模块为什么从四个变成三个",
            ),
            (
                "2024级方案采用通识模块、专业模块、创新训练与科学研究、素质拓展与发展指导4模块结构；2025级方案改为立本模块、专业模块、卓越模块3模块结构。",
                "2024级信息学院专业包括计算机科学与技术、信息管理与信息系统、信息安全、软件工程；2025级信息学院专业列表调整为计算机科学与技术、信息管理与信息系统、信息安全、数据科学与大数据技术。",
                "2024级数据科学与大数据技术在目录和专业设置中体现为统计学院与信息学院联合设置；2025级信息学院专业列表中直接列出数据科学与大数据技术。",
                "2024级平台课口径是《数据与信息技术基础》；2025级平台课口径调整为《人工智能与数据技术基础》，反映了学校在培养方案修订说明中强调的人工智能赋能教育教学取向。",
            ),
            note="如果你要核对单个专业的总学分或学位，请进一步查看对应年份的专业修读指导计划页。",
        ),
        manual_consult_hint="跨年级对比只适用于当前两份培养方案文本，不代表后续年级继续沿用相同口径。",
        version_label="2024-2025对照",
    ),
)


async def _resolve_operator(db: AsyncSession) -> tuple[int, str]:
    admin = (
        await db.execute(select(User).where(User.work_no == "admin").limit(1))
    ).scalar_one_or_none()
    if admin:
        return admin.id, "SUPER_ADMIN"
    return 0, "KNOWLEDGE_FILE2_IMPORT"


async def _upsert_source(
    db: AsyncSession,
    seed: SourceSeed,
    *,
    only_missing: bool = False,
) -> tuple[KnowledgeSource, str]:
    current = (
        await db.execute(select(KnowledgeSource).where(KnowledgeSource.source_name == seed.source_name))
    ).scalar_one_or_none()
    fields = {
        "source_name": seed.source_name,
        "source_url": seed.source_url,
        "issuing_org": seed.issuing_org,
        "version_label": seed.version_label,
        "is_official": seed.is_official,
        "is_active": True,
    }
    if current is None:
        current = await repo.create_source(db, **fields)
        return current, "created"

    if only_missing:
        return current, "skipped"

    changed = False
    for key, value in fields.items():
        if getattr(current, key) != value:
            setattr(current, key, value)
            changed = True
    if changed:
        await db.flush()
        return current, "updated"
    return current, "skipped"


def _entry_changed(entry: KnowledgeEntry, seed: EntrySeed, source_id: int) -> bool:
    comparable_fields = {
        "title": seed.title,
        "summary": seed.summary,
        "category_code": seed.category_code,
        "applicable_condition": seed.applicable_condition,
        "required_materials": seed.required_materials,
        "process_steps": seed.process_steps,
        "body_md": seed.body_md,
        "source_id": source_id,
        "version_label": seed.version_label,
        "ambiguity_flag": seed.ambiguity_flag,
        "manual_consult_hint": seed.manual_consult_hint,
        "status": ENTRY_STATUS_PUBLISHED,
    }
    for key, expected in comparable_fields.items():
        if getattr(entry, key) != expected:
            return True
    current_tags = {tag.tag for tag in (entry.tags or [])}
    return current_tags != set(seed.tags)


async def _upsert_entry(
    db: AsyncSession,
    seed: EntrySeed,
    *,
    source_id: int,
    operator_id: int,
    operator_role: str,
    only_missing: bool = False,
) -> str:
    now = datetime.now(UTC)
    entry = await repo.get_entry_by_slug(db, seed.slug)
    if entry is None:
        entry = KnowledgeEntry(
            slug=seed.slug,
            title=seed.title,
            summary=seed.summary,
            category_code=seed.category_code,
            applicable_condition=seed.applicable_condition,
            required_materials=seed.required_materials,
            process_steps=seed.process_steps,
            body_md=seed.body_md,
            source_id=source_id,
            version_label=seed.version_label,
            status=ENTRY_STATUS_PUBLISHED,
            ambiguity_flag=seed.ambiguity_flag,
            manual_consult_hint=seed.manual_consult_hint,
            published_at=now,
            published_by=operator_id,
            deprecated_at=None,
            deprecated_by=None,
            created_by=operator_id,
            updated_by=operator_id,
        )
        db.add(entry)
        await db.flush()
        await repo.set_entry_tags(db, entry.id, list(seed.tags))
        await repo.add_revision(
            db,
            entry_id=entry.id,
            action=REVISION_PUBLISH,
            version_label=seed.version_label,
            status_before=None,
            status_after=ENTRY_STATUS_PUBLISHED,
            snapshot={
                "title": seed.title,
                "summary": seed.summary,
                "category_code": seed.category_code,
                "applicable_condition": seed.applicable_condition,
                "required_materials": seed.required_materials,
                "process_steps": seed.process_steps,
                "body_md": seed.body_md,
                "source_id": source_id,
                "version_label": seed.version_label,
                "tags": list(seed.tags),
            },
            operator_id=operator_id,
            operator_role=operator_role,
            note="party platform file2 import create+publish",
        )
        await log_action(
            db,
            event_type="KNOWLEDGE",
            entity_code="KNOWLEDGE_ENTRY",
            action="IMPORT_FILE2_ENTRY",
            entity_id=entry.id,
            actor_user_id=operator_id or None,
            actor_role=operator_role,
            detail=build_audit_detail(
                target={"entry_id": entry.id, "slug": entry.slug, "title": entry.title},
                refs={"source_name": next(src.source_name for src in _SOURCES if src.key == seed.source_key)},
                changes={"after": {"status": ENTRY_STATUS_PUBLISHED, "tags": list(seed.tags)}},
                metrics={"created": 1},
            ),
        )
        return "created"

    if only_missing:
        return "skipped"

    if not _entry_changed(entry, seed, source_id):
        return "skipped"

    entry.title = seed.title
    previous_status = entry.status
    entry.summary = seed.summary
    entry.category_code = seed.category_code
    entry.applicable_condition = seed.applicable_condition
    entry.required_materials = seed.required_materials
    entry.process_steps = seed.process_steps
    entry.body_md = seed.body_md
    entry.source_id = source_id
    entry.version_label = seed.version_label
    entry.status = ENTRY_STATUS_PUBLISHED
    entry.ambiguity_flag = seed.ambiguity_flag
    entry.manual_consult_hint = seed.manual_consult_hint
    entry.deprecated_at = None
    entry.deprecated_by = None
    if entry.published_at is None:
        entry.published_at = now
    entry.published_by = operator_id
    entry.updated_by = operator_id
    await db.flush()
    await repo.set_entry_tags(db, entry.id, list(seed.tags))
    await repo.add_revision(
        db,
        entry_id=entry.id,
        action=REVISION_PUBLISH,
        version_label=seed.version_label,
        status_before=previous_status,
        status_after=ENTRY_STATUS_PUBLISHED,
        snapshot={
            "title": seed.title,
            "summary": seed.summary,
            "category_code": seed.category_code,
            "applicable_condition": seed.applicable_condition,
            "required_materials": seed.required_materials,
            "process_steps": seed.process_steps,
            "body_md": seed.body_md,
            "source_id": source_id,
            "version_label": seed.version_label,
            "tags": list(seed.tags),
        },
        operator_id=operator_id,
        operator_role=operator_role,
        note="party platform file2 import refresh",
    )
    await log_action(
        db,
        event_type="KNOWLEDGE",
        entity_code="KNOWLEDGE_ENTRY",
        action="IMPORT_FILE2_ENTRY",
        entity_id=entry.id,
        actor_user_id=operator_id or None,
        actor_role=operator_role,
        detail=build_audit_detail(
            target={"entry_id": entry.id, "slug": entry.slug, "title": entry.title},
            refs={"source_name": next(src.source_name for src in _SOURCES if src.key == seed.source_key)},
            changes={"after": {"status": ENTRY_STATUS_PUBLISHED, "tags": list(seed.tags)}},
            metrics={"updated": 1},
        ),
    )
    return "updated"


async def import_party_platform_file2_knowledge(
    db: AsyncSession,
    *,
    only_missing: bool = False,
    skip_if_any_entries: bool = False,
) -> tuple[dict[str, int], dict[str, int], bool]:
    operator_id, operator_role = await _resolve_operator(db)
    source_ids: dict[str, int] = {}
    source_stats = {"created": 0, "updated": 0, "skipped": 0}
    entry_stats = {"created": 0, "updated": 0, "skipped": 0}

    existing_entries = await db.scalar(select(func.count()).select_from(KnowledgeEntry))
    skipped_due_to_existing_entries = bool(skip_if_any_entries and existing_entries and existing_entries > 0)
    if skipped_due_to_existing_entries:
        source_stats["skipped"] = len(_SOURCES)
        entry_stats["skipped"] = len(_ENTRIES)
        return source_stats, entry_stats, True

    for source in _SOURCES:
        row, status = await _upsert_source(db, source, only_missing=only_missing)
        source_ids[source.key] = row.id
        source_stats[status] += 1

    for entry in _ENTRIES:
        status = await _upsert_entry(
            db,
            entry,
            source_id=source_ids[entry.source_key],
            operator_id=operator_id,
            operator_role=operator_role,
            only_missing=only_missing,
        )
        entry_stats[status] += 1

    return source_stats, entry_stats, False


async def _main() -> int:
    async with AsyncSessionLocal() as db:
        source_stats, entry_stats, skipped_due_to_existing_entries = await import_party_platform_file2_knowledge(db)
        await db.commit()

    if skipped_due_to_existing_entries:
        logger.info(
            "party-platform-file2 knowledge import skipped because the knowledge library already contains entries"
        )
        return 0

    logger.info(
        "party-platform-file2 knowledge import finished: sources created=%s updated=%s skipped=%s; "
        "entries created=%s updated=%s skipped=%s",
        source_stats["created"],
        source_stats["updated"],
        source_stats["skipped"],
        entry_stats["created"],
        entry_stats["updated"],
        entry_stats["skipped"],
    )
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
