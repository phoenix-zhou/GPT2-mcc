# ClearCare Health

**A safety-bounded, evidence-grounded healthcare information AI agent**

Safety · Governed RAG · Agent Evaluation · Evidence Governance

[English](README.md) | [简体中文](README.zh-CN.md)

ClearCare Health / 澄心循证健康智能体 is a vertical Applied AI product case:
how can an LLM help a person organize a health question, surface important
warning signs, and inspect general-information sources without presenting
itself as a clinician?

The implementation contains reusable governed-agent components, but this
repository does **not** claim to be a proven general-purpose agent platform.
Its product behavior, evidence corpus, safety policy, and measured results are
specific to the ClearCare health-information scenario.

> [!WARNING]
> This project is for research and education only. It does not diagnose,
> prescribe, select treatment, or replace a clinician. Do not enter real
> patient identifiers, contact details, or other sensitive information.

## Product thesis

General-purpose LLM health answers can sound more certain than their evidence,
miss time-sensitive signals, fabricate or misuse citations, and treat missing
context as permission to guess. ClearCare turns those risks into explicit
product constraints:

- deterministic routing for strong emergency signals before model generation;
- one allow-listed plan/tool/respond cycle and at most one read-only tool call;
- governed sources with provenance, freshness, domain, review, and hash checks;
- citations displayed separately from generated prose;
- local Qwen by default and explicit per-request consent for optional OpenAI;
- provider-neutral evaluation with visible limitations and failure segments.

## Current implementation

| Capability | Current state |
|---|---|
| Safety routing | Deterministic strong-signal router; measurable but not a diagnostic classifier |
| Bounded agent | One plan/tool/respond cycle with validated action/reason pairs and one read-only evidence tool |
| Conversation | Bounded in-memory follow-up context and an explicit reset action |
| Governed RAG | Versioned coverage contract, controlled topic clusters, approved-source registry, URL-host binding, review dates, corpus bounds, and SHA-256 integrity |
| Evaluation | 90-case development set, provider-neutral capture, failure taxonomy, and Keyword/BM25 comparison |
| Model providers | Pinned local Qwen default and optional OpenAI; GPT-2 is excluded from the web runtime |
| Web demo | Local/single-process Flask interface with trace, citations, CSRF, request limits, and security headers |
| Clinical validation | Not completed; all 19 project-authored summaries remain unverified by a clinician |
| Production deployment | Not supported; authentication, distributed controls, encrypted persistence, and compliance work are absent |

## User and agent flow

```text
User health-information question
  → validate input and consent boundary
  → deterministic emergency routing
      ├─ strong signal: fixed emergency guidance; no model call
      └─ non-emergency: bounded planner
          ├─ ask for essential clarification
          ├─ search governed evidence
          └─ respond without a tool
              → local Qwen by default
              → optional OpenAI when enabled and selected
  → answer + separate source links + inspectable action trace
  → bounded follow-up context or explicit reset
```

The trace reports actions and result counts, never hidden chain-of-thought.

## Architecture: reusable, not over-claimed

```text
ClearCare Health
├── Product policy
│   ├── non-diagnosis boundary
│   ├── emergency routing
│   └── clarification and out-of-scope policy
├── Governed agent architecture
│   ├── bounded planner / tool / responder runtime
│   ├── provider adapters
│   ├── evidence validation and retrieval
│   └── privacy and web guardrails
├── Evaluation
│   ├── frozen health cases and prediction contract
│   ├── safety, retrieval, citation, latency, and cost metrics
│   └── segmented failure reports
└── Developer workflow
    └── curate-health-evidence Codex Skill
```

The runtime and evaluation contracts are designed for reuse. They should be
called *domain-extensible abstractions*, not a validated horizontal platform,
until another product domain has its own policy, corpus, frozen evaluation,
and human review.

## Measured evidence and limitations

The table below is the last completed end-to-end Qwen run, captured on dataset
v1.0.0 and the earlier three-record corpus. It is a historical engineering
regression result, not a current 19-record estimate, independent benchmark,
or clinical-performance claim.

| Measurement | Keyword baseline | BM25 candidate |
|---|---:|---:|
| Local-Qwen task-success proxy | 72.5% | 78.75% |
| Retrieval Recall@3 | 62.5% | 75.0% |
| Emergency recall | 100% | 100% |
| Citation-ID validity | 100% | 100% |

