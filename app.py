"""Flask application entry point for the medical chatbot demo."""

from __future__ import annotations

import logging
from collections.abc import Callable

from flask import Flask, current_app, render_template, request

Predictor = Callable[[str], str]


def _default_predictor(text: str) -> str:
    """Load the configured model provider on the first prediction request."""
    try:
        try:
            from .chat_models import get_default_chat_model
        except ImportError:
            from chat_models import get_default_chat_model

        return get_default_chat_model().generate(text)
    except Exception as exc:
        # Provider SDKs expose different exception hierarchies. Normalize them
        # at this boundary so the web layer can return a controlled 503 page.
        raise RuntimeError("Model provider request failed") from exc


def _default_cloud_predictor(text: str) -> str:
    """Use OpenAI only for an explicitly approved cloud-enhanced request."""
    try:
        try:
            from .chat_models import get_chat_model
        except ImportError:
            from chat_models import get_chat_model

        return get_chat_model("openai").generate(text)
    except Exception as exc:
        raise RuntimeError("Cloud model provider request failed") from exc


def create_app(
    predictor: Predictor | None = None,
    cloud_predictor: Predictor | None = None,
    safety_router=None,
    knowledge_base=None,
) -> Flask:
    """Create the web application, optionally injecting a test predictor."""
    app = Flask(__name__)
    app.config.from_mapping(
        MAX_INPUT_LENGTH=1000,
        CLOUD_ENHANCEMENT_ENABLED=False,
    )
    app.config.from_prefixed_env(prefix="GPT2_MCC")
    app.extensions["predictor"] = predictor or _default_predictor
    app.extensions["cloud_predictor"] = (
        cloud_predictor or _default_cloud_predictor
    )
    if safety_router is None:
        try:
            from .safety import EmergencyRiskRouter
        except ImportError:
            from safety import EmergencyRiskRouter

        safety_router = EmergencyRiskRouter()
    if knowledge_base is None:
        try:
            from .knowledge import LocalKnowledgeBase
        except ImportError:
            from knowledge import LocalKnowledgeBase

        knowledge_base = LocalKnowledgeBase()
    app.extensions["safety_router"] = safety_router
    app.extensions["knowledge_base"] = knowledge_base

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/ask")
    def ask():
        user_input = request.form.get("user_input", "").strip()
        if not user_input:
            return render_template("index.html", error="请输入咨询内容。"), 400

        max_length = int(current_app.config["MAX_INPUT_LENGTH"])
        if len(user_input) > max_length:
            return render_template(
                "index.html",
                user_input=user_input,
                error=f"输入内容不能超过 {max_length} 个字符。",
            ), 400

        use_cloud = request.form.get("use_cloud") == "on"
        assessment = current_app.extensions["safety_router"].assess(user_input)
        if assessment.is_emergency:
            try:
                from .safety import EMERGENCY_MESSAGE
            except ImportError:
                from safety import EMERGENCY_MESSAGE

            return render_template(
                "index.html",
                user_input=user_input,
                answer=EMERGENCY_MESSAGE,
                provider_name="紧急风险分流（未调用生成模型）",
                is_emergency=True,
            )

        if use_cloud and not current_app.config["CLOUD_ENHANCEMENT_ENABLED"]:
            return render_template(
                "index.html",
                user_input=user_input,
                error="云端增强未启用，因此没有发送数据或产生 API 费用。",
            ), 403

        try:
            from .knowledge import augment_with_context
        except ImportError:
            from knowledge import augment_with_context

        documents = current_app.extensions["knowledge_base"].search(user_input)
        model_input = augment_with_context(user_input, documents)
        provider_name = "OpenAI GPT" if use_cloud else "本地 Qwen"
        selected_predictor = (
            current_app.extensions["cloud_predictor"]
            if use_cloud
            else current_app.extensions["predictor"]
        )

        try:
            answer = selected_predictor(model_input)
        except (FileNotFoundError, OSError, RuntimeError):
            current_app.logger.exception("Model prediction failed")
            return render_template(
                "index.html",
                user_input=user_input,
                error="模型当前不可用，请确认模型权重和运行环境已正确配置。",
            ), 503

        return render_template(
            "index.html",
            user_input=user_input,
            answer=answer,
            provider_name=provider_name,
            sources=documents,
        )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run()
