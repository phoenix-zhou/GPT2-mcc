"""Flask application entry point for the medical chatbot demo."""

from __future__ import annotations

import logging
from collections.abc import Callable

from flask import Flask, current_app, render_template, request

Predictor = Callable[[str], str]


def _default_predictor(text: str) -> str:
    """Load the configured model provider on the first prediction request."""
    try:
        from chat_models import get_default_chat_model

        return get_default_chat_model().generate(text)
    except Exception as exc:
        # Provider SDKs expose different exception hierarchies. Normalize them
        # at this boundary so the web layer can return a controlled 503 page.
        raise RuntimeError("Model provider request failed") from exc


def create_app(predictor: Predictor | None = None) -> Flask:
    """Create the web application, optionally injecting a test predictor."""
    app = Flask(__name__)
    app.config.from_mapping(MAX_INPUT_LENGTH=1000)
    app.config.from_prefixed_env(prefix="GPT2_MCC")
    app.extensions["predictor"] = predictor or _default_predictor

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

        try:
            answer = current_app.extensions["predictor"](user_input)
        except (FileNotFoundError, OSError, RuntimeError):
            current_app.logger.exception("Model prediction failed")
            return render_template(
                "index.html",
                user_input=user_input,
                error="模型当前不可用，请确认模型权重和运行环境已正确配置。",
            ), 503

        return render_template(
            "index.html", user_input=user_input, answer=answer
        )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run()
