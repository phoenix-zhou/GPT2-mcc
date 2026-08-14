# Legacy data boundary / 历史数据边界

The original medical dialogue TXT and generated Pickle files are intentionally
not distributed. Their provenance, consent/de-identification quality, licensing,
and redistribution rights could not be established. Do not restore them to the
tracked repository.

原始医疗对话 TXT 和生成的 Pickle 不再随仓库分发，因为其来源、授权/去标识质量、
许可证和再分发权无法确认。不要把这些文件重新提交到仓库。

If the historical GPT-2 baseline must be reproduced, use a lawfully obtained,
appropriately licensed, de-identified dataset and keep it under the ignored
`local_data/` directory. The preprocessing script does not print raw records,
and the runtime loader rejects Pickle globals/classes and oversized structures.
Legacy checkpoints must be local Safetensors files; never load an untrusted
PyTorch `.bin` checkpoint.

如确需复现 GPT-2 历史基线，请使用具有合法来源、适当许可并已去标识的数据，保存
到被忽略的 `local_data/`。预处理脚本不会输出原始记录，运行时加载器会拒绝 Pickle
全局对象、类和超大结构。
