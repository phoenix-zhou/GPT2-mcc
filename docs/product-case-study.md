# ClearCare Health — Governed Healthcare AI Agent Product Case Study

Status: working case study; current repository behavior is distinguished from
planned validation work.

## Executive summary

ClearCare Health is a vertical, local-first, evidence-grounded health-
information agent designed to explore a
product question: **how can an LLM help a person organize a health question
without presenting itself as a clinician?**

The product combines deterministic emergency routing, bounded agent autonomy,
governed sources, visible citations, and multi-turn clarification. It does not
provide diagnosis, prescriptions, or treatment decisions. The next product
milestone is not more autonomy; it is a reproducible evaluation system that can
measure safety, retrieval, grounding, usability proxies, latency, and cost.

## Problem

General-purpose LLM health answers create several product risks:

1. A fluent answer can appear more certain than its evidence supports.
2. A model can miss or understate a time-sensitive emergency signal.
3. Citations can be absent, fabricated, or disconnected from the claim.
4. A user may provide too little context and interpret a generic answer as a
   diagnosis.
5. Sending sensitive text to a cloud model can conflict with user expectations.
6. A more autonomous agent introduces additional tool and control failures
   without necessarily improving the user's outcome.

ClearCare addresses these risks as product constraints, not as claims that an
LLM can make clinical decisions safely.

## Target users and jobs to be done

### Primary user

An adult seeking general, non-diagnostic health information before deciding
what kind of professional help or additional information may be appropriate.

**Job to be done:** “Help me organize what is happening, identify important
warning signs or missing context, and show me the source of general information
without pretending to diagnose me.”

### Secondary user

A developer or content maintainer responsible for keeping the agent's evidence
corpus traceable and current.

**Job to be done:** “Help me add and audit health guidance through a repeatable
workflow that preserves provenance and does not overstate clinical review.”

### Non-users

- People seeking emergency response, diagnosis, prescriptions, or treatment
  decisions
- Clinicians expecting a clinical decision-support or medical-record system
- Organizations expecting a validated or regulated medical device

## User journey

1. **Arrival:** the user sees the local-first and non-diagnosis boundaries.
2. **Initial question:** the user describes a symptom or health-information
   need without entering identifying information.
3. **Safety route:** strong emergency signals are handled by deterministic
   guidance before any generative call.
4. **Agent plan:** for non-emergency input, the bounded planner chooses one
   allow-listed action: retrieve evidence, ask for essential clarification, or
   respond without a tool.
5. **Evidence and answer:** the system generates a response and displays source
   links separately when governed material was retrieved.
6. **Follow-up:** the user adds only new context; recent turns are carried
   forward in bounded in-memory state.
7. **Inspection or reset:** the user can inspect the action trace or start a new
   consultation and clear the current in-memory history.

## Key product decisions

### Deterministic emergency routing

Strong emergency phrases are checked before the LLM. This reduces dependence
on model variability for a narrow, high-cost routing decision and makes the
behavior directly testable. The router can still produce false positives and
false negatives; it is a guardrail, not a diagnostic classifier.

### Bounded autonomy

The agent performs one plan/tool/respond cycle with at most one read-only tool
call. In a high-risk domain, additional loops or write tools require evidence
that they improve user outcomes enough to justify larger failure surfaces.

### Governed sources only

Retrieval is limited to repository-controlled records with approved source IDs,
provenance metadata, review dates, reuse status, and content hashes. Source
authority does not prove that a project-authored summary is clinically valid,
so review status and evidence grade remain explicit.

### Separate citations from generated prose

Sources are rendered from retrieved records rather than trusted from arbitrary
links generated inside the answer. This makes provenance inspectable and allows
citation validity to be evaluated independently from writing quality.

### No diagnosis

The intended product task is health-information organization and
signposting—not deciding what condition a person has. This boundary appears in
the interface, prompts, evidence workflow, and evaluation roadmap.

### Local-first, with explicit cloud enhancement

Local Qwen is the default to improve offline reproducibility, avoid per-token
API fees, and better match the expectation that a local demo will not send text
to a third party. OpenAI is an explicit per-request option when enabled by the
server. Local inference is not assumed to be better; quality and latency must
be compared in evaluation.

## Trade-offs

| Decision | Benefit | Cost / limitation |
|---|---|---|
| Deterministic emergency rules | Testable and independent of model variability | Incomplete linguistic coverage and possible false alarms |
| One bounded agent cycle | Easier to inspect, test, and constrain | Cannot perform complex iterative research |
| Governed local corpus | Traceable sources and stable evaluation | Small coverage and ongoing maintenance burden |
| Local Qwen default | Offline demo, predictable API cost, clearer data boundary | Hardware requirements and potentially lower quality or higher latency |
| In-memory conversation state | Simple local demo and automatic expiry on restart | Not horizontally scalable and unsuitable for production retention needs |
| Project-authored summaries | Concise Chinese context for the model | Not equivalent to source text, evidence grading, or clinical review |