BM25 remains a candidate because selection and measurement used the same
development set. Citation-ID validity proves that a returned ID exists; it
does not prove claim-level entailment or answer groundedness. Promotion now
requires a broader governed corpus, an author-separated blind holdout, and
human-reviewed groundedness results.

See [Evaluation v1](docs/evaluation-v1.md),
[RAG V2](docs/rag-v2-experiment.md), and the
[Evaluation MVP](docs/evaluation-mvp.md). The six-record Batch 1, model-free
component replay is preserved as a historical milestone in
[Corpus v1 Batch 1](docs/corpus-v1-batch-1.md): Keyword and BM25 achieved 64%
and 72% Recall@3 respectively while both held 90% no-hit accuracy. The current
19-record component replay is recorded in
[Corpus v1 Batch 5](docs/corpus-v1-batch-5.md): Keyword and BM25 both achieved
75.0% Recall@3 and 89.7% no-hit accuracy after the BM25 threshold was retuned.

## What I owned, inherited, and removed

### Implemented in the modernization

- the professional Flask experience, bounded multi-turn memory, and explicit
  cloud-consent flow;
- local Qwen and optional OpenAI provider abstraction;
- deterministic emergency routing and bounded agent orchestration;
- governed evidence schema, source manifest, validation, and retrieval
  experiments;
- provider-neutral evaluation capture, metrics, failure analysis, and reports;
- the evidence-curation Codex Skill, product case study, roadmap, and security
  hardening.

### Inherited starting point

