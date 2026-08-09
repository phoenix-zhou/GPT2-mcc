from app import create_app


def test_health_endpoint():
    client = create_app(lambda text: text).test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_ask_uses_injected_predictor():
    client = create_app(lambda text: f"回答：{text}").test_client()

    response = client.post("/ask", data={"user_input": "  你好  "})

    assert response.status_code == 200
    assert "回答：你好" in response.get_data(as_text=True)


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