## Success framework

### North Star

**Safe, evidence-supported task completion:** the share of eligible
consultations in which the user receives an understandable, appropriately
bounded response with valid supporting evidence when evidence is required, and
without a guardrail failure.

This is a product definition, not yet a measured result. Until user research is
available, the project will report a transparent operational proxy composed of
task completion, route correctness, citation validity, and unsupported-claim
checks.

### Guardrail metrics

- Emergency recall and false-positive rate
- Unsupported-claim rate
- Citation validity and citation entailment
- Unsafe or diagnostic recommendation rate
- Privacy-policy violations in stored analytics
- Provider and runtime failure rate

### Quality and efficiency metrics

- Clarification precision and task completion
- Retrieval Recall@K and MRR
- Groundedness by scenario
- Source-open rate in usability testing or a consented demo study
- P50/P95 latency
- Model calls and estimated cloud cost per completed consultation

No metric values are claimed until the versioned evaluation harness produces
them.

## Current evidence and limitations

As of 2026-08-15:

- 98 automated code, evaluation, security, and Skill tests pass.
- The corpus validator accepts 19 records from 5 approved sources.
- All 19 records are project-authored Chinese summaries marked as not reviewed
  by a clinician.
- All 19 records have an evidence grade of `not_assessed`.
- Production retrieval remains Keyword; a deterministic BM25 candidate is
  measured separately and has not passed an independent holdout.
- A 90-case synthetic, project-reviewed Evaluation MVP measures deterministic
  safety routing and retrieval. The current 19-document component replay
  reports Recall@3 of 0.7500 and no-hit accuracy of 0.8966 for both Keyword and
  BM25 after threshold retuning. These development-set results are not clinical
  performance claims or independent holdout estimates.
- A complete 80-case local-Qwen run measures 81.25% planner-route accuracy,
  72.5% deterministic task-success proxy, and 13.44-second P95 case latency
  with zero provider errors and zero API cost.
- Response groundedness, human usefulness, and dashboarding are not measured yet.
- There has been no clinical validation, regulatory assessment, or production
  privacy/security review.

## Likely failure modes

1. A symptom is phrased in a way the emergency rules do not cover.
2. A conservative rule escalates a non-emergency question unnecessarily.
3. The planner retrieves when clarification is needed, or asks questions when
   a direct bounded answer would be sufficient.
4. Keyword retrieval misses a relevant document because the user uses a
   synonym or indirect description.
5. The generated answer goes beyond the retrieved evidence.
6. A valid source is presented but does not entail a nearby claim.
7. The local model produces an incomplete answer or formatting failure.
8. A user infers diagnosis despite the interface boundary.
9. A public deployment accidentally logs sensitive raw text.
10. A stale project summary remains technically valid but no longer reflects
    current guidance.

## Prioritization and roadmap

1. **Evaluation first:** build a reviewed scenario set, deterministic checks,
   failure taxonomy, and reproducible report.
2. **Measured RAG V2:** compare keyword, lexical, embedding, and hybrid options
   on the same frozen cases before selecting a default.
3. **Analytics and dashboard:** expose segmented failures, guardrail metrics,
   latency, and cost without logging raw health text by default.
4. **Developer workflow demo:** show the evidence Skill's candidate-to-audit
   lifecycle in a recruiter-readable before/after example.
5. **Evaluation Skill:** package the stable evaluation workflow as
   `evaluate-health-agent`.
6. **Deployment last:** publish a constrained portfolio demo with synthetic
   examples, rate limits, disclosure, and explicit data handling.

See [`portfolio-upgrade-roadmap.md`](portfolio-upgrade-roadmap.md) for the
dated checklist and acceptance criteria.

## What we deliberately will not build yet

- A fully autonomous medical agent
- Diagnosis, treatment selection, prescriptions, or patient-specific medical
  decisions
- Autonomous web browsing or write tools in the user-facing agent
- A vector database without a measured retrieval need
- A second release-audit Skill that duplicates the evaluation workflow
- Claims of clinical reliability based only on official source URLs

## Portfolio narrative

ClearCare should be presented as a governed, measurable LLM application—not as
a medical chatbot or a complex autonomous framework:

> Designed and evaluated a bounded, evidence-grounded agent architecture for a
> high-stakes health-information domain, combining deterministic safety routing,
> governed retrieval, inspectable tool traces, privacy-aware model selection,
> and reproducible evaluation.

The words “evaluated” and any metric results should be used on a resume only
after the P0 evaluation milestone is complete.
