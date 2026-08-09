from conversation import (
    ConversationTurn,
    InMemoryConversationStore,
    build_conversation_prompt,
)


def make_turn(number: int) -> ConversationTurn:
    return ConversationTurn(
        user=f"用户问题 {number}",
        assistant=f"助手回答 {number}",
        provider_name="测试模型",
    )


def test_store_keeps_only_the_latest_turns():
    store = InMemoryConversationStore(max_turns=2)
    for number in range(3):
        store.append("session", make_turn(number))

    turns = store.get("session")

    assert [turn.user for turn in turns] == ["用户问题 1", "用户问题 2"]


def test_prompt_uses_only_recent_context_and_marks_current_input():
    turns = [make_turn(number) for number in range(5)]

    prompt = build_conversation_prompt(turns, "这是最新补充", max_context_turns=2)

    assert "用户问题 2" not in prompt
    assert "用户问题 3" in prompt
    assert "助手回答 4" in prompt
    assert "用户本轮补充或问题：\n这是最新补充" in prompt


def test_prompt_does_not_wrap_first_turn():
    assert build_conversation_prompt([], "首次问题") == "首次问题"


def test_prompt_limits_each_historical_answer():
    long_turn = ConversationTurn(
        user="旧问题",
        assistant="很长的回答" * 1000,
        provider_name="测试模型",
    )

    prompt = build_conversation_prompt([long_turn], "最新问题")

    assert len(prompt) < 2000
    assert prompt.endswith("不要机械复述全部历史。")
