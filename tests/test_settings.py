from settings import get_setting


def test_clearcare_setting_takes_precedence(monkeypatch):
    monkeypatch.setenv("GPT2_MCC_SAMPLE", "legacy")
    monkeypatch.setenv("CLEARCARE_SAMPLE", "clearcare")

    assert get_setting("SAMPLE") == "clearcare"


def test_legacy_setting_is_supported_during_migration(monkeypatch):
    monkeypatch.delenv("CLEARCARE_SAMPLE", raising=False)
    monkeypatch.setenv("GPT2_MCC_SAMPLE", "legacy")

    assert get_setting("SAMPLE") == "legacy"
