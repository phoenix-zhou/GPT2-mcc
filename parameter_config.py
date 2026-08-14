"""Runtime and training configuration.

Paths default to locations inside the repository and can be overridden with
``GOVERNED_AGENT_*`` variables. The health-vertical ``CLEARCARE_*`` and legacy
``GPT2_MCC_*`` prefixes remain available during migration.
"""

from __future__ import annotations

from pathlib import Path

import torch

try:
    from .settings import get_setting
except ImportError:
    from settings import get_setting


class ParameterConfig:
    def __init__(self) -> None:
        project_root = Path(__file__).resolve().parent

        self.device = torch.device(
            get_setting(
                "DEVICE",
                "cuda" if torch.cuda.is_available() else "cpu",
            )
        )
        self.vocab_path = get_setting(
            "VOCAB_PATH", str(project_root / "vocab" / "vocab.txt")
        )
        self.train_path = get_setting(
            "TRAIN_PATH", str(project_root / "data" / "medical_train.pkl")
        )
        self.valid_path = get_setting(
            "VALID_PATH", str(project_root / "data" / "medical_valid.pkl")
        )
        self.config_json = get_setting(
            "CONFIG_PATH", str(project_root / "config" / "config.json")
        )
        self.save_model_path = get_setting(
            "MODEL_DIR", str(project_root / "save_model")
        )
        self.inference_model_path = get_setting(
            "INFERENCE_MODEL_PATH",
            str(project_root / "save_model" / "epoch97"),
        )
        self.pretrained_model = get_setting("PRETRAINED_MODEL", "")
        self.save_samples_path = get_setting(
            "SAMPLES_PATH", ""
        )

        self.ignore_index = -100
        self.max_history_len = 3
        self.max_len = 300
        self.repetition_penalty = 10.0
        self.topk = 4
        self.batch_size = 4
        self.epochs = 4
        self.loss_step = 1
        self.lr = 2.6e-5
        self.eps = 1.0e-9
        self.max_grad_norm = 4.0
        self.gradient_accumulation_steps = 4
        self.warmup_steps = 100


if __name__ == "__main__":
    config = ParameterConfig()
    print(config.train_path)
    print(config.device)
    print(torch.cuda.device_count())
