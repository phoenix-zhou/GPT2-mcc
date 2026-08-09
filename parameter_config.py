"""Runtime and training configuration.

Paths default to locations inside the repository and can be overridden with
environment variables prefixed with ``GPT2_MCC_``.
"""

from __future__ import annotations

import os
from pathlib import Path

import torch


class ParameterConfig:
    def __init__(self) -> None:
        project_root = Path(__file__).resolve().parent

        self.device = torch.device(
            os.getenv(
                "GPT2_MCC_DEVICE",
                "cuda" if torch.cuda.is_available() else "cpu",
            )
        )
        self.vocab_path = os.getenv(
            "GPT2_MCC_VOCAB_PATH", str(project_root / "vocab" / "vocab.txt")
        )
        self.train_path = os.getenv(
            "GPT2_MCC_TRAIN_PATH", str(project_root / "data" / "medical_train.pkl")
        )
        self.valid_path = os.getenv(
            "GPT2_MCC_VALID_PATH", str(project_root / "data" / "medical_valid.pkl")
        )
        self.config_json = os.getenv(
            "GPT2_MCC_CONFIG_PATH", str(project_root / "config" / "config.json")
        )
        self.save_model_path = os.getenv(
            "GPT2_MCC_MODEL_DIR", str(project_root / "save_model")
        )
        self.inference_model_path = os.getenv(
            "GPT2_MCC_INFERENCE_MODEL_PATH",
            str(project_root / "save_model" / "epoch97"),
        )
        self.pretrained_model = os.getenv("GPT2_MCC_PRETRAINED_MODEL", "")
        self.save_samples_path = os.getenv(
            "GPT2_MCC_SAMPLES_PATH", str(project_root / "sample")
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
