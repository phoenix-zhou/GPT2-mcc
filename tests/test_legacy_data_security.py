import os
import pickle

import pytest

from data_preprocess.safe_pickle import load_token_id_sequences


def test_restricted_legacy_loader_accepts_only_token_id_lists(tmp_path):
    dataset = tmp_path / "tokens.pkl"
    dataset.write_bytes(pickle.dumps([[101, 102], [101, 200, 102]]))

    assert load_token_id_sequences(dataset) == [[101, 102], [101, 200, 102]]


def test_restricted_legacy_loader_blocks_pickle_code_execution(tmp_path):
    marker = tmp_path / "must-not-exist"

    class MaliciousPayload:
        def __reduce__(self):
            return os.system, (f"touch {marker}",)

    dataset = tmp_path / "malicious.pkl"
    dataset.write_bytes(pickle.dumps(MaliciousPayload()))

    with pytest.raises(ValueError, match="forbidden pickle objects"):
        load_token_id_sequences(dataset)
    assert not marker.exists()


def test_restricted_legacy_loader_rejects_invalid_token_shape(tmp_path):
    dataset = tmp_path / "invalid.pkl"
    dataset.write_bytes(pickle.dumps([[101, "not-an-id"]]))

    with pytest.raises(ValueError, match="token IDs"):
        load_token_id_sequences(dataset)


def test_restricted_legacy_loader_rejects_trailing_payload(tmp_path):
    dataset = tmp_path / "trailing.pkl"
    dataset.write_bytes(pickle.dumps([[101, 102]]) + b"unexpected")

    with pytest.raises(ValueError, match="trailing pickle data"):
        load_token_id_sequences(dataset)
