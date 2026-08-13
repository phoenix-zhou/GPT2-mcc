from app import create_app, render_markdown
from knowledge import KnowledgeDocument


def test_health_endpoint():
    client = create_app(lambda text: text).test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_platform_flask_prefix_overrides_compatibility_prefixes(monkeypatch):
    monkeypatch.setenv("GPT2_MCC_CLOUD_ENHANCEMENT_ENABLED", "true")
    monkeypatch.setenv("CLEARCARE_CLOUD_ENHANCEMENT_ENABLED", "false")
    monkeypatch.setenv("GOVERNED_AGENT_CLOUD_ENHANCEMENT_ENABLED", "true")

    app = create_app(lambda text: text)

    assert app.config["CLOUD_ENHANCEMENT_ENABLED"] is True


def test_homepage_uses_professional_brand_and_assets():
    response = create_app(lambda text: text).test_client().get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "<title>澄心循证健康智能体</title>" in html
    assert "ClearCare Health" in html
    assert "Governed Agent Lab" in html
    assert "/static/styles.css" in html
    assert "/static/app.js" in html
    assert "黑马" not in html
    assert "小李子" not in html


def test_markdown_renderer_formats_and_sanitizes_model_output():
    rendered = str(
        render_markdown(
            "### 初步判断\n\n**重点**\n\n- 第一项\n- 第二项\n\n"
            "<script>alert(1)</script>[危险](javascript:alert(1))"
        )
    )

    assert "<h3>初步判断</h3>" in rendered
    assert "<strong>重点</strong>" in rendered
    assert "<li>第一项</li>" in rendered
    assert "<script>" not in rendered
    assert "javascript:" not in rendered


def test_ask_uses_injected_predictor():
    client = create_app(lambda text: f"回答：{text}").test_client()

    response = client.post("/ask", data={"user_input": "  你好  "})

    assert response.status_code == 200
    assert "回答：你好" in response.get_data(as_text=True)
    assert "查看智能体执行记录" in response.get_data(as_text=True)


def test_follow_up_includes_recent_conversation_context():
    model_inputs = []
    app = create_app(
        lambda text: model_inputs.append(text) or f"第 {len(model_inputs)} 次回答"
    )
    client = app.test_client()

    first = client.post("/ask", data={"user_input": "我有拉肚子"})
    second = client.post(
        "/ask", data={"user_input": "已经两天了，每天五次，没有发烧"}
    )

    assert first.status_code == 200
    assert second.status_code == 200
    answer_inputs = [text for text in model_inputs if not text.startswith("[AGENT_PLAN]")]
    assert answer_inputs[0] == "我有拉肚子"
    assert "我有拉肚子" in answer_inputs[1]
    assert "第 2 次回答" in answer_inputs[1]
    assert "已经两天了，每天五次，没有发烧" in answer_inputs[1]
    html = second.get_data(as_text=True)
    assert "无需删除或重复前面的内容" in html
    assert "开始新咨询" in html
    assert html.count('class="conversation-turn') == 2


def test_follow_up_knowledge_search_includes_recent_user_context():
    queries = []

    class RecordingKnowledgeBase:
        def search(self, query):
            queries.append(query)
            return []

    app = create_app(
        lambda text: "回答",
        knowledge_base=RecordingKnowledgeBase(),
    )
    client = app.test_client()
    client.post("/ask", data={"user_input": "我有拉肚子"})
    client.post("/ask", data={"user_input": "每天大约五次"})

    assert queries == ["我有拉肚子", "我有拉肚子\n每天大约五次"]


def test_new_consultation_clears_history_and_model_context():
    model_inputs = []
    app = create_app(lambda text: model_inputs.append(text) or "回答")
    client = app.test_client()
    client.post("/ask", data={"user_input": "旧问题"})

    reset = client.post("/conversation/reset")
    homepage = client.get("/")
    client.post("/ask", data={"user_input": "新问题"})

    assert reset.status_code == 302
    assert "旧问题" not in homepage.get_data(as_text=True)
    assert model_inputs[-1] == "新问题"


