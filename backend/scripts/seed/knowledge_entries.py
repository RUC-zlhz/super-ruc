"""默认官方知识正文种子（S49）。

种子只保存结构化摘要、办理提醒与官方链接，不复制政策全文。对缺少稳定
公开办理细则的事项标记 ambiguity_flag，引导学生转人工或查看官方入口。
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.models import (
    ENTRY_STATUS_PUBLISHED,
    KnowledgeEntry,
    KnowledgeEntryTag,
    KnowledgeSource,
)
from scripts.seed import SeedResult

DOMAIN = "knowledge_entries"


_ENTRIES: list[dict[str, Any]] = [
    {
        "slug": "ruc-student-suspension-guide",
        "title": "休学办理官方指引",
        "summary": "学生因病、创业、应征入伍等原因需要暂停学业时，应先查阅学校学生工作部休学复学说明，再按校级系统和学院要求提交材料。",
        "category_code": "ACADEMIC",
        "source": {
            "source_name": "中国人民大学学生工作部休学复学说明",
            "source_url": "https://xsc.ruc.edu.cn/info/1327/4598.htm",
            "issuing_org": "中国人民大学学生工作部",
            "version_label": "official",
        },
        "applicable_condition": "拟申请休学、暂停学业或需要了解休学影响的在籍学生。",
        "required_materials": "以学生工作部页面和学院通知为准；涉及病休、入伍等情形通常需上传对应证明材料。",
        "process_steps": "1. 先阅读官方页面；2. 准备证明材料；3. 通过学校/学院指定系统提交；4. 按学院老师反馈补正或线下确认。",
        "body_md": "敏感或特殊情形不在平台直接判定，学生应以官方页面、学院老师和校级系统最终要求为准。",
        "tags": ["休学", "学籍", "学生工作部"],
    },
    {
        "slug": "ruc-student-resumption-guide",
        "title": "复学办理官方指引",
        "summary": "休学期满或休学原因消除后，复学办理应对照学生工作部休学复学说明及学院通知执行。",
        "category_code": "ACADEMIC",
        "source": {
            "source_name": "中国人民大学学生工作部休学复学说明",
            "source_url": "https://xsc.ruc.edu.cn/info/1327/4598.htm",
            "issuing_org": "中国人民大学学生工作部",
            "version_label": "official",
        },
        "applicable_condition": "已办理休学且拟恢复学籍、返校继续学习的学生。",
        "required_materials": "以官方页面和学院通知为准；如涉及病休复学，应按要求准备健康或诊断相关材料。",
        "process_steps": "1. 对照官方复学要求；2. 在规定时间内提交复学申请；3. 学院和学校审核；4. 审核通过后恢复相关学习安排。",
        "body_md": "复学时间、材料和审核口径以校级通知为准；平台只提供入口和提醒。",
        "tags": ["复学", "学籍", "学生工作部"],
    },
    {
        "slug": "ruc-scholarship-aid-program-guide",
        "title": "奖助项目与资助申请入口",
        "summary": "奖学金、助学金和资助项目以学生工作部发布的项目程序与学院通知为准，学生应关注申请时间、材料要求和公示环节。",
        "category_code": "SCHOLARSHIP",
        "source": {
            "source_name": "中国人民大学学生工作部奖助项目程序",
            "source_url": "https://xsc.ruc.edu.cn/info/1020/3471.htm",
            "issuing_org": "中国人民大学学生工作部",
            "version_label": "official",
        },
        "applicable_condition": "拟申请奖助学金、资助项目或查询奖助政策入口的学生。",
        "required_materials": "以项目通知为准，通常包括申请表、成绩/成果材料、家庭经济情况或学院要求的佐证材料。",
        "process_steps": "1. 查看学生工作部和学院通知；2. 按项目填写材料；3. 学院初审；4. 学校复核、公示或发放。",
        "body_md": "平台不替代项目通知，不承诺资格结论；涉及资助隐私时只给官方链接和人工咨询入口。",
        "tags": ["奖学金", "助学金", "资助", "学生工作部"],
    },
    {
        "slug": "ruc-archive-transfer-guide",
        "title": "档案转递办理入口",
        "summary": "档案转递属于学校档案服务事项，应以中国人民大学信息服务中心档案馆办事页面为准。",
        "category_code": "DAILY_AFFAIRS",
        "source": {
            "source_name": "中国人民大学信息服务中心档案转递办理页",
            "source_url": "https://isc.ruc.edu.cn/bmfwa/dag/70b1d89905b04fffac3a00d87d57c2f3.htm",
            "issuing_org": "中国人民大学信息服务中心",
            "version_label": "official",
        },
        "applicable_condition": "毕业、升学、就业或其他需要办理档案转递的学生。",
        "required_materials": "请以档案馆办理页列明材料为准；涉及接收单位信息时务必核对单位名称、地址和联系人。",
        "process_steps": "1. 打开官方办理页；2. 核对档案接收单位信息；3. 按页面要求提交或线下办理；4. 保存办理记录。",
        "body_md": "档案信息敏感，平台不展示个人档案内容，仅提供官方入口和办理提醒。",
        "tags": ["档案", "转递", "毕业", "信息服务中心"],
    },
    {
        "slug": "ruc-academic-calendar-holiday-entry",
        "title": "校历与节假日安排查询入口",
        "summary": "教学周、考试周、寒暑假和节假日安排以教务处校历页面及学校通知为准。",
        "category_code": "ACADEMIC",
        "source": {
            "source_name": "中国人民大学教务处 2025-2026 学年校历",
            "source_url": "https://jiaowu.ruc.edu.cn/jxrlhome/88527dd018e141b88b9a995f97c8ce7c.htm",
            "issuing_org": "中国人民大学教务处",
            "version_label": "2025-2026",
        },
        "applicable_condition": "需要查询教学安排、考试周、假期或节假日调整的学生。",
        "required_materials": "无需提交材料；如涉及请假或离校，请另按学院和学校请假规定办理。",
        "process_steps": "1. 查看教务处校历；2. 对照学院通知；3. 涉及离校、请假、考试冲突时联系辅导员或教务老师。",
        "body_md": "节假日临时调整以学校最新通知为准；平台只保存校历入口。",
        "tags": ["校历", "放假", "教学周", "教务处"],
    },
    {
        "slug": "info-school-announcements-entry",
        "title": "信息学院公告查询入口",
        "summary": "学院通知、讲座、评奖评优和事务提醒应优先查看信息学院官网公告栏目。",
        "category_code": "OTHER",
        "source": {
            "source_name": "中国人民大学信息学院公告栏目",
            "source_url": "https://info.ruc.edu.cn/xwgg/xygg/index.htm",
            "issuing_org": "中国人民大学信息学院",
            "version_label": "official",
        },
        "applicable_condition": "需要查询学院公告、事务通知、活动通知或后续办理要求的学生。",
        "required_materials": "按具体公告要求准备；平台不统一推断材料。",
        "process_steps": "1. 打开学院公告栏目；2. 搜索对应事项；3. 按公告联系人或学院老师要求办理。",
        "body_md": "学院公告会随时间更新，平台仅提供入口和检索提示。",
        "tags": ["信息学院", "公告", "通知"],
    },
    {
        "slug": "info-school-consultation-entry",
        "title": "信息学院事务咨询入口",
        "summary": "党团学、学院办公室和学生事务的具体联系人可能随分工调整，应优先通过信息学院官网入口和最新公告确认。",
        "category_code": "OTHER",
        "source": {
            "source_name": "中国人民大学信息学院官网",
            "source_url": "https://info.ruc.edu.cn/",
            "issuing_org": "中国人民大学信息学院",
            "version_label": "official",
        },
        "applicable_condition": "无法确定具体办理老师、办公室或党团学负责人的学生。",
        "required_materials": "咨询前准备学号、姓名、事项类型和已查阅的官方链接。",
        "process_steps": "1. 先查学院官网和公告；2. 仍不确定时联系学院办公室或辅导员；3. 涉及敏感事项时线下核验。",
        "body_md": "本条为官方入口指引，不承诺固定联系人；以学院当期分工为准。",
        "tags": ["信息学院", "咨询", "办公室", "党团学"],
        "ambiguity_flag": True,
        "manual_consult_hint": "联系人和分工可能变化，请通过学院官网或辅导员确认。",
    },
    {
        "slug": "ruc-outbound-affairs-entry",
        "title": "出国出境事务办理入口",
        "summary": "出国出境、国际交流或涉外事项应以学校国际交流相关官方入口和学院通知为准。",
        "category_code": "DAILY_AFFAIRS",
        "source": {
            "source_name": "中国人民大学国际交流处官方入口",
            "source_url": "https://io.ruc.edu.cn/",
            "issuing_org": "中国人民大学国际交流处",
            "version_label": "official",
        },
        "applicable_condition": "拟办理出国出境、交换交流、涉外证明或相关咨询的学生。",
        "required_materials": "以国际交流处、学院公告及项目通知为准；涉证照、审批和隐私材料不在平台展示。",
        "process_steps": "1. 查询国际交流处官方入口；2. 查学院对应项目通知；3. 按要求提交申请；4. 不确定时联系学院老师。",
        "body_md": "出国出境事项政策性强，平台只提供官方入口和风险提示。",
        "tags": ["出国", "出境", "国际交流", "涉外"],
        "ambiguity_flag": True,
        "manual_consult_hint": "请以国际交流处和学院项目通知为准，必要时转人工。",
    },
    {
        "slug": "party-development-official-rule-entry",
        "title": "发展党员工作细则入口",
        "summary": "党员发展流程、培养考察和审批要求应以党内法规与学院党组织通知为准。",
        "category_code": "PARTY",
        "source": {
            "source_name": "中国共产党发展党员工作细则",
            "source_url": "https://news.12371.cn/2014/06/10/ARTI1402408565380843.shtml",
            "issuing_org": "共产党员网",
            "version_label": "official",
        },
        "applicable_condition": "提交入党申请、积极分子培养、发展对象、预备党员转正等党务流程相关学生。",
        "required_materials": "以党支部和学院党委通知为准，常见材料包括申请书、思想汇报、培养考察材料、政审或公示材料等。",
        "process_steps": "1. 对照党内法规和学院流程；2. 按党支部通知提交材料；3. 支部培养考察和会议讨论；4. 上级党组织审批。",
        "body_md": "党务流程不由平台自动判定资格；敏感材料不在线展示，平台只做节点提示和官方链接。",
        "tags": ["入党", "党员发展", "党务", "共产党员网"],
    },
    {
        "slug": "party-knowledge-self-test-entry",
        "title": "共产党员网知识自测入口",
        "summary": "党建理论自测题目应优先使用有来源的官方题库或法规依据；默认不编造题目。",
        "category_code": "PARTY",
        "source": {
            "source_name": "共产党员网知识自测",
            "source_url": "https://www.12371.cn/special/zszc/",
            "issuing_org": "共产党员网",
            "version_label": "official",
        },
        "applicable_condition": "需要进行党章党规、党史和党建知识自主学习或题库导入溯源的学生和老师。",
        "required_materials": "无需提交材料；如导入平台题库，需保留题目来源名称和来源链接。",
        "process_steps": "1. 打开共产党员网知识自测入口；2. 进行自主练习；3. 管理员可按模板导入有来源题目；4. 学生端抽题不展示答案。",
        "body_md": "若公开页面无法稳定提取完整题面与答案，平台只提供导入器和来源字段，不生成伪官方题。",
        "tags": ["理论自测", "党章", "党史", "题库"],
    },
    {
        "slug": "dorm-adjustment-consultation-entry",
        "title": "宿舍调整咨询入口",
        "summary": "宿舍调整涉及住宿资源和个人隐私，未找到稳定公开办理细则时只提供官方入口和人工咨询提示。",
        "category_code": "DAILY_AFFAIRS",
        "source": {
            "source_name": "中国人民大学学生工作部官方入口",
            "source_url": "https://xsc.ruc.edu.cn/",
            "issuing_org": "中国人民大学学生工作部",
            "version_label": "official",
        },
        "applicable_condition": "需要咨询宿舍调整、住宿困难或特殊住宿需求的学生。",
        "required_materials": "以学生工作部、后勤或学院老师实际要求为准；平台不收集不必要隐私。",
        "process_steps": "1. 先查学生工作部和学院通知；2. 与辅导员说明情况；3. 按官方渠道提交材料；4. 等待人工审核。",
        "body_md": "本条不生成宿舍调整流程结论，避免依据不充分造成误导。",
        "tags": ["宿舍", "住宿", "人工咨询"],
        "ambiguity_flag": True,
        "manual_consult_hint": "宿舍调整请先联系辅导员或查看学生工作部最新通知。",
    },
]


async def _upsert_source(db: AsyncSession, payload: dict[str, Any]) -> tuple[KnowledgeSource, bool]:
    source_url = payload.get("source_url")
    stmt = select(KnowledgeSource).where(KnowledgeSource.source_url == source_url)
    row = (await db.execute(stmt)).scalars().first()
    created = False
    if row is None:
        row = KnowledgeSource(is_official=True, is_active=True, **payload)
        db.add(row)
        created = True
    else:
        for key, value in payload.items():
            setattr(row, key, value)
        row.is_official = True
        row.is_active = True
    await db.flush()
    return row, created


async def _replace_tags(db: AsyncSession, entry_id: int, tags: list[str]) -> None:
    await db.execute(delete(KnowledgeEntryTag).where(KnowledgeEntryTag.entry_id == entry_id))
    for tag in sorted({item.strip() for item in tags if item and item.strip()}):
        db.add(KnowledgeEntryTag(entry_id=entry_id, tag=tag))
    await db.flush()


async def seed(db: AsyncSession) -> SeedResult:
    inserted = updated = skipped = 0
    now = datetime.now(UTC)
    for spec in _ENTRIES:
        source, _ = await _upsert_source(db, spec["source"])
        entry_fields = {
            key: spec.get(key)
            for key in (
                "title",
                "summary",
                "category_code",
                "applicable_condition",
                "required_materials",
                "process_steps",
                "body_md",
                "manual_consult_hint",
            )
        }
        entry_fields.update(
            {
                "source_id": source.id,
                "version_label": spec["source"].get("version_label"),
                "status": ENTRY_STATUS_PUBLISHED,
                "ambiguity_flag": bool(spec.get("ambiguity_flag", False)),
                "updated_by": None,
            }
        )
        row = (
            await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.slug == spec["slug"]))
        ).scalar_one_or_none()
        if row is None:
            row = KnowledgeEntry(
                slug=spec["slug"],
                created_by=None,
                published_at=now,
                **entry_fields,
            )
            db.add(row)
            await db.flush()
            inserted += 1
        else:
            changed = False
            for key, value in entry_fields.items():
                if getattr(row, key) != value:
                    setattr(row, key, value)
                    changed = True
            if row.published_at is None:
                row.published_at = now
                changed = True
            if changed:
                updated += 1
            else:
                skipped += 1
        await _replace_tags(db, row.id, spec.get("tags") or [])
    return SeedResult(domain=DOMAIN, inserted=inserted, updated=updated, skipped=skipped)
