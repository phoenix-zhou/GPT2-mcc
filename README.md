# 🏥 Local-first Medical Chatbot

[English](README.md) | [简体中文](README.zh-CN.md)

A Flask-based medical information chatbot research project. The current
version runs a Qwen instruction model locally by default, supports explicit
per-request OpenAI enhancement, and preserves the original GPT-2
implementation as a legacy baseline for education and comparison.

> [!WARNING]
> This project is for research and education only. It does not provide medical
> diagnosis, prescriptions, or treatment advice and must not replace qualified
> clinicians. Do not enter real patient names, identifiers, contact details, or
> other sensitive information.

## Highlights

- Local Qwen is the default provider, with no per-token API charge.
- OpenAI enhancement is disabled by default and requires both server approval
  and explicit selection by the user for each request.
- The original GPT-2 path remains available as a compatibility baseline.
- Strong emergency signals are routed before any generative model is called.
- Non-emergency questions can retrieve versioned local medical references,
  with source links rendered separately from model output.
- Follow-up messages automatically include the latest four dialogue turns;
  the interface keeps up to six turns in bounded server memory.
- Flask application factory, lazy model loading, health endpoint, input
  validation, controlled error handling, Pytest tests, and GitHub Actions CI.

## Request flow

```text
Browser request
  → Input validation
  → Emergency-risk routing
      ├─ High risk: fixed emergency guidance; no model call
      └─ Non-emergency: local knowledge retrieval
          → Recent conversation context (up to four turns)
          → Local Qwen (default)
          → OpenAI GPT (server-enabled and selected per request)
  → Answer and reference links
```

## Quick start with local Qwen

Python 3.10 or newer is required. The first run downloads the selected model
and requires enough RAM or VRAM for its weights.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[inference]'

export GPT2_MCC_MODEL_PROVIDER="qwen-local"
export GPT2_MCC_QWEN_MODEL="mlx-community/Qwen3-4B-Instruct-2507-4bit"

flask --app app run
```

Open <http://127.0.0.1:5000>.

## Follow-up conversations and memory

After the first answer, enter only the new information—for example, “It has
lasted two days, about five times a day, without fever.” You do not need to
delete, copy, or repeat the earlier question. The model receives up to the
latest four turns as context, while the page displays up to six turns.

Conversation content is held only in the running Flask process. It is not
written to the repository or a database, and it disappears when the server
restarts or when **Start a new consultation** is selected. This simple design
is suitable for the local demo; production deployment should use an encrypted,
access-controlled server-side session store with an explicit retention policy.

## Optional OpenAI enhancement

OpenAI API usage is billed separately from ChatGPT subscriptions. The API key
is read only from the environment and must never be committed to source code,
`.env` files, or Git history.

```bash
python -m pip install -e '.[openai]'

export OPENAI_API_KEY="your_api_key"
export GPT2_MCC_OPENAI_MODEL="gpt-5.6-luna"
export GPT2_MCC_CLOUD_ENHANCEMENT_ENABLED=true

flask --app app run
```

OpenAI requests set `store=False`. This alone is not a complete zero-data-
retention guarantee. Review account data controls, applicable regulations, and
medical-data requirements before any production deployment.

## Legacy GPT-2 baseline

```bash
export GPT2_MCC_MODEL_PROVIDER="legacy-gpt2"
export GPT2_MCC_INFERENCE_MODEL_PATH="/path/to/gpt2/checkpoint"
python -m pip install -e '.[legacy-inference]'
flask --app app run
```

The upstream repository does not commit the large `pytorch_model.bin` file.
Resources published by the original author:

- [Model checkpoint on Baidu Netdisk](https://pan.baidu.com/s/1CBWmrspoGenggJ2-GyOirA?pwd=2mrv), extraction code `2mrv`
- [Original CSDN project article](https://blog.csdn.net/zhoupenghui168/article/details/162314485)

## Safety routing and local retrieval

`safety.py` conservatively routes strong signals such as severe breathing
difficulty, stroke signs, uncontrolled bleeding, unconsciousness, and
immediate self-harm risk. It is not a diagnostic model, can produce false
positives or false negatives, and must not be treated as a medical device.

`knowledge/medical_guidance.json` is a small, reviewable local knowledge base.
The starter documents cite CDC, NHS, and WHO guidance. `knowledge.py` currently
uses dependency-free keyword retrieval and can later be replaced by vector
retrieval without changing the web-layer interface.

## Development and tests

```bash
python -m pip install -e '.[dev]'
pytest
```

Tests use fake providers. They do not download Qwen or make paid API calls.

## Project layout

```text
app.py                          Flask app and request orchestration
chat_models.py                  Qwen, OpenAI, and GPT-2 providers
conversation.py                 Bounded in-memory multi-turn context
safety.py                       Emergency-risk routing
knowledge.py                    Local retrieval and context construction
knowledge/medical_guidance.json Versioned guidance with provenance
templates/index.html            Web interface
data_preprocess/                Original GPT-2 preprocessing code
train.py                        Original GPT-2 training entry point
tests/                          Automated tests
```

## Roadmap

- Expand the knowledge base with professional content review.
- Upgrade RAG with Chinese embeddings and a reranker.
- Add streaming output and structured answers.
- Build safety, factuality, citation-accuracy, latency, and cost evaluations.
- Add containers, a production WSGI server, observability, and deployment docs.

## License

The upstream project currently does not declare an open-source license. Do not
assume the code or data may be redistributed or used commercially without
explicit permission from the original author.
