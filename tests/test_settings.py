from settings import get_setting


def test_platform_setting_takes_precedence(monkeypatch):
    monkeypatch.setenv("GPT2_MCC_SAMPLE", "legacy")
    monkeypatch.setenv("CLEARCARE_SAMPLE", "clearcare")
    monkeypatch.setenv("GOVERNED_AGENT_SAMPLE", "platform")

    assert get_setting("SAMPLE") == "platform"


def test_clearcare_setting_is_supported_for_health_vertical(monkeypatch):
    monkeypatch.delenv("GOVERNED_AGENT_SAMPLE", raising=False)
    monkeypatch.setenv("CLEARCARE_SAMPLE", "clearcare")

    assert get_setting("SAMPLE") == "clearcare"


def test_legacy_setting_is_supported_during_migration(monkeypatch):
    monkeypatch.delenv("GOVERNED_AGENT_SAMPLE", raising=False)
    monkeypatch.delenv("CLEARCARE_SAMPLE", raising=False)
    monkeypatch.setenv("GPT2_MCC_SAMPLE", "legacy")

    assert get_setting("SAMPLE") == "legacy"
