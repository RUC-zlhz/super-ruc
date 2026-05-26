from scripts.seed import workflow_templates


def _templates_by_code():
    return {template.code: template for template in workflow_templates._TEMPLATES}


def test_official_workflow_template_specs_are_complete() -> None:
    templates = _templates_by_code()

    party = templates["PARTY_DEVELOPMENT_OFFICIAL_V2"]
    assert party.is_active is True
    assert party.name == "发展党员工作程序（官方29步）"
    assert len(party.nodes) == 29
    assert party.nodes[0].name == "教育引导"
    assert party.nodes[-1].name == "存档"
    assert party.nodes[-1].is_terminal is True
    assert {node.stage_group for node in party.nodes} == {
        "ACTIVIST_CONFIRMATION",
        "DEVELOPMENT_TARGET",
        "PROBATION_ACCEPTANCE",
        "PROBATION_EDUCATION_FULL_MEMBER",
    }

    youth = templates["YOUTH_LEAGUE_DEVELOPMENT_OFFICIAL_V2"]
    youth_node_names = [node.name for node in youth.nodes]
    assert youth.is_active is True
    assert youth.name == "发展团员工作流程（官方15步）"
    assert len(youth.nodes) == 15
    assert youth.nodes[0].name == "提交入团申请书"
    assert youth.nodes[-1].name == "档案管理"
    assert youth.nodes[-1].is_terminal is True
    assert "推优入党" not in youth_node_names
    assert "毕业团员转出" not in youth_node_names
    assert {node.stage_group for node in youth.nodes} == {
        "APPLY",
        "ACTIVIST_CONFIRMATION",
        "ACTIVIST_EDUCATION",
        "DEVELOPMENT_TARGET",
        "NEW_MEMBER_ACCEPTANCE",
    }


def test_legacy_and_membership_templates_are_split() -> None:
    templates = _templates_by_code()

    assert templates["PARTY_DEVELOPMENT_V1"].is_active is False
    assert templates["YOUTH_LEAGUE_V1"].is_active is False

    membership = templates["YOUTH_LEAGUE_MEMBERSHIP_MANAGEMENT_V1"]
    assert membership.is_active is True
    assert [node.name for node in membership.nodes] == ["推优入党", "毕业团员转出"]
