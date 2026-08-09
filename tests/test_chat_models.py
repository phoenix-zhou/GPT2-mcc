import sys
from types import SimpleNamespace

import pytest

from chat_models import OpenAIChatModel, QwenLocalChatModel, create_chat_model


class FakeResponses:
    def __init__(self, output_text: str = "测试回答") -> None:
        self.output_text = output_text
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(output_text=self.output_text)


def test_openai_provider_uses_safe_responses_request():
    responses = FakeResponses()
    client = SimpleNamespace(responses=responses)
    provider = OpenAIChatModel(model="test-model", client=client)

    assert provider.generate("我头痛") == "测试回答"
    assert responses.kwargs["model"] == "test-model"
    assert responses.kwargs["input"] == "我头痛"
    assert responses.kwargs["store"] is False
    assert "不能作出诊断" in responses.kwargs["instructions"]


def test_openai_provider_rejects_empty_output():
    client = SimpleNamespace(responses=FakeResponses("  "))
    provider = OpenAIChatModel(client=client)

    with pytest.raises(RuntimeError, match="empty response"):
        provider.generate("测试")


def test_unknown_provider_has_actionable_error():
    with pytest.raises(ValueError, match="Supported providers"):
        create_chat_model("unknown")


def test_local_qwen_is_the_default(monkeypatch):
    monkeypatch.delenv("GPT2_MCC_MODEL_PROVIDER", raising=False)

    class FakeQwen:
        def __init__(self, model_name):
            self.model_name = model_name

    monkeypatch.setattr("chat_models.QwenLocalChatModel", FakeQwen)

    provider = create_chat_model()

    assert provider.model_name == "mlx-community/Qwen3-4B-Instruct-2507-4bit"


def test_mlx_qwen_provider_applies_chat_template(monkeypatch):
    calls = {}

    class FakeTokenizer:
        def apply_chat_template(self, messages, **kwargs):
            calls["messages"] = messages
            calls["template_kwargs"] = kwargs
            return "rendered prompt"

    def fake_load(model_name):
        calls["model_name"] = model_name
        return "model", FakeTokenizer()

    def fake_generate(model, tokenizer, **kwargs):
        calls["generate_kwargs"] = kwargs
        return " 本地回答 "

    monkeypatch.setitem(
        sys.modules,
        "mlx_lm",
        SimpleNamespace(load=fake_load, generate=fake_generate),
    )
    provider = QwenLocalChatModel("local-test-model")

    assert provider.generate("你好") == "本地回答"
    assert calls["model_name"] == "local-test-model"
    assert calls["messages"][0]["role"] == "system"
    assert calls["messages"][1] == {"role": "user", "content": "你好"}
    assert calls["template_kwargs"]["tokenize"] is False
    assert calls["generate_kwargs"]["prompt"] == "rendered prompt"
