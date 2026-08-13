# ClearCare Portfolio Upgrade Roadmap

Last updated: 2026-08-11

This roadmap turns ClearCare from a working health-chat demo into an
evidence-backed product case for three related roles:

- **AI Product Manager:** problem framing, risk decisions, metrics, user
  journey, prioritization, and trade-offs;
- **Data Analyst:** evaluation design, metric definitions, experiment analysis,
  dashboards, and failure segmentation;
- **Applied AI / LLM Application Engineer:** bounded agent orchestration,
  retrieval experiments, safety controls, observability, and reusable skills.

The goal is not to maximize feature count. The goal is to produce a coherent,
measurable story: **why the system is constrained, how it is evaluated, and
which evidence supports each product decision.**

## Status legend

- [x] Implemented and verified in the repository
- [ ] Not yet complete

## Current foundation

- [x] Establish the ClearCare Evidence Agent product identity and explicit
  non-diagnosis boundary.
- [x] Use local Qwen by default and make OpenAI an explicit per-request option.
- [x] Route strong emergency signals deterministically before model generation.
- [x] Bound the agent to one allow-listed plan/tool/respond cycle and one
  read-only tool call.
- [x] Maintain bounded multi-turn context and a visible reset action.
- [x] Separate generated answers, source links, and inspectable action traces.
- [x] Govern evidence records with source metadata, review status, content
  hashes, and freshness rules.
- [x] Ship the installable `curate-health-evidence` developer Skill.
- [x] Pass the current automated suite (43 tests as of 2026-08-11).
- [x] Publish an initial product case study at
  [`docs/product-case-study.md`](product-case-study.md).

## P0 — Evaluation before architecture expansion

### 1. Evaluation dataset and harness

- [ ] Define a versioned, privacy-safe evaluation schema with case ID, intent,
  expected route, required facts, prohibited claims, expected sources, and
  reviewer status.
- [ ] Create an 80-case MVP covering emergency, routine health information,
  insufficient context, out-of-scope, adversarial, and retrieval/citation
  scenarios.
- [ ] Expand to at least 150 cases only after reviewing the MVP labels and
  failure taxonomy.
- [ ] Implement deterministic checks for route selection, source presence,
  citation mapping, refusal/non-diagnosis behavior, latency, and model-call
  count.
- [ ] Add judge-based groundedness scoring as a separate, clearly labelled
  metric; never use it as the only safety evaluator.
- [ ] Generate a reproducible Markdown and JSON evaluation report.
- [ ] Add regression thresholds to CI for deterministic metrics.

**Core metrics**

- Emergency recall and emergency false-positive rate
- Clarification precision and task completion rate
- Retrieval Recall@K / MRR
- Citation validity and citation entailment
- Groundedness / unsupported-claim rate
- P50 and P95 latency
- Model-call count and estimated cloud cost per completed consultation

**Definition of done:** one command runs the frozen dataset and produces a
versioned report with results segmented by scenario, model provider, and
retrieval strategy.

### 2. Failure taxonomy and release gates

- [ ] Define failure categories: missed emergency, unnecessary escalation,
  missing clarification, retrieval miss, unsupported claim, citation mismatch,
  incomplete answer, unsafe instruction, and provider/runtime failure.
- [ ] Set guardrail thresholds before running comparative experiments.
- [ ] Document which failures block a release and which require human review.
- [ ] Add a compact model card / evaluation limitations section.

## P1 — RAG V2 as a measured experiment

- [ ] Preserve keyword retrieval as the baseline.
- [ ] Add document chunking with stable chunk IDs and parent-document metadata.
- [ ] Implement a Chinese embedding retrieval candidate.
- [ ] Implement BM25 or an equivalent lexical retrieval candidate.
- [ ] Implement hybrid fusion and an optional reranker behind configuration.
- [ ] Compare baseline, lexical, embedding, and hybrid strategies on the same
  frozen retrieval cases.
- [ ] Report Recall@3, MRR, citation accuracy, latency, memory footprint, and
  local hardware requirements.
- [ ] Select a default strategy from evidence, not architectural fashion.

**Definition of done:** an experiment report explains whether RAG V2 improves
retrieval and citation outcomes enough to justify its latency and operational
cost.

## P1 — Product analytics and evaluation dashboard

- [ ] Define privacy-safe events such as consultation started, route selected,
  clarification requested, source opened, answer completed, reset selected,
  and provider error; do not log raw health text by default.
- [ ] Define the North Star metric as **safe, evidence-supported task
  completion**, with an operational proxy documented until user research is
  available.
- [ ] Build a local evaluation dashboard with scenario filters and comparisons
  across model/retrieval versions.
