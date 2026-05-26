from app.report import transcript_pdf

RUC_TRANSCRIPT_TEXT = """
学 生 成 绩 单
学号： 2024201540 层次：本科生 院系：信息学院
姓名： 张念昊 学制：4 专业：理科试验班
课程名称 学分 成绩 学分绩点 课程名称 学分 成绩 学分绩点
2
0
2
4
-
2
0
2
5
学
年
秋
季
学
期
离
散
数
学
A
3.0 90 12.0
健
美
1.0 77 2.7
职
业
生
涯
规
划
（
理
论
） 1.0 P 1.0
2
0
2
5
-
2
0
2
6
学
年
春
季
学
期
思
政
实
践
课 2.0 P 2.0
高
等
数
学
Ⅱ
5.0 90 20.0
总取得学分： 87 总学分绩点： 314.7 平均学分绩点(GPA)： 3.85
"""

RUC_TRANSCRIPT_TEXT_WITH_TEACHERS = """
学号：2024202721  姓名：曾翎一  院系：信息学院  专业：理科试验班  年级：2024
课程名称 教师 课程性质 学分 平时成绩 期中成绩 期末成绩 最终成绩 学分绩点 成绩标志
游泳 吴升扣 公共体育 1 90 90 4
军训 孔玉姝 科研与实践
环节 2 A A 8
新生研讨课 杨继东 新生研讨课 1 P P 1
微积分CⅠ 刘双 公共数学 3 100 98 100 99 12
军事理论
刘硕扬,周
晓辉,孔玉
姝,孙琳,
张国凤,程
万昕
军事课 2 A A 8
数据与信息技术基础 李刚 数据与信息
技术平台课 2 90 91 90 8
思想道德与法治 单文鹏 思想政治理
论课 3 93 94 93 12
大学英语综合B 杨扬 公共外语 2 92 83 88 7.4
网页设计与编程 曹巍 数据与信息
技术平台课 2 91 84 88 7.4
政治经济学原理B 赵峰 部类共同 3 90 80 84 9.9
经济学原理I 赵勇 部类共同 3 89 89 89 11.1
美育实践 楚奇 美育课程 1 P P 1
2024-2025学年秋季学期: 已取得总学分:25 总学分绩点:89.8 平均学分绩点:3.82
会计学 宋建波 部类共同 3 100 84 92 12
乒乓球 刘圣文 公共体育 1 88 88 3.7
当代中国经济 张培丽 个性化选修 3 91 91 91 12
综合设计 陈晋川 科研与实践
环节 2 92 92 8
实用算法与程序设计 孙辉 公共选修课 2 99 80 90 8
中国近现代史纲要 杜家丞 思想政治理
论课 3 86 87 87 11.1
微积分CⅡ 张倩伟 公共数学 3 100 100 85 93 12
学术英语视听说 杨扬
公共外语（
拓展类课
程）
2 92 93 93 8
中国特色社会主义政治
经济学A 赵峰 部类共同 3 96 88 91 12
职业生涯规划（理论） 王桢 职业生涯规
划 1 P P 1
经济学原理II 郭杰 部类共同 3 100 84 90 12
大学生心理健康 袁世琨,金
霞
心理健康教
育 2 P P 2
2024-2025学年春季学期: 已取得总学分:28 总学分绩点:101.8 平均学分绩点:3.95
概率论与数理统计 李亚平 专业核心课 4 90 80 84 13.2
马克思主义基本原理 付天睿 思想政治理
论课 3 96 89 93 12
数据科学导论 范举 专业核心课 3 86 91 88 11.1
计算机系统基础Ⅰ 张延松,柴
云鹏 专业核心课 3 90 65 83 9.9
高等代数Ⅰ 戚发全 部类共同 4 97 73 85 13.2
英语演讲 伍阳艳 公共外语 2 94 88 91 8
数据结构与算法Ⅰ 蒋洪迅 专业核心课 4 90 85 88 14.8
习近平新时代中国特色
社会主义思想概论 杜家丞 思想政治理
论课 3 87 92 90 12
网络空间安全引论 梁彬,黄建
军 专业核心课 2 95 80 88 7.4
程序设计 何玥 部类基础 4 100 83 93 16
2025-2026学年秋季学期: 已取得总学分:32 总学分绩点:117.6 平均学分绩点:3.68
各学期汇总: 已取得总学分:85 总学分绩点:309.2 平均学分绩点:3.80
"""


