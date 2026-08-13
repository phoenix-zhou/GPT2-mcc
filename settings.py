"""Environment configuration with ordered brand-migration compatibility."""

from __future__ import annotations

import os


def get_setting(name: str, default: str | None = None) -> str | None:
    """Read the platform setting, then health-vertical and legacy aliases."""
    for prefix in ("GOVERNED_AGENT", "CLEARCARE", "GPT2_MCC"):
        value = os.getenv(f"{prefix}_{name}")
        if value is not None:
            return value
    return default
