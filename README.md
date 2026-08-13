# ClearCare Evidence Agent

[English](README.md) | [简体中文](README.zh-CN.md)

A local-first, evidence-grounded health AI agent research project. ClearCare
uses a bounded plan/tool/respond cycle, governed local sources, deterministic
emergency routing, and multi-turn context. Qwen runs locally by default;
OpenAI is an explicit per-request option. The inherited GPT-2 implementation
is retained only as an archived educational baseline.

> [!WARNING]
> This project is for research and education only. It does not provide medical
> diagnosis, prescriptions, or treatment advice and must not replace qualified
> clinicians. Do not enter real patient names, identifiers, contact details, or
> other sensitive information.

## Highlights

- Local Qwen is the default provider, with no per-token API charge.
- OpenAI enhancement is disabled by default and requires both server approval
  and explicit selection by the user for each request.
- A model planner selects an allow-listed action: retrieve evidence, request
  clarification, or respond without a tool.
- Agent execution is bounded to one read-only tool call and emits an
  inspectable action trace without exposing chain-of-thought.
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
      └─ Non-emergency: bounded agent plan
          ├─ Ask for essential clarification
          ├─ Search the governed evidence tool
          └─ Respond without a tool
              → Local Qwen (default)
              → OpenAI GPT (server-enabled and selected per request)
  → Answer and reference links
  → Inspectable action/tool trace
```

## Quick start with local Qwen

Python 3.10 or newer is required. The first run downloads the selected model
and requires enough RAM or VRAM for its weights.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[inference]'

export CLEARCARE_MODEL_PROVIDER="qwen-local"
export CLEARCARE_QWEN_MODEL="mlx-community/Qwen3-4B-Instruct-2507-4bit"

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
export CLEARCARE_OPENAI_MODEL="gpt-5.6-luna"
export CLEARCARE_CLOUD_ENHANCEMENT_ENABLED=true

flask --app app run
```

OpenAI requests set `store=False`. This alone is not a complete zero-data-
retention guarantee. Review account data controls, applicable regulations, and
medical-data requirements before any production deployment. An agent turn can
use one planning call and one answering call, so cloud usage may incur two
model calls.

## Legacy GPT-2 baseline

```bash
export CLEARCARE_MODEL_PROVIDER="legacy-gpt2"
export CLEARCARE_INFERENCE_MODEL_PATH="/path/to/gpt2/checkpoint"
python -m pip install -e '.[legacy-inference]'
flask --app app run
```

The upstream repository does not commit the large `pytorch_model.bin` file.
Resources published by the original author:

- [Model checkpoint on Baidu Netdisk](https://pan.baidu.com/s/1CBWmrspoGenggJ2-GyOirA?pwd=2mrv), extraction code `2mrv`
- [Original CSDN project article](https://blog.csdn.net/zhoupenghui168/article/details/162314485)

`GPT2_MCC_*` variables remain accepted temporarily for local migration, but new
configuration should use `CLEARCARE_*`.

## Agent safety and governed evidence

`safety.py` conservatively routes strong signals such as severe breathing
difficulty, stroke signs, uncontrolled bleeding, unconsciousness, and
immediate self-harm risk. It is not a diagnostic model, can produce false
positives or false negatives, and must not be treated as a medical device.

`agent_runtime.py` implements the allow-listed plan/tool/respond cycle. Planner
output is parsed as JSON; invalid or unregistered actions fall back to a single
read-only evidence search. Tool traces contain action names and result counts,
not hidden reasoning.

`knowledge/medical_guidance.json` currently contains three project-authored
Chinese summaries linked to CDC, NHS, and WHO pages. They are explicitly marked
as not clinician-reviewed and must not be represented as validated clinical
recommendations. Every record includes provenance, jurisdiction, review date,
version, applicability, reuse status, and a SHA-256 content hash.
`knowledge/source_manifest.json` defines the approved source registry and
review policy. The application refuses missing metadata, unknown sources,
non-HTTPS URLs, invalid dates, duplicate IDs, and changed content with a stale
hash.

## Installable Codex skill

The repository includes `curate-health-evidence`, a reusable Codex skill for
adding governed records, auditing provenance and freshness, and generating
corpus coverage reports. It is deliberately a developer workflow, not a
patient-advice skill.

Ask Codex to install:

```text
Install the Codex skill from
https://github.com/yuanzou0/clearcare-health-agent/tree/main/skills/curate-health-evidence
```

On the next turn, invoke it with `$curate-health-evidence`. The source folder
contains only `SKILL.md`, UI metadata, deterministic scripts, and references;
the Flask application and model weights are not duplicated inside the skill.

## Development and tests

```bash
python -m pip install -e '.[dev]'
python scripts/validate_knowledge.py
pytest
```

Tests use fake providers. They do not download Qwen or make paid API calls.

## Product case and upgrade plan

- [Product case study](docs/product-case-study.md): problem, users, journey,
  product decisions, trade-offs, metrics, failure cases, and non-goals.
- [Portfolio upgrade roadmap](docs/portfolio-upgrade-roadmap.md): dated,
  checkable milestones for evaluation, RAG experiments, analytics, Skills, and
  deployment.

## Project layout

```text
app.py                          Flask app and request orchestration
agent_runtime.py                Bounded planner/tool/responder runtime
chat_models.py                  Qwen, OpenAI, and GPT-2 providers
conversation.py                 Bounded in-memory multi-turn context
safety.py                       Emergency-risk routing
knowledge.py                    Local retrieval and context construction
knowledge/medical_guidance.json Versioned guidance with provenance
knowledge/source_manifest.json  Approved sources and review policy
scripts/validate_knowledge.py    Standalone provenance/integrity check
skills/curate-health-evidence/   Installable evidence-curation Codex skill
templates/index.html            Web interface
data_preprocess/                Original GPT-2 preprocessing code
train.py                        Original GPT-2 training entry point
tests/                          Automated tests
```

## Roadmap

The next milestone is a reproducible evaluation harness, followed by a measured
comparison of retrieval strategies. See the
[checkable portfolio roadmap](docs/portfolio-upgrade-roadmap.md) for priorities,
acceptance criteria, and timeline.

## License

The upstream project currently does not declare an open-source license. Do not
assume the code or data may be redistributed or used commercially without
explicit permission from the original author.
