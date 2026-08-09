"""Interchangeable chat model providers.

The web layer depends only on :class:`ChatModel`, so changing providers does
not require route or template changes. Heavy ML and API SDKs are imported only
when their provider is selected.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Protocol


MEDICAL_SYSTEM_PROMPT = """你是专业、审慎的医疗健康信息助手，而不是医生。
你只能提供一般性健康信息，不能作出诊断、开具处方或保证治疗效果。
先给出简明结论和用户可以采取的下一步，不要展示内部推理过程，也不要使用“我们来逐步分析”等措辞。
使用清晰的 Markdown，最多包含以下小节：### 初步判断、### 需要及时就医的情况、### 现在可以做什么、### 需要补充的信息。小节之间留空行，列表使用短句。
仅在确有必要时列出危险信号；不要用危险信号淹没普通问题。信息不足时提出不超过四个最重要的澄清问题。
不要编造医学事实、检查结果、药物剂量或资料来源。回答控制在 700 个汉字以内，并以完整句子结束。
最后单独写：以上信息仅供健康科普参考，不能替代医生的面诊与诊断。"""


class ChatModel(Protocol):
    """Minimal interface shared by local and hosted chat models."""

    def generate(self, user_input: str) -> str: ...


class OpenAIChatModel:
    """Hosted OpenAI model using the Responses API."""

    def __init__(
        self,
        model: str = "gpt-5.6-luna",
        client: Any | None = None,
    ) -> None:
        if client is None:
            from openai import OpenAI

            client = OpenAI()
        self.client = client
        self.model = model

    def generate(self, user_input: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            instructions=MEDICAL_SYSTEM_PROMPT,
            input=user_input,
            store=False,
        )
        output_text = response.output_text.strip()
        if not output_text:
            raise RuntimeError("The model returned an empty response")
        return output_text


class QwenLocalChatModel:
    """Locally hosted, MLX-quantized Qwen model for Apple Silicon."""

    def __init__(
        self,
        model_name: str = "mlx-community/Qwen3-4B-Instruct-2507-4bit",
    ) -> None:
        from mlx_lm import generate, load

        self.model_name = model_name
        self.model, self.tokenizer = load(model_name)
        self._generate = generate

    def generate(self, user_input: str) -> str:
        messages = [
            {"role": "system", "content": MEDICAL_SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        answer = self._generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=int(os.getenv("GPT2_MCC_MAX_NEW_TOKENS", "1024")),
            verbose=False,
        )
        if not answer.strip():
            raise RuntimeError("The model returned an empty response")
        return answer.strip()


class LegacyGPT2ChatModel:
    """Compatibility adapter for the repository's original GPT-2 model."""

    def generate(self, user_input: str) -> str:
        from flask_predict import model_predict

        return model_predict(user_input)


def create_chat_model(provider: str | None = None) -> ChatModel:
    """Create a provider from explicit input or environment configuration."""
    provider_name = (
        provider or os.getenv("GPT2_MCC_MODEL_PROVIDER", "qwen-local")
    ).strip().lower()

    if provider_name == "openai":
        return OpenAIChatModel(
            model=os.getenv("GPT2_MCC_OPENAI_MODEL", "gpt-5.6-luna")
        )
    if provider_name in {"qwen", "qwen-local"}:
        return QwenLocalChatModel(
            model_name=os.getenv(
                "GPT2_MCC_QWEN_MODEL",
                "mlx-community/Qwen3-4B-Instruct-2507-4bit",
            )
        )
    if provider_name in {"gpt2", "legacy-gpt2"}:
        return LegacyGPT2ChatModel()

    supported = "openai, qwen-local, legacy-gpt2"
    raise ValueError(
        f"Unknown model provider {provider_name!r}. Supported providers: {supported}"
    )


@lru_cache(maxsize=4)
def get_chat_model(provider: str) -> ChatModel:
    """Reuse an explicitly selected provider across requests."""
    return create_chat_model(provider)


@lru_cache(maxsize=1)
def get_default_chat_model() -> ChatModel:
    """Reuse the selected model instead of loading it for every request."""
    return create_chat_model()
