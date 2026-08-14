# Corpus v1 Batch 1: Gastrointestinal Symptoms

**Review date:** 2026-08-14

**Mechanical status:** passed

**Clinical review:** not performed

## Decision summary

Batch 1 adds three independently authored Chinese summaries to the
`gastrointestinal_symptoms` cluster. The cluster now meets its declared target
of three documents and exceeds its minimum of two sources, with one record each
from NHS, CDC, and WHO.

This is a coverage milestone, not a clinical-validity claim. All summaries
remain `project_summary_unverified_by_clinician`, evidence grade remains
`not_assessed`, and source reuse remains `source-terms-apply`.

## Source review

| Record | Canonical source | Source date captured | Intended use | Jurisdiction caveat |
|---|---|---|---|---|
| `nhs-diarrhoea-vomiting-2026-08-review` | [NHS: Diarrhoea and vomiting](https://www.nhs.uk/symptoms/diarrhoea-and-vomiting/) | Page reviewed 2023-12-21; project reviewed 2026-08-14 | General symptoms, hydration, and escalation signals | NHS 111/999 instructions apply to the UK |
| `cdc-norovirus-symptoms-2026-08-review` | [CDC: About Norovirus](https://www.cdc.gov/norovirus/about/index.html) | Page dated 2024-04-24; project reviewed 2026-08-14 | Norovirus symptoms and dehydration signs | U.S. public-health framing |
| `who-diarrhoeal-disease-2026-08-review` | [WHO: Diarrhoeal disease](https://www.who.int/news-room/fact-sheets/detail/diarrhoeal-disease) | Fact sheet dated 2024-03-07; project reviewed 2026-08-14 | Definition, dehydration risk, and escalation | Global guidance with strong child-health emphasis |

The records do not diagnose the cause of diarrhoea, recommend antibiotics,
calculate doses, or copy long source passages.

## Evaluation impact

Adding evidence changed the meaning of an existing development case. The case
“轻微腹泻一天应该记录哪些信息” was no longer a valid expected no-hit, so its
relevant-document labels were updated and the dataset version moved from
`1.0.0` to `1.1.0`. Historical Qwen prediction runs remain attached to v1.0.0
and are intentionally rejected by the v1.1.0 evaluator until recaptured.

The six-document component replay uses no model or API calls:

| Strategy | Recall@3 | MRR | No-hit accuracy |
|---|---:|---:|---:|
| Keyword | 64% | 62% | 90% |
| BM25 (`minimum_score=3.0`) | 72% | 72% | 90% |

The old BM25 threshold of 2.0 reduced no-hit accuracy after corpus expansion.
The development-set sweep selected 3.0 as the highest-recall tested threshold
that matched the Keyword no-hit guardrail. This is still a tuned development
candidate; Keyword remains the production default until blind-holdout replay.

Known failures remain visible in the generated
[`retrieval_experiment.md`](../evaluation/reports/corpus-v1-batch-1/retrieval_experiment.md),
including quoted-phrase hard negatives and a BM25 miss on the newly relabelled
light-diarrhoea case.

## Validation

- 6 documents from 3 approved sources passed governance and freshness checks;
- the coverage report shows 6/24 documents, an 18-document gap, and 1/8 topic
  clusters meeting both document and source targets;
- all 90 automated tests passed;
- no summary is marked clinician-reviewed, evidence-graded, or openly licensed.

---

# 中文摘要：Corpus v1 第一批胃肠道资料

第一批新增 NHS、CDC、WHO 各一条项目自编中文摘要，使
`gastrointestinal_symptoms` 成为第一个同时满足三条文档和至少两个来源门槛的
主题群。当前总覆盖为 6/24，仍有 18 条缺口。

三条摘要都只用于一般健康信息，不诊断腹泻原因、不推荐抗生素、不计算剂量，且
仍明确标记为“未经临床人员审核”“证据等级未评估”“来源条款适用”。NHS 的
111/999 指引具有英国地区限制，不能直接替换其他地区的医疗服务号码。

语料扩充后，原来标记为 No-hit 的“轻微腹泻”案例已经有相关资料，因此开发集从
1.0.0 升级到 1.1.0。旧 Qwen 结果继续作为 1.0.0 历史快照，不得冒充新语料的
端到端结果。六文档组件回放中，Keyword 的 Recall@3 为 64%、No-hit Accuracy
为 90%；BM25 在阈值 3.0 时分别为 72% 和 90%。BM25 仍只是开发集候选，必须通过
盲测 Holdout 才能替换默认 Keyword。