def test_conversations_are_isolated_between_browser_sessions():
    app = create_app(lambda text: "回答")
    first_client = app.test_client()
    second_client = app.test_client()

    first_client.post("/ask", data={"user_input": "第一个人的问题"})
    second_home = second_client.get("/")

    assert "第一个人的问题" not in second_home.get_data(as_text=True)


def test_ask_rejects_empty_input():
    client = create_app(lambda text: text).test_client()

    response = client.post("/ask", data={"user_input": "  "})

    assert response.status_code == 400
    assert "请输入咨询内容" in response.get_data(as_text=True)


def test_ask_reports_unavailable_model():
    def unavailable(_text: str) -> str:
        raise FileNotFoundError("missing weights")

    client = create_app(unavailable).test_client()
    response = client.post("/ask", data={"user_input": "头痛"})

    assert response.status_code == 503
    assert "模型当前不可用" in response.get_data(as_text=True)


def test_cloud_request_is_blocked_by_default():
    cloud_calls = []
    app = create_app(
        lambda text: "local",
        cloud_predictor=lambda text: cloud_calls.append(text) or "cloud",
    )

    response = app.test_client().post(
        "/ask", data={"user_input": "测试", "use_cloud": "on"}
    )

    assert response.status_code == 403
    assert cloud_calls == []
    assert "没有发送数据或产生 API 费用" in response.get_data(as_text=True)


def test_explicit_cloud_request_uses_cloud_provider():
    local_calls = []
    cloud_calls = []
    app = create_app(
        lambda text: local_calls.append(text) or "local",
        cloud_predictor=lambda text: cloud_calls.append(text) or "cloud answer",
    )
    app.config["CLOUD_ENHANCEMENT_ENABLED"] = True

    response = app.test_client().post(
        "/ask", data={"user_input": "复杂问题", "use_cloud": "on"}
    )

    assert response.status_code == 200
    assert local_calls == []
    assert len(cloud_calls) == 2
    assert cloud_calls[0].startswith("[AGENT_PLAN]")
    assert cloud_calls[1] == "复杂问题"
    assert "OpenAI GPT" in response.get_data(as_text=True)


def test_cloud_option_discloses_that_recent_context_is_sent():
    app = create_app(lambda text: "local")
    app.config["CLOUD_ENHANCEMENT_ENABLED"] = True

    html = app.test_client().get("/").get_data(as_text=True)

    assert "本轮内容及最近对话将发送至 OpenAI" in html


def test_emergency_bypasses_all_model_providers():
    local_calls = []
    cloud_calls = []
    app = create_app(
        lambda text: local_calls.append(text) or "local",
        cloud_predictor=lambda text: cloud_calls.append(text) or "cloud",
    )
    app.config["CLOUD_ENHANCEMENT_ENABLED"] = True

    response = app.test_client().post(
        "/ask",
        data={"user_input": "突然说话不清而且一侧肢体无力", "use_cloud": "on"},
    )

    assert response.status_code == 200
    assert local_calls == []
    assert cloud_calls == []
    assert "立即联系当地急救服务" in response.get_data(as_text=True)
    assert "未调用生成模型" in response.get_data(as_text=True)


def test_retrieved_context_reaches_model_and_source_is_rendered():
    document = KnowledgeDocument(
        title="可信资料",
        content="经过审核的内容",
        source_url="https://example.test/guidance",
        keywords=("测试",),
    )

    class FakeKnowledgeBase:
        def search(self, query):
            assert query == "一般测试问题"
            return [document]

    model_inputs = []
    app = create_app(
        lambda text: model_inputs.append(text) or "回答",
        knowledge_base=FakeKnowledgeBase(),
    )

    response = app.test_client().post(
        "/ask", data={"user_input": "一般测试问题"}
    )

    assert response.status_code == 200
    assert any("经过审核的内容" in text for text in model_inputs)
    assert "可信资料" in response.get_data(as_text=True)
    assert "https://example.test/guidance" in response.get_data(as_text=True)
