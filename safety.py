"""Deterministic safety routing before any generative model is called."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyAssessment:
    is_emergency: bool
    category: str | None = None


EMERGENCY_MESSAGE = """你描述的情况可能需要立即处理。请停止等待聊天机器人回答，并立即联系当地急救服务（中国大陆可拨打 120；其他地区请拨打当地急救号码）或前往最近的急诊。

如果现场有人，请让对方陪同并协助联系急救。不要自行驾车。如果涉及立即自伤或自杀风险，请不要独处，远离可能造成伤害的物品，并立即联系急救服务、危机干预热线或可信任的人。

本提示基于关键词进行保守分流，不能判断你是否确实患有某种疾病。"""


class EmergencyRiskRouter:
    """Conservatively identify obvious emergency descriptions, not diagnoses."""

    CATEGORIES = {
        "breathing": (
            "无法呼吸", "不能呼吸", "呼吸极度困难", "喘不上气", "嘴唇发紫", "窒息"
        ),
        "chest_pain": (
            "剧烈胸痛", "胸口压榨", "胸痛放射到", "胸痛伴呼吸困难"
        ),
        "stroke": (
            "一侧肢体无力", "一边脸下垂", "突然说话不清", "突然口齿不清", "突然看不清"
        ),
        "unconsciousness": ("失去意识", "昏迷", "叫不醒", "没有反应"),
        "bleeding": ("大出血", "血流不止", "喷射性出血", "无法止血"),
        "seizure": ("持续抽搐", "癫痫持续", "第一次癫痫发作"),
        "self_harm": (
            "想自杀", "准备自杀", "结束自己的生命", "想伤害自己", "已经割腕", "服药自杀"
        ),
    }

    def assess(self, text: str) -> SafetyAssessment:
        normalized = "".join(text.lower().split())
        for category, phrases in self.CATEGORIES.items():
            if any(phrase in normalized for phrase in phrases):
                return SafetyAssessment(True, category)
        return SafetyAssessment(False)
