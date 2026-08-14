"""Restricted loader for legacy token-ID datasets.

The original project used unrestricted ``pickle.load``. Pickle may execute
arbitrary code while deserializing attacker-controlled files, so this loader
rejects all global/class lookups and validates the complete primitive shape.
"""

from __future__ import annotations

import io
import pickle
from pathlib import Path


MAX_PICKLE_BYTES = 64 * 1024 * 1024
MAX_SEQUENCES = 200_000
MAX_SEQUENCE_LENGTH = 8_192
MAX_TOKEN_ID = 10_000_000


class _PrimitiveOnlyUnpickler(pickle.Unpickler):
    def find_class(self, module: str, name: str):  # pragma: no cover - invoked by pickle
        raise pickle.UnpicklingError(
            f"global objects are forbidden in legacy datasets: {module}.{name}"
        )


def load_token_id_sequences(path: str | Path) -> list[list[int]]:
    """Load a bounded ``list[list[int]]`` without permitting code execution."""
    source = Path(path)
    size = source.stat().st_size
    if size > MAX_PICKLE_BYTES:
        raise ValueError(f"legacy dataset exceeds {MAX_PICKLE_BYTES} bytes")
    payload = source.read_bytes()
    stream = io.BytesIO(payload)
    try:
        value = _PrimitiveOnlyUnpickler(stream).load()
    except pickle.UnpicklingError as exc:
        raise ValueError("legacy dataset contains forbidden pickle objects") from exc
    if stream.read(1):
        raise ValueError("legacy dataset contains trailing pickle data")
    if not isinstance(value, list) or len(value) > MAX_SEQUENCES:
        raise ValueError("legacy dataset must be a bounded list of sequences")
    for sequence in value:
        if not isinstance(sequence, list) or len(sequence) > MAX_SEQUENCE_LENGTH:
            raise ValueError("legacy dataset sequences must be bounded lists")
        if not all(
            isinstance(token_id, int)
            and not isinstance(token_id, bool)
            and 0 <= token_id <= MAX_TOKEN_ID
            for token_id in sequence
        ):
            raise ValueError("legacy dataset token IDs must be non-negative integers")
    return value
