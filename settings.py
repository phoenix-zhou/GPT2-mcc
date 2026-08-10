"""Environment configuration with temporary legacy-name compatibility."""

from __future__ import annotations

import os


def get_setting(name: str, default: str | None = None) -> str | None:
    """Read a ClearCare setting, falling back to the former project prefix."""
    value = os.getenv(f"CLEARCARE_{name}")
    if value is not None:
        return value
    return os.getenv(f"GPT2_MCC_{name}", default)