def test_ruc_transcript_text_layer_is_parsed_into_review_candidates(monkeypatch) -> None:
    monkeypatch.setattr(
        transcript_pdf,
        "_extract_pdf_text",
        lambda _pdf_bytes: (RUC_TRANSCRIPT_TEXT, []),
    )

    analysis = transcript_pdf.analyze_transcript_pdf(
        b"%PDF-1.4",
        student_no="2024201540",
        student_name="张念昊",
    )

    assert [candidate.course_name for candidate in analysis.candidate_courses] == [
        "离散数学A",
        "健美",
        "职业生涯规划（理论）",
        "思政实践课",
        "高等数学Ⅱ",
    ]
    assert analysis.candidate_courses[0].credits == 3.0
    assert analysis.candidate_courses[0].score == 90.0
    assert analysis.candidate_courses[0].term_code == "2024-FALL"
    assert analysis.candidate_courses[2].raw_text == "职业生涯规划（理论） 学分 1.0 成绩 P 绩点 1.0"
    assert analysis.candidate_courses[2].grade_letter == "P"
    assert analysis.candidate_courses[2].pass_flag is True
    assert analysis.candidate_courses[-1].term_code == "2025-SPRING"
    assert any("识别 5 条疑似课程记录" in warning for warning in analysis.data_warnings)


def test_generic_course_code_parser_still_handles_labeled_lines(monkeypatch) -> None:
    monkeypatch.setattr(
        transcript_pdf,
        "_extract_pdf_text",
        lambda _pdf_bytes: (
            "2025-FALL\nBISYMS0012 网络空间安全引论 学分 2.0 成绩 86",
            [],
        ),
    )

    analysis = transcript_pdf.analyze_transcript_pdf(
        b"%PDF-1.4",
        student_no="A100001",
        student_name="测试学生",
    )

    assert len(analysis.candidate_courses) == 1
    candidate = analysis.candidate_courses[0]
    assert candidate.course_code == "BISYMS0012"
    assert candidate.course_name == "网络空间安全引论"
    assert candidate.credits == 2.0
    assert candidate.score == 86.0
    assert candidate.pass_flag is True


def test_ruc_transcript_with_teachers_and_course_property_columns_is_parsed(monkeypatch) -> None:
    monkeypatch.setattr(
        transcript_pdf,
        "_extract_pdf_text",
        lambda _pdf_bytes: (RUC_TRANSCRIPT_TEXT_WITH_TEACHERS, []),
    )

    analysis = transcript_pdf.analyze_transcript_pdf(
        b"%PDF-1.4",
        student_no="2024202721",
        student_name="曾翎一",
    )

    names = [candidate.course_name for candidate in analysis.candidate_courses]
    assert len(analysis.candidate_courses) == 34
    assert names[:5] == ["游泳", "军训", "新生研讨课", "微积分CⅠ", "军事理论"]
    assert "学术英语视听说" in names
    assert "中国特色社会主义政治经济学A" in names
    assert "习近平新时代中国特色社会主义思想概论" in names
    assert analysis.candidate_courses[0].term_code == "2024-FALL"
    assert analysis.candidate_courses[11].term_code == "2024-FALL"
    assert analysis.candidate_courses[12].term_code == "2024-SPRING"
    assert analysis.candidate_courses[-1].term_code == "2025-FALL"
    assert analysis.candidate_courses[1].grade_letter == "A"
    assert analysis.candidate_courses[2].grade_letter == "P"
    assert analysis.candidate_courses[3].score == 99.0
    assert any("识别 34 条疑似课程记录" in warning for warning in analysis.data_warnings)
