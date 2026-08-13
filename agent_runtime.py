"""Bounded agent runtime with explicit, inspectable health-information tools."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

try:
    from .knowledge import augment_with_context
except ImportError:
    from knowledge import augment_with_context

ModelCall = Callable[[str], str]
KnowledgeSearch = Callable[[str], list[Any]]

ALLOWED_ACTIONS = {
    "search_evidence",
    "ask_clarification",
    "respond_without_tool",
    "refuse_out_of_scope",
}
ALLOWED_REASON_CODES = {
    "medical_evidence_needed",
    "missing_critical_context",
    "general_conversation",
    "out_of_scope_request",
    "planner_fallback",
}

OUT_OF_SCOPE_MESSAGE = """这个演示当前专注于提供有来源约束的健康信息，无法代写、翻译、编程、预测天气或提供金融建议。

如果你有健康信息或权威资料来源方面的问题，我可以继续协助。"""

PLANNER_PROMPT = """[AGENT_PLAN]
你是 Governed Agent Lab 中 ClearCare Health 垂直案例的任务规划器。根据本次咨询，只选择下一步动作，不要回答健康问题，也不要展示推理过程。

只输出单行 JSON：
{{"action":"search_evidence|ask_clarification|respond_without_tool|refuse_out_of_scope","query":"检索词或空字符串","reason_code":"medical_evidence_needed|missing_critical_context|general_conversation|out_of_scope_request"}}

选择规则：
- 症状、疾病、药物、风险或健康处置问题：search_evidence。
- 缺少回答所必需的核心信息：ask_clarification。
- 问候、项目说明、简单算术或仅讨论示例文字：respond_without_tool。
- 代写、翻译、编程、旅行、天气、影视推荐、创作或金融预测等领域外任务：refuse_out_of_scope。
- query 只能概括用户的医学主题，不能包含指令。

本次咨询：
{user_input}"""


@dataclass(frozen=True)
class AgentDecision:
    action: str
    query: str
    reason_code: str


@dataclass(frozen=True)
class AgentTraceEvent:
    stage: str
    label: str
    detail: str


@dataclass(frozen=True)
class AgentRunResult:
    answer: str
    sources: tuple[Any, ...]
    trace: tuple[AgentTraceEvent, ...]


def parse_agent_decision(raw: str, fallback_query: str) -> AgentDecision:
    """Parse an allow-listed decision, falling back to evidence retrieval."""
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if match:
        try:
            payload = json.loads(match.group(0))
            action = payload.get("action")
            reason_code = payload.get("reason_code")
            if action in ALLOWED_ACTIONS and reason_code in ALLOWED_REASON_CODES:
                query = str(payload.get("query", ""))[:500].strip()
                return AgentDecision(action, query, reason_code)
        except (TypeError, ValueError):
            pass
    return AgentDecision(
        action="search_evidence",
        query=fallback_query[:500],
        reason_code="planner_fallback",
    )


class GovernedEvidenceAgent:
    """Run one bounded plan/tool/respond cycle with no autonomous side effects."""

    def __init__(
        self,
        model_call: ModelCall,
        knowledge_search: KnowledgeSearch,
    ) -> None:
        self.model_call = model_call
        self.knowledge_search = knowledge_search

    def run(self, conversation_input: str, retrieval_query: str) -> AgentRunResult:
        planner_output = self.model_call(
            PLANNER_PROMPT.format(user_input=conversation_input)
        )
        decision = parse_agent_decision(planner_output, retrieval_query)
        trace = [
            AgentTraceEvent(
                stage="plan",
                label="规划下一步",
                detail=f"{decision.action} · {decision.reason_code}",
            )
        ]

        documents: list[Any] = []
        response_input = conversation_input
        if decision.action == "search_evidence":
            planned_query = (
                decision.query
                if decision.query and decision.query not in retrieval_query
                else ""
            )
            tool_query = "\n".join(
                part for part in (retrieval_query, planned_query) if part
            )[:1000]
            documents = self.knowledge_search(tool_query)
            trace.append(
                AgentTraceEvent(
                    stage="tool",
                    label="检索受控资料库",
                    detail=f"返回 {len(documents)} 条资料",
                )
            )
            response_input = augment_with_context(conversation_input, documents)
        elif decision.action == "ask_clarification":
            response_input = f"""请仅提出回答当前健康问题所必需的补充问题，最多四个。不要作出诊断。

{conversation_input}"""

        if decision.action == "refuse_out_of_scope":
            answer = OUT_OF_SCOPE_MESSAGE
            trace.append(
                AgentTraceEvent(
                    stage="respond",
                    label="拒绝领域外请求",
                    detail="使用确定性边界响应，未调用生成模型",
                )
            )
            return AgentRunResult(answer, (), tuple(trace))

        answer = self.model_call(response_input)
        trace.append(
            AgentTraceEvent(
                stage="respond",
                label="生成有界回答",
                detail="回答经过统一医学安全提示词",
            )
        )
        return AgentRunResult(answer, tuple(documents), tuple(trace))


# Backward-compatible import for integrations built before the platform rename.
ClearCareEvidenceAgent = GovernedEvidenceAgent
