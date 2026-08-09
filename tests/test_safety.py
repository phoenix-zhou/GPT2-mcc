from safety import EmergencyRiskRouter


def test_router_detects_obvious_stroke_signal():
    result = EmergencyRiskRouter().assess("他突然说话不清，而且一侧肢体无力")

    assert result.is_emergency is True
    assert result.category == "stroke"


def test_router_detects_immediate_self_harm_signal():
    result = EmergencyRiskRouter().assess("我准备自杀")

    assert result.is_emergency is True
    assert result.category == "self_harm"


def test_router_does_not_classify_ordinary_question_as_emergency():
    result = EmergencyRiskRouter().assess("感冒之后有点咳嗽应该注意什么")

    assert result.is_emergency is False
