from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH

from docx_common import (
    DEEP_BLUE,
    MUTED,
    ROOT,
    add_bullets,
    add_callout,
    add_direct_paragraph,
    add_kv_table,
    add_paragraph,
    add_spacer,
    add_table,
    finalize,
    prepare_document,
    today_label,
)


TEMPLATE = ROOT / "docs" / "templates" / "软件测试报告模板.docx"
DEFAULT_OUTPUT = ROOT / "output" / "doc" / "软件测试报告-信息学院学生综合服务与党团管理平台-v1.0.docx"


PROJECT_NAME = "信息学院学生综合服务与党团管理平台"
PRODUCTION_BASE_URL = "http://10.10.0.13/"
PRODUCTION_SNAPSHOT_DATE = "2026-06-07"
PRODUCTION_WEB_TITLE = "信息学院管理后台"
PRODUCTION_WEB_JS = "/assets/index-CTe-2Tbm.js"
PRODUCTION_WEB_CSS = "/assets/index-5iSv60ht.css"
PRODUCTION_KNOWLEDGE_TOTAL = 16
PRODUCTION_TEMPLATE_ENTRY_COUNT = 4
PRODUCTION_CATEGORY_COUNT = 9


def git_head_short() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def build_doc(output_path: Path) -> Path:
    doc = prepare_document(TEMPLATE)
    updated_at = today_label()
    head = git_head_short()

    add_direct_paragraph(doc, "文档编号：SIP-TEST-1.0", size=11, color=MUTED)
    add_direct_paragraph(
        doc,
        PROJECT_NAME,
        size=22,
        bold=True,
        color=DEEP_BLUE,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=8,
    )
    add_direct_paragraph(
        doc,
        "软件测试报告",
        size=18,
        bold=True,
        color=DEEP_BLUE,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=6,
    )
    add_direct_paragraph(
        doc,
        f"版本：V1.0    当前仓库 HEAD：{head}    更新日期：{updated_at}",
        size=11,
        color=MUTED,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=8,
    )

    add_kv_table(
        doc,
        [
            ("测试对象", f"{PROJECT_NAME} 当前主线代码与生产部署链路"),
            ("测试口径", f"整合 2026-05-26 全量测试工程师审查、2026-06-06 PR #6 专项复核与 {PRODUCTION_SNAPSHOT_DATE} 生产在线抽检"),
            ("覆盖平台", "FastAPI 后端、Vue 3 Web 管理端、uni-app 小程序、金仓数据库、内网生产环境"),
            ("测试目标", "验证代码基线、线上真实响应、认证边界和残留缺陷，并给出当前交付风险与改进建议"),
        ],
    )

    add_spacer(doc)
    add_paragraph(doc, "文档变更历史记录", style="Heading 2")
    add_table(
        doc,
        ["序号", "变更日期", "变更人员", "变更内容详情描述", "版本"],
        [["1", updated_at, "项目组 / Codex", "按 2026-06-07 生产在线抽检重新收口的正式测试报告，区分线上已验证事实与仅代码/历史专项验证结论。", "V1.0"]],
        [0.5, 1.0, 1.0, 3.3, 0.7],
    )

    add_paragraph(doc, "1 测试概述", style="Heading 1")
    add_paragraph(doc, "1.1 编写目的", style="Heading 2")
    add_paragraph(
        doc,
        f"本文档用于沉淀 {PROJECT_NAME} 当前主线的测试结论，统一记录已完成的静态检查、构建验证、自动化回归、生产在线抽检和专项业务验证结果，并明确区分“当前线上已核对事实”与“仅由代码实现和历史专项验证支撑的能力结论”，据此识别当前交付的残留风险和缺陷优先级。",
        style="First Paragraph",
    )

    add_paragraph(doc, "1.2 测试范围", style="Heading 2")
    add_bullets(
        doc,
        [
            "后端：鉴权、知识库、通知、党团流程、事务审批、画像、荣誉、学业分析、导入导出与审计。",
            "Web 管理端：登录态、通知中心、审批工作台、学生管理、党团流程、学业与审计页面。",
            "小程序学生端：首页、知识库、通知中心、事务申请、党团流程、画像与学业分析。",
            "环境链路：本地金仓回归环境、内网生产部署、健康检查与关键 API 认证边界。",
        ],
    )

    add_paragraph(doc, "1.3 测试人员与时间", style="Heading 2")
    add_table(
        doc,
        ["项目", "内容"],
        [
            ["执行 / 汇总人员", "Codex（基于仓库留痕测试结果与专项验证记录整理）"],
            ["主回归窗口", "2026-05-26：S50 当前 HEAD 测试工程师 Bug 审查"],
            ["后续专项验证", "2026-05-26 ~ 2026-06-06：证明 PDF、微信订阅消息、模板下载、按钮反馈、PR #6 合并复核等专项补验"],
            ["生产在线抽检", f"{PRODUCTION_SNAPSHOT_DATE}：对 {PRODUCTION_BASE_URL} 根页、healthz、知识搜索、知识分类、受保护接口和历史共享口令做在线核对"],
            ["当前代码基线", f"当前仓库 HEAD {head}；已知全量测试基线来自 2026-05-26 的 current-head 审查"],
        ],
        [1.45, 5.05],
    )

    add_paragraph(doc, "1.4 测试环境", style="Heading 2")
    add_table(
        doc,
        ["环境", "配置 / 说明"],
        [
            ["后端", "FastAPI + uv；数据库为 Kingbase；支持本地 Docker 开发环境与内网生产环境"],
            ["Web 管理端", "Vue 3 + pnpm；通过 build 结果验证类型与构建链路"],
            ["小程序", "uni-app + mp-weixin；通过 vue-tsc 与 build:mp-weixin 验证交付包"],
            ["生产环境", f"{PRODUCTION_BASE_URL} 内网部署；本轮已在线核对根页标题={PRODUCTION_WEB_TITLE}、资源 {PRODUCTION_WEB_JS} / {PRODUCTION_WEB_CSS}、healthz 与知识接口"],
            ["测试账号", "历史共享口令 admin / admin123 于 2026-06-07 在线核对返回 401，不再作为有效线上测试账号；当前有效账号需由部署维护方发放"],
        ],
        [1.3, 5.2],
    )

    add_paragraph(doc, "2 测试设计", style="Heading 1")
    add_paragraph(doc, "2.1 测试策略", style="Heading 2")
    add_table(
        doc,
        ["测试层次", "目标", "代表验证"],
        [
            ["静态检查", "快速发现语法、风格和明显实现错误", "ruff、compileall / py_compile、vue-tsc"],
            ["自动化回归", "验证后端契约与业务流程主干是否稳定", "pytest 全量 / 定向集成测试"],
            ["构建验证", "确认 Web 与小程序产物可生成", "pnpm -C web build、pnpm -C miniapp build:mp-weixin"],
            ["生产在线抽检", "确认内网部署当前真实响应、公开能力与认证边界", "GET /、GET /healthz、knowledge/search、knowledge/categories、受保护接口 401、旧共享口令登录 401"],
            ["专项业务验证", "验证证明预览、订阅消息、模板下载等高风险细节", "S57、S64、S70、PR #6 merge review 等记录"],
        ],
        [1.1, 1.8, 3.6],
    )

    add_paragraph(doc, "2.2 测试用例设计", style="Heading 2")
    add_table(
        doc,
        ["模块", "核心用例", "关注点"],
        [
            ["知识库", "关键词检索、来源展示、模板下载、AI 匹配", "必须优先返回官方来源，避免幻觉或空链路"],
            ["党团流程", "模板查看、学生流程发起、节点推进、提醒记录", "scope 权限、节点状态推进与留痕一致性"],
            ["事务审批", "请假/盖章/证明提交、驳回重提、审批通过、证明 PDF 预览", "状态机、附件、审批角色与 PDF 开放条件"],
            ["通知中心", "圈人预览、批次发送、投递明细、站内消息查看", "目标范围准确性、失败原因回看、多渠道边界"],
            ["画像与荣誉", "主档查看、纠错申诉、荣誉展示、导出与敏感字段保护", "字段权限、越权拒绝、导出脱敏"],
            ["学业分析", "成绩单解析、培养方案比对、课程建议", "仅做弱提示，不给出毕业强结论"],
        ],
        [1.15, 2.45, 2.95],
    )

    add_paragraph(doc, "2.3 测试总体情况", style="Heading 2")
    add_table(
        doc,
        ["检查项", "结果", "证据"],
        [
            ["后端静态检查", "通过", "2026-05-26：ruff、compileall 均通过"],
            ["后端全量回归", "通过", "2026-05-26：pytest 143 passed, 3 warnings"],
            ["Web 管理端构建", "通过", "2026-05-26 current-head 审查通过"],
            ["小程序类型与构建", "通过", "2026-05-26 current-head 审查通过；2026-06-06 PR #6 合并复核再次通过"],
            ["生产根页在线抽检", "通过", f"GET / => 200，title={PRODUCTION_WEB_TITLE}，静态资源为 {PRODUCTION_WEB_JS} / {PRODUCTION_WEB_CSS}"],
            ["生产知识搜索在线抽检", "通过", f"GET /api/v1/knowledge/search?page=1&page_size=20 => 200，total={PRODUCTION_KNOWLEDGE_TOTAL}，其中模板下载类条目 {PRODUCTION_TEMPLATE_ENTRY_COUNT} 个"],
            ["生产知识分类在线抽检", "通过", f"GET /api/v1/knowledge/categories => 200，返回 {PRODUCTION_CATEGORY_COUNT} 个分类"],
            ["生产受保护接口边界", "通过", "未带 Bearer token 访问 /api/v1/knowledge/templates 与 /api/v1/workflow/public/templates 均返回 401 缺少 Authorization"],
            ["历史共享账号在线复核", "已失效", "POST /api/v1/auth/login 使用 admin / admin123 返回 401：工号或密码错误"],
            ["专项验证", "通过 / 部分保留前置条件", "证明 PDF、微信订阅消息、模板直下载等专项结果已留痕"],
        ],
        [1.9, 0.85, 3.75],
    )

    add_paragraph(doc, "3 测试执行结果", style="Heading 1")
    add_paragraph(doc, "3.1 平台级执行结果", style="Heading 2")
    add_table(
        doc,
        ["平台", "执行结果", "说明"],
        [
            ["后端代码基线", "通过", "当前留痕基线为 2026-05-26：143 passed, 3 warnings；后续针对知识、证明、订阅消息等能力有专项补验"],
            ["Web 管理端构建基线", "通过", "构建链路稳定；当前风险主要集中在登录态、401 跳转和通知错误态呈现"],
            ["生产匿名 / 未登录面", "通过", "根页、healthz、知识搜索、知识分类均在线；受保护接口的未登录边界正确返回 401"],
            ["生产认证链路", "部分验证", "已确认受保护接口需要 Bearer token，但本轮未拿到当前有效线上账号；旧共享口令 admin / admin123 已失效"],
            ["微信小程序联调", "部分验证", "mp-weixin 构建可通过；真实微信授权、手机端送达与线上学生账号仍依赖外部前置条件"],
        ],
        [1.45, 0.9, 4.15],
    )

    add_paragraph(doc, "3.2 重点业务闭环结果", style="Heading 2")
    add_table(
        doc,
        ["业务闭环", "当前结论", "说明"],
        [
            ["知识库公开查询", "线上已验证", f"knowledge/search 在线返回 total={PRODUCTION_KNOWLEDGE_TOTAL}，包含休学、复学、校历、学院公告等官方知识条目及 {PRODUCTION_TEMPLATE_ENTRY_COUNT} 个模板下载类条目"],
            ["模板文件鉴权", "线上边界已验证", "knowledge/templates 未带 token 返回 401；模板直下载能力仍以 S70 与 PR #6 历史专项验证为主"],
            ["党团流程管理", "代码与历史验证通过", "流程模板、发起、推进与提醒链路已有代码和历史专项验证；但本轮线上未使用有效账号实登复核"],
            ["事务申请与审批", "代码与历史验证通过", "请假、盖章、证明申请与审批工作台可用；证明 PDF 仅在 APPROVED 后开放预览，但本轮线上未完成真实账号复测"],
            ["通知中心", "代码与历史验证通过", "圈人、发送、批次查看链路已有历史验证；当前仍保留 scoped 越权投递与生产 mock 入口等已登记缺陷"],
            ["画像、荣誉与学业分析", "代码与历史验证通过", "本人查看、教师范围查看、纠错申诉、荣誉展示和弱结论学业分析已打通；本轮线上未使用有效角色账号逐项实登"],
        ],
        [1.55, 1.25, 3.7],
    )

    add_paragraph(doc, "3.3 残留风险与未覆盖项", style="Heading 2")
    add_bullets(
        doc,
        [
            "当前最新的全量后端回归基线来自 2026-05-26；2026-06-06 的 PR #6 合并复核主要覆盖小程序构建与模板相关链路，未重新执行一轮新的全量 pytest。",
            "2026-06-07 在线核对表明，旧版文档沿用的共享口令 admin / admin123 已失效；后续任何生产实登验收都必须重新发放当前有效的管理员、教师和学生账号。",
            "生产环境当前缺少可直接用于本轮复测的真实教师 / 学生账号；证明类申请虽然代码上可在正确角色下完成审批并生成 PDF，但正式验收仍需准备真实账号。",
            "微信订阅消息链路代码与生产出网已验证可达，但真实手机端送达仍依赖用户在小程序中完成有效模板授权。",
            "部分 Web / Miniapp 风险属于逻辑与分页体验问题，不影响系统启动和主链路演示，但会影响正式交付质量。",
            "由于本轮没有拿到当前有效生产账号，管理端登录后功能、党团流程、事务审批和通知操作未能在 10.10.0.13 上重新完成一轮实登抽检。",
        ],
    )

    add_paragraph(doc, "4 缺陷分析", style="Heading 1")
    add_paragraph(doc, "4.1 缺陷统计", style="Heading 2")
    add_table(
        doc,
        ["类型", "数量", "说明"],
        [
            ["Crash", "0", "当前主线未发现可稳定复现的新增崩溃类问题"],
            ["Logic", "14", "范围集中在认证/权限、通知治理、Web 登录态与错误态、小程序分页统计"],
            ["基础分合计", "112", "按测试实验指导书口径：Crash 15 分 / Logic 8 分"],
        ],
        [1.4, 0.9, 4.2],
    )

    add_paragraph(doc, "4.2 缺陷分类分析", style="Heading 2")
    add_table(
        doc,
        ["类别", "数量", "代表问题"],
        [
            ["后端认证与权限", "4", "改密后旧 token 未失效、scoped 看板全局聚合、协同角色可发起但不能搜人、scoped 通知可越权投递"],
            ["Web 登录态与错误处理", "4", "默认落点错误、/auth/me 临时失败误登出、401 跳转丢 redirect、党团提醒 raw fetch 绕过统一处理"],
            ["Web 通知治理", "2", "生产暴露模拟短信回执入口、详情/批次失败被展示成正常空态"],
            ["Miniapp 统计与分页", "4", "首页未读通知、首页待跟进申请、事务申请列表、画像历史都只计算第一页"],
        ],
        [1.55, 0.7, 4.25],
    )

    add_paragraph(doc, "4.3 典型缺陷说明", style="Heading 2")
    add_table(
        doc,
        ["ID", "模块", "问题描述", "影响"],
        [
            ["S50-L01", "后端认证", "用户修改密码后旧 access token 与 refresh token 仍然有效", "存在会话安全风险，应列为 P0"],
            ["S50-L02", "运营看板", "带 scope 的教师访问 overview 时仍看到全局统计", "会造成越权数据暴露，应优先修复"],
            ["S50-L04", "通知中心", "scoped 通知编辑者可预览并投递 scope 外学生", "会导致误投和越权投递，是核心业务风险"],
            ["S50-L07", "Web 401 处理", "token 失效后普通请求或画像下载都直接跳裸 /login，丢失 redirect", "影响用户连续操作体验与复测效率"],
            ["S50-L11 ~ L14", "小程序", "首页和历史列表只统计第一页，没有加载更多或剩余提示", "不影响启动，但会影响数据完整性和可用性"],
        ],
        [0.9, 1.2, 2.6, 1.8],
    )
    add_callout(doc, "说明：典型缺陷完整清单、代码定位和优先级以仓库根目录 bug-report.md 与 S50 细化文件为准。")

    add_paragraph(doc, "5 测试结论与建议", style="Heading 1")
    add_paragraph(doc, "5.1 测试结论", style="Heading 2")
    add_bullets(
        doc,
        [
            "当前主线代码可以通过后端静态检查、后端全量回归、Web 构建、小程序类型检查与小程序构建，系统已具备稳定演示和继续迭代的基础。",
            f"生产环境 {PRODUCTION_BASE_URL} 当前根页、healthz、知识搜索和知识分类接口均在线，未登录访问受保护接口时认证边界也符合预期。",
            "生产认证链路尚不能视为“已完整验证”：历史共享口令 admin / admin123 已失效，本轮未拿到新的有效线上账号，因此登录后的真实业务操作仍需补一轮实登复测。",
            "截至当前留痕口径，未发现新的崩溃类问题，但仍存在 14 个已确认 Logic bug；其中权限越权、旧 token 失效和通知治理问题应在正式交付前优先清零。",
        ],
    )

    add_paragraph(doc, "5.2 改进建议", style="Heading 2")
    add_bullets(
        doc,
        [
            "P0：立即修复改密后旧 token 仍可用、scoped 运营看板全局聚合、scoped 通知越权投递三项问题。",
            "P1：统一 Web 401 跳转与登录态恢复逻辑，移除生产环境中的模拟回执入口，并修复协同角色搜人权限不一致问题。",
            "P2：补齐小程序首页与历史列表的分页、加载更多和总数口径，避免用户只看到第一页数据。",
            "运维侧应立即更新互测和交付文档中的账号口径，发放当前有效的管理员、教师和学生验收账号，避免继续依赖已失效的共享口令。",
            "在下一轮正式交付测试前，建议重新执行一轮以当前 HEAD 为基线的后端全量 pytest、Web build 和 Miniapp build，并补一轮 10.10.0.13 的真实教师账号、真实学生账号和真实微信授权联调。",
        ],
    )

    return finalize(doc, output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build project test report DOCX.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(build_doc(args.output))


if __name__ == "__main__":
    main()
