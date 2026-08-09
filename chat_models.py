"""Interchangeable chat model providers.

The web layer depends only on :class:`ChatModel`, so changing providers does
not require route or template changes. Heavy ML and API SDKs are imported only
when their provider is selected.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Protocol


MEDICAL_SYSTEM_PROMPT = """你是医疗健康信息助手，而不是医生。
你只能提供一般性的健康信息，不能作出诊断、开具处方或保证治疗效果。
回答前先识别是否存在危及生命的危险信号；如存在，应明确建议用户立即联系当地急救服务或前往急诊。
信息不足时先提出必要的澄清问题。说明不确定性，并建议用户向有资质的医疗专业人员求助。
不要编造医学事实、检查结果、药物剂量或资料来源。"""


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
            max_tokens=int(os.getenv("GPT2_MCC_MAX_NEW_TOKENS", "512")),
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