- [ ] Show guardrail metrics next to task-success metrics so aggregate quality
  cannot hide safety regressions.
- [ ] Add a short analysis notebook or report containing at least one segmented
  failure analysis and one recommendation based on data.

**Definition of done:** a reviewer can identify the largest failure segment and
trace a product decision back to measured evidence.

## P1 — Demonstrate the existing Skill

- [ ] Add a repository-level before/after demo showing a candidate source,
  metadata check, dry run, SHA-256 generation, corpus update, validation, and
  coverage report.
- [ ] Record terminal output or a short GIF/video without secrets or patient
  data.
- [ ] Explain how the developer Skill differs from the user-facing health
  agent.

**Definition of done:** a recruiter can understand the Skill's input, actions,
guardrails, and output without opening `SKILL.md`.

## P2 — Add one evaluation Skill

- [ ] Create `evaluate-health-agent` only after the evaluation harness and
  report format are stable.
- [ ] Make the Skill run a selected dataset, classify failures, calculate
  metrics, compare against a baseline, and produce the release report.
- [ ] Include deterministic scripts for metric calculation and references for
  the evaluation schema and release policy.
- [ ] Validate and forward-test the Skill with realistic prompts.

We will **not** create a separate `audit-health-agent-release` Skill yet. At
this stage it would largely duplicate the evaluation workflow. Split it out
only when release auditing has distinct inputs, owners, or compliance gates.

## P2 — Demo UI and deployment

- [x] Provide a clear local web demo with question input, source links, safety
  routing, multi-turn memory, and an inspectable agent trace.
- [ ] Add a development-only evaluation view; do not expose internal evaluation
  controls as patient-facing features.
- [ ] Add structured response sections and streaming only if they improve
  completion or perceived latency in testing.
- [ ] Containerize the demo and use a production WSGI server.
- [ ] Deploy a public portfolio demo using synthetic/example prompts, rate
  limits, no raw-text analytics, an explicit retention policy, and prominent
  non-medical-device disclosure.
- [ ] Add screenshots and a 60–90 second walkthrough to the README.

**Definition of done:** the public demo communicates the product decision and
evaluation story in under two minutes and does not imply clinical validation.

## P2 — Portfolio packaging

- [ ] Add an architecture diagram covering the user agent, deterministic safety
  router, governed retrieval, evidence Skill, evaluation harness, and dashboard.
- [ ] Publish an evaluation report and RAG experiment report with reproducible
  commands.
- [ ] Add a concise “What I owned” section distinguishing inherited GPT-2 code
  from new work.
- [ ] Add English-first screenshots, demo links, and case-study links to the
  README; retain the Chinese README.
- [ ] Prepare three resume variants emphasizing AI PM, Data Analytics, and
  Applied AI outcomes without changing the underlying facts.

## Six-week working timeline

| Dates | Milestone | Deliverable / acceptance signal |
|---|---|---|
| Aug 11–13 | Baseline and product framing | Case study and this roadmap published; current tests and corpus audit recorded |
| Aug 14–20 | Evaluation MVP | Schema, 80 reviewed cases, deterministic runner, first segmented report |
| Aug 21–27 | RAG experiment | Keyword/BM25/embedding/hybrid comparison on frozen retrieval cases |
| Aug 28–Sep 3 | Analytics layer | Metric dictionary, privacy-safe events, evaluation dashboard, failure analysis |
| Sep 4–10 | Skills and release workflow | Evidence Skill demo plus validated `evaluate-health-agent` Skill |
| Sep 11–17 | Portfolio demo | Deployment hardening, public demo, screenshots, walkthrough, architecture diagram |
| Sep 18–20 | Resume packaging | Final case study, measured results, role-specific bullets, interview narrative |

## Product decisions we will preserve

- Keep emergency routing deterministic because the cost of a generative routing
  miss is unacceptable for a research health-information interface.
- Keep agent autonomy bounded because additional loops and tools add failure
  surfaces without a demonstrated user benefit here.
- Keep source citations separate from model text so provenance remains
  inspectable and links cannot be fabricated invisibly inside prose.
- Keep local-first inference as the default for privacy, demo cost, and offline
  reproducibility; measure its quality and latency instead of claiming it is
  universally superior.
- Keep project-authored summaries explicitly separate from clinical review and
  evidence grading.

## Explicit non-goals for this portfolio phase

- Diagnosing users, selecting treatment, prescribing medication, or replacing
  clinicians
- Claiming medical-device status, clinical validation, or regulatory compliance
- Collecting real patient data for the evaluation set
- Adding autonomous write tools or multi-agent complexity without a measured
  product need
- Adding a vector database solely to make the architecture look more advanced
