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
