"""Generate local legacy GPT-2 token-ID pickles from reviewed text files."""

from __future__ import annotations

import argparse
import pickle
from pathlib import Path

from tqdm import tqdm
from transformers import BertTokenizerFast


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def data_preprocess(
    input_path: str | Path,
    output_path: str | Path,
    *,
    vocab_path: str | Path = PROJECT_ROOT / "vocab" / "vocab.txt",
) -> None:
    """Tokenize dialogue blocks and write a local, ignored legacy artifact."""
    source = Path(input_path)
    destination = Path(output_path)
    tokenizer = BertTokenizerFast(
        vocab_file=str(vocab_path),
        sep_token="[SEP]",
        pad_token="[PAD]",
        cls_token="[CLS]",
    )
    data = source.read_text(encoding="utf-8")
    normalized = data.replace("\r\n", "\n")
    dialogues = normalized.split("\n\n")
    dialogue_list: list[list[int]] = []
    for dialogue in tqdm(dialogues, desc=f"Tokenizing {source.name}"):
        input_ids = [tokenizer.cls_token_id]
        for sequence in dialogue.split("\n"):
            input_ids.extend(
                tokenizer.encode(sequence, add_special_tokens=False)
            )
            input_ids.append(tokenizer.sep_token_id)
        dialogue_list.append(input_ids)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as stream:
        pickle.dump(dialogue_list, stream, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"Wrote {len(dialogue_list)} sequences to {destination}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--vocab",
        type=Path,
        default=PROJECT_ROOT / "vocab" / "vocab.txt",
    )
    args = parser.parse_args()
    data_preprocess(args.input, args.output, vocab_path=args.vocab)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
