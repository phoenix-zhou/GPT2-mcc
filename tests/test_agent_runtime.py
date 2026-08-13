import json

from agent_runtime import (
    ClearCareEvidenceAgent,
    GovernedEvidenceAgent,
    parse_agent_decision,
)
from knowledge import KnowledgeDocument


def decision(action, query="", reason_code="general_conversation"):
    return json.dumps(
        {"action": action, "query": query, "reason_code": reason_code},
        ensure_ascii=False,
    )


def test_legacy_agent_name_is_a_compatible_alias():
    assert ClearCareEvidenceAgent is GovernedEvidenceAgent


def test_agent_selects_evidence_tool_and_passes_results_to_responder():
    calls = []
    queries = []
    document = KnowledgeDocument(
        title="可信资料",
        content="资料正文",
        source_url="https://example.test/source",
        keywords=("测试",),
    )

    def model_call(prompt):
        calls.append(prompt)
        if prompt.startswith("[AGENT_PLAN]"):
            return decision(
                "search_evidence",
                query="腹泻 补水",
                reason_code="medical_evidence_needed",
            )
        return "有依据的回答"

    agent = GovernedEvidenceAgent(
        model_call=model_call,
        knowledge_search=lambda query: queries.append(query) or [document],
    )
    result = agent.run("我有腹泻", "我有腹泻")

    assert queries == ["我有腹泻\n腹泻 补水"]
    assert "资料正文" in calls[-1]
    assert result.answer == "有依据的回答"
    assert result.sources == (document,)
    assert [event.stage for event in result.trace] == ["plan", "tool", "respond"]


def test_agent_can_request_clarification_without_calling_tool():
    prompts = []

    def model_call(prompt):
        prompts.append(prompt)
        if prompt.startswith("[AGENT_PLAN]"):
            return decision(
                "ask_clarification",
                reason_code="missing_critical_context",
            )
        return "请补充持续时间。"

    def unexpected_search(query):
        raise AssertionError(f"unexpected tool call: {query}")

    agent = GovernedEvidenceAgent(model_call, unexpected_search)
    result = agent.run("我不舒服", "我不舒服")

    assert "最多四个" in prompts[-1]
    assert result.sources == ()
    assert [event.stage for event in result.trace] == ["plan", "respond"]


def test_agent_refuses_out_of_scope_without_a_second_model_call():
    prompts = []

    def model_call(prompt):
        prompts.append(prompt)
        return decision(
            "refuse_out_of_scope",
            reason_code="out_of_scope_request",
        )

    def unexpected_search(query):
        raise AssertionError(f"unexpected tool call: {query}")

    result = GovernedEvidenceAgent(model_call, unexpected_search).run(
        "帮我写一封求职邮件",
        "帮我写一封求职邮件",
    )

    assert len(prompts) == 1
    assert "专注于提供有来源约束的健康信息" in result.answer
    assert result.sources == ()
    assert [event.stage for event in result.trace] == ["plan", "respond"]


def test_invalid_planner_output_falls_back_to_bounded_search():
    calls = []
    queries = []

    def model_call(prompt):
        calls.append(prompt)
        return "not json" if len(calls) == 1 else "安全回答"

    result = GovernedEvidenceAgent(
        model_call,
        lambda query: queries.append(query) or [],
    ).run("当前问题", "最近历史\n当前问题")

    assert queries == ["最近历史\n当前问题"]
    assert "planner_fallback" in result.trace[0].detail


def test_parser_rejects_unregistered_actions():
    raw = decision("delete_database", reason_code="general_conversation")

    parsed = parse_agent_decision(raw, "安全回退检索")

    assert parsed.action == "search_evidence"
    assert parsed.query == "安全回退检索"