The project began from
[`phoenix-zhou/GPT2-mcc`](https://github.com/phoenix-zhou/GPT2-mcc). Its legacy
GPT-2 training/inference scripts, vocabulary, and model configuration are
inherited work and are not presented as original contributions. The upstream
repository does not declare an open-source license.

### Removed or quarantined

- raw legacy medical dialogue TXT/Pickle data with unresolved provenance and
  de-identification quality;
- tracked Python bytecode, duplicate templates/vocabulary, and scratch scripts;
- unrestricted Pickle loading, raw conversation logging by default, and the
  legacy GPT-2 web provider;
- mutable default model and CI references.

See the [security and risk review](docs/security-and-risk-review.md) for the
full finding and residual-risk record.

## Quick start

Python 3.10+ is required. Deterministic tests and evaluation do not download a
model or make paid API calls.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'

python scripts/validate_knowledge.py
pytest
python scripts/run_evaluation.py
```

### Run the local Qwen demo

The MLX configuration targets Apple Silicon. The first run downloads the
pinned quantized model and requires sufficient memory.

```bash
python -m pip install -e '.[inference]'
export GOVERNED_AGENT_MODEL_PROVIDER="qwen-local"
export GOVERNED_AGENT_QWEN_MODEL="mlx-community/Qwen3-4B-Instruct-2507-4bit"
export GOVERNED_AGENT_QWEN_REVISION="50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b"
flask --app app run
```

Open <http://127.0.0.1:5000>. In a follow-up, enter only the new information;
the application supplies bounded recent context. Select **Start a new
consultation** to clear it.

### Optional OpenAI comparison

OpenAI API usage is billed separately from ChatGPT subscriptions. Cloud use is
disabled until the server enables it and the user selects it for that request.

```bash
python -m pip install -e '.[openai]'
export OPENAI_API_KEY="your_api_key"
export GOVERNED_AGENT_OPENAI_MODEL="gpt-5.6-terra"
export GOVERNED_AGENT_CLOUD_ENHANCEMENT_ENABLED=true
flask --app app run
```

Requests set `store=False`, but that alone is not a zero-data-retention or
compliance guarantee. Never commit keys or submit sensitive health data.

## Security and deployment boundary

The local demo includes CSRF protection, a 16 KiB request limit,
single-process rate limiting, secure cookie defaults, restrictive response
headers, non-persistent conversations, evidence-source binding, bounded input
and corpus sizes, pinned model provenance, and generic error persistence.
Production mode fails closed without a durable 32+ character secret and secure
cookies.

These controls do **not** make the Flask development server internet-ready.
There is no user authentication, authorization, distributed rate limiter,
encrypted persistent session store, WAF, audit service, or healthcare
compliance certification. See [SECURITY.md](SECURITY.md).

## Governed evidence and data strategy

The current corpus contains 19 project-authored Chinese summaries linked to
CDC, NHS, WHO, NHC, and NMPA pages. They are explicitly **not
clinician-reviewed**. Runtime loading rejects unknown or impersonated sources,
stale reviews, future dates, unsafe URLs, duplicate IDs, oversized records, and
content/hash mismatches.

The versioned [Corpus v1 coverage specification](docs/corpus-v1-coverage-spec.md)
now defines 8 topic clusters and a 24-record target. The automated report shows
the current 19/24 records and every remaining cluster gap. The neurological,
cardiovascular, gastrointestinal, respiratory, fever/infection, and allergy/
medication-safety clusters meet both targets. The
[Batch 5 audit](docs/corpus-v1-batch-5.md) records the source
decisions, label changes, and retrieval regression results.
Paraphrases, hard
negatives, no-hit prompts, and jurisdiction differences are evaluation
phenomena rather than evidence-document types. Adding more documents alone is
not a reliability claim. The included
[`curate-health-evidence`](skills/curate-health-evidence/) Skill automates
deterministic governance checks; it does not perform clinical review.
The bilingual [Chinese official-source discovery guide](docs/china-official-source-discovery.md)
explains how NHC and NMPA portals are used without treating portal pages or
regulatory approval as patient guidance.

## Legacy GPT-2 boundary

The original GPT-2 code remains only as an attributed historical CLI/training
baseline. It is not a web provider or part of the current evaluation. Data
loading rejects Pickle globals/classes and oversized structures; checkpoint
loading is local-only and Safetensors-only. Raw legacy datasets are absent from
the current tree. Git history and upstream snapshots may still retain them.

## Repository map

```text
app.py, web_security.py          Web orchestration and request controls
agent_runtime.py                 Bounded plan/tool/respond runtime
chat_models.py                   Qwen and OpenAI web providers
conversation.py                 Bounded in-memory context
safety.py                        ClearCare emergency routing
knowledge.py, retrieval.py       Governed corpus validation and retrieval
evaluation/, scripts/            Cases, capture, reports, and release checks
skills/curate-health-evidence/   Developer-facing evidence Skill
docs/                            Product, evaluation, RAG, brand, and risk records
data_preprocess/, train.py       Attributed, quarantined GPT-2 legacy workflow
tests/                           Automated regression and security tests
```

## Product documents

- [Product case study](docs/product-case-study.md)
- [Portfolio upgrade roadmap](docs/portfolio-upgrade-roadmap.md)
- [Brand and ownership architecture](docs/brand-architecture.md)
- [Evaluation MVP](docs/evaluation-mvp.md) and [Evaluation v1](docs/evaluation-v1.md)
- [RAG V2 experiment](docs/rag-v2-experiment.md)
- [Security and risk review](docs/security-and-risk-review.md)
- [Health Corpus v1 coverage specification](docs/corpus-v1-coverage-spec.md)
- Corpus v1 audits: [Batch 1](docs/corpus-v1-batch-1.md),
  [Batch 2](docs/corpus-v1-batch-2.md),
  [Batch 3](docs/corpus-v1-batch-3.md),
  [Batch 4](docs/corpus-v1-batch-4.md), and
  [Batch 5](docs/corpus-v1-batch-5.md)

## Next milestones

1. Expand the governed corpus against the completed coverage contract and
   freeze `health_corpus_v1` only after all 24 records pass its acceptance gate.
2. Create an author-separated blind holdout and run paired Keyword/BM25 replay
   with the same planner decisions.
3. Human-review 20–30 sampled answers for citation entailment, claim
   groundedness, unsupported-claim rate, and usefulness.
4. Use an LLM judge only as a calibrated secondary metric, never the sole
   safety gate.
5. Add a recruiter-readable evaluation dashboard and concise walkthrough.

Embedding, hybrid retrieval, additional tools, and broader autonomy remain
deferred until these evidence gaps are closed.

## License and reuse warning

The upstream project does not declare an open-source license, and the provenance
and reuse rights of the removed legacy training data are unresolved. Do not
assume inherited code or data may be redistributed or used commercially without
explicit permission. This modernization does not cure that legal risk; a
clean-room repository is the safest long-term portfolio path if permission
cannot be obtained.
