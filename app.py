"""Flask entry point for the ClearCare Health reference vertical."""

from __future__ import annotations

import logging
import secrets
import uuid
from collections.abc import Callable

import bleach
import markdown
from flask import (
    Flask,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from markupsafe import Markup, escape

try:
    from .settings import get_setting
except ImportError:
    from settings import get_setting

Predictor = Callable[[str], str]

ALLOWED_MARKDOWN_TAGS = {
    "a", "blockquote", "br", "code", "em", "h2", "h3", "hr", "li",
    "ol", "p", "pre", "strong", "ul",
}


def render_markdown(text: str) -> Markup:
    """Render model Markdown while removing unsafe HTML and URL schemes."""
    rendered = markdown.markdown(
        str(escape(text)),
        extensions=["sane_lists", "nl2br"],
    )
    cleaned = bleach.clean(
        rendered,
        tags=ALLOWED_MARKDOWN_TAGS,
        attributes={"a": ["href", "title"]},
        protocols={"http", "https"},
        strip=True,
    )
    return Markup(cleaned)


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
    conversation_store=None,
) -> Flask:
    """Create the web application, optionally injecting a test predictor."""
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=get_setting("SECRET_KEY") or secrets.token_hex(32),
        MAX_INPUT_LENGTH=1000,
        CLOUD_ENHANCEMENT_ENABLED=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    app.config.from_prefixed_env(prefix="GPT2_MCC")
    app.config.from_prefixed_env(prefix="CLEARCARE")
    app.config.from_prefixed_env(prefix="GOVERNED_AGENT")
    app.jinja_env.filters["render_markdown"] = render_markdown
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
    if conversation_store is None:
        try:
            from .conversation import InMemoryConversationStore
        except ImportError:
            from conversation import InMemoryConversationStore

        conversation_store = InMemoryConversationStore()
    app.extensions["conversation_store"] = conversation_store

    def get_conversation_id() -> str:
        conversation_id = session.get("conversation_id")
        if not conversation_id:
            conversation_id = uuid.uuid4().hex
            session["conversation_id"] = conversation_id
        return conversation_id

    def page_context(**extra):
        conversation_id = get_conversation_id()
        return {
            "conversation": current_app.extensions["conversation_store"].get(
                conversation_id
            ),
            **extra,
        }

    @app.get("/")
    def index():
        return render_template("index.html", **page_context())

    @app.post("/conversation/reset")
    def reset_conversation():
        conversation_id = get_conversation_id()
        current_app.extensions["conversation_store"].clear(conversation_id)
        session["conversation_id"] = uuid.uuid4().hex
        return redirect(url_for("index"))

    @app.post("/ask")
    def ask():
        conversation_id = get_conversation_id()
        conversation_store = current_app.extensions["conversation_store"]
        history = conversation_store.get(conversation_id)
        user_input = request.form.get("user_input", "").strip()
        if not user_input:
            return render_template(
                "index.html", **page_context(error="请输入咨询内容。")
            ), 400

        max_length = int(current_app.config["MAX_INPUT_LENGTH"])
        if len(user_input) > max_length:
            return render_template(
                "index.html",
                **page_context(
                    user_input=user_input,
                    error=f"输入内容不能超过 {max_length} 个字符。",
                ),
            ), 400

        use_cloud = request.form.get("use_cloud") == "on"
        assessment = current_app.extensions["safety_router"].assess(user_input)
        if assessment.is_emergency:
            try:
                from .safety import EMERGENCY_MESSAGE
            except ImportError:
                from safety import EMERGENCY_MESSAGE

            try:
                from .conversation import ConversationTurn
            except ImportError:
                from conversation import ConversationTurn

            conversation_store.append(
                conversation_id,
                ConversationTurn(
                    user=user_input,
                    assistant=EMERGENCY_MESSAGE,
                    provider_name="紧急风险分流（未调用生成模型）",
                    is_emergency=True,
                ),
            )
            return render_template("index.html", **page_context())

        if use_cloud and not current_app.config["CLOUD_ENHANCEMENT_ENABLED"]:
            return render_template(
                "index.html",
                **page_context(
                    user_input=user_input,
                    error="云端增强未启用，因此没有发送数据或产生 API 费用。",
                ),
            ), 403

        retrieval_query = "\n".join(
            [turn.user for turn in history[-2:]] + [user_input]
        )
        try:
            from .conversation import ConversationTurn, build_conversation_prompt
        except ImportError:
            from conversation import ConversationTurn, build_conversation_prompt

        model_input = build_conversation_prompt(history, user_input)
        provider_name = "OpenAI GPT · Agent" if use_cloud else "本地 Qwen · Agent"
        selected_predictor = (
            current_app.extensions["cloud_predictor"]
            if use_cloud
            else current_app.extensions["predictor"]
        )

        try:
            try:
                from .agent_runtime import GovernedEvidenceAgent
            except ImportError:
                from agent_runtime import GovernedEvidenceAgent

            agent = GovernedEvidenceAgent(
                model_call=selected_predictor,
                knowledge_search=current_app.extensions["knowledge_base"].search,
            )
            result = agent.run(model_input, retrieval_query)
        except (FileNotFoundError, OSError, RuntimeError):
            current_app.logger.exception("Model prediction failed")
            return render_template(
                "index.html",
                **page_context(
                    user_input=user_input,
                    error="模型当前不可用，请确认模型权重和运行环境已正确配置。",
                ),
            ), 503

        conversation_store.append(
            conversation_id,
            ConversationTurn(
                user=user_input,
                assistant=result.answer,
                provider_name=provider_name,
                sources=result.sources,
                agent_trace=result.trace,
            ),
        )
        return render_template("index.html", **page_context())

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run()
