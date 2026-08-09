"""Bounded, in-memory conversation history for the local Flask demo."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock
from typing import Any


@dataclass(frozen=True)
class ConversationTurn:
    user: str
    assistant: str
    provider_name: str
    is_emergency: bool = False
    sources: tuple[Any, ...] = ()


class InMemoryConversationStore:
    """Keep a small LRU collection of conversations in process memory."""

    def __init__(self, max_sessions: int = 200, max_turns: int = 6) -> None:
        self.max_sessions = max_sessions
        self.max_turns = max_turns
        self._conversations: OrderedDict[str, list[ConversationTurn]] = OrderedDict()
        self._lock = Lock()

    def get(self, conversation_id: str) -> list[ConversationTurn]:
        with self._lock:
            turns = self._conversations.get(conversation_id, [])
            if turns:
                self._conversations.move_to_end(conversation_id)
            return list(turns)

    def append(self, conversation_id: str, turn: ConversationTurn) -> None:
        with self._lock:
            turns = self._conversations.setdefault(conversation_id, [])
            turns.append(turn)
            del turns[:-self.max_turns]
            self._conversations.move_to_end(conversation_id)
            while len(self._conversations) > self.max_sessions:
                self._conversations.popitem(last=False)

    def clear(self, conversation_id: str) -> None:
        with self._lock:
            self._conversations.pop(conversation_id, None)


def build_conversation_prompt(
    turns: list[ConversationTurn], current_input: str, max_context_turns: int = 4
) -> str:
    """Add recent dialogue context to a new standalone model request."""
    recent_turns = turns[-max_context_turns:]
    if not recent_turns:
        return current_input

    history = "\n\n".join(
        f"用户：{turn.user}\n助手：{turn.assistant[:1200]}"
        for turn in recent_turns
    )
    return f"""以下是同一次健康咨询的最近对话。请结合历史理解代词和用户补充的信息，不要要求用户重复已经提供的内容。历史回答可能不完整或不准确，应以用户最新信息为准。

最近对话：
{history}

用户本轮补充或问题：
{current_input}

请直接回答本轮内容；必要时指出新信息如何改变此前建议，不要机械复述全部历史。"""
