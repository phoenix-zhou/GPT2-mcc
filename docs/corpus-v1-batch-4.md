# Corpus v1 Batch 4: Acute Warning Signs and Medication Safety

**Review date:** 2026-08-14

**Mechanical status:** passed

**Clinical review:** not performed

## Decision summary

Batch 4 adds five project-authored Chinese summaries. Two records complete the
`neurological_warning_signs` cluster, two complete
`cardiovascular_warning_signs`, and one starts
`allergy_and_medication_safety` with antimicrobial-resistance education. The
corpus advances from 12/24 to 17/24 records, with five of eight clusters meeting
both the document and source-diversity targets.

All records remain `project_summary_unverified_by_clinician`; evidence grade is
`not_assessed`, and source reuse is `source-terms-apply`.

## Source review

| Record | Canonical source | Source date captured | Intended use | Boundary |
|---|---|---|---|---|
| `nhc-stroke-warning-signs-2026-08-review` | [NHC: 27 October 2025 press briefing](https://www.nhc.gov.cn/xcs/c100122/202510/13e1060bbb0a44ed9c1bc31bc326aadd.shtml) | Published 2025-10-27; project reviewed 2026-08-14 | China-specific “Stroke 120” recognition and urgent escalation | Official health communication; no stroke subtype inference or self-medication |
| `who-meningitis-warning-signs-2026-08-review` | [WHO: Meningitis](https://www.who.int/news-room/fact-sheets/detail/meningitis) | Fact sheet dated 2025-04-01; project reviewed 2026-08-14 | Neurological warning signs, including infant presentations | Emergency recognition only; no diagnosis or antimicrobial selection |
| `who-cardiovascular-warning-signs-2026-08-review` | [WHO: Cardiovascular diseases](https://www.who.int/news-room/fact-sheets/detail/cardiovascular-diseases-(cvds)) | Fact sheet dated 2025-07-31; project reviewed 2026-08-14 | Heart-attack warning signs across common and less typical presentations | No cause attribution, risk scoring, or medication advice |
| `cdc-heart-attack-warning-signs-2026-08-review` | [CDC: About Heart Attack](https://www.cdc.gov/heart-disease/about/heart-attack.html) | Page dated 2024-10-24; project reviewed 2026-08-14 | Symptom recognition and urgent help seeking | 911 is U.S.-specific; other jurisdictions use local emergency services |
| `who-antimicrobial-resistance-safety-2026-08-review` | [WHO: Antimicrobial resistance](https://www.who.int/news-room/fact-sheets/detail/antimicrobial-resistance) | Fact sheet dated 2026-07-16; project reviewed 2026-08-14 | Why inappropriate antimicrobial use is unsafe | No determination that an individual needs an antimicrobial; no drug, dose, or stopping advice |

## Review of user-supplied pages

One supplied page was selected: the WHO antimicrobial-resistance fact sheet.
The remaining pages were reviewed but not forced into the runtime corpus:

- the supplied NHC URL returned a 412 response to automated review and could
  not be bound to verified page-level metadata, so it remains quarantined;
- [WHO Dementia](https://www.who.int/news-room/fact-sheets/detail/dementia)
  describes a progressive condition and does not match the current cluster's
  time-sensitive neurological-warning scope;
- [WHO Hepatitis B](https://www.who.int/news-room/fact-sheets/detail/hepatitis-b)
  is a valid fact sheet, but the fever-and-infection cluster already meets its
  target and disease-specific expansion is not a current coverage gap;
- the [Global Patient Safety Action Plan](https://www.who.int/teams/integrated-health-services/patient-safety/policy/global-patient-safety-action-plan)
  is a health-system policy framework rather than patient-facing query evidence;
- [World Patient Safety Day 2026](https://www.who.int/news-room/events/detail/2026/09/17/default-calendar/world-patient-safety-day--17-september-2026---noncommunicable-diseases)
  is a future campaign page, not stable patient guidance.

These exclusions are scope decisions, not judgments that the organizations or
pages lack authority.

## Evaluation impact

Five source-specific retrieval cases were added, and overlapping stroke and
heart-attack relevance labels were updated. The development set changes from
83 cases / version `1.3.0` to 88 cases / version `1.4.0`. Historical provider
runs remain attached to their original datasets.

The 17-document component replay uses no model or API calls:

| Strategy | Recall@3 | MRR | No-hit accuracy |
|---|---:|---:|---:|
| Keyword | 73.5% | 73.5% | 89.7% |
| BM25 (`minimum_score=5.5`) | 73.5% | 75.0% | 89.7% |

At the previous BM25 threshold of 4.5, recall was 77.5% but no-hit accuracy
fell to 82.8%. The development sweep selected 5.5 to restore the Keyword
guardrail; BM25 then had no Recall@3 gain. Keyword therefore remains the
production default. This is development tuning, not a holdout estimate.

Known misses and false hits remain visible in the generated
[`retrieval_experiment.md`](../evaluation/reports/corpus-v1-batch-4/retrieval_experiment.md).

## Validation

- 17 documents from 4 approved sources passed governance and freshness checks;
- coverage is 17/24 with a 7-document gap and 5/8 clusters meeting both targets;
- the dataset contains 88 synthetic, project-reviewed cases and no personal data;
- retrieval regression tests cover all five new records and an unrelated code
  hard negative;
- no summary is marked clinician-reviewed, evidence-graded, or openly licensed.

---

# 中文摘要：Corpus v1 第四批急性警示与用药安全资料

第四批新增 5 条项目自编中文摘要：国家卫生健康委与 WHO 补齐神经系统危险信号，
WHO 与 CDC 补齐心血管危险信号，用户提供的 WHO 抗微生物药物耐药页面成为过敏与
用药安全主题的第一条资料。语料从 12/24 提升到 17/24，达到文档数和来源多样性
目标的主题从 3/8 提升到 5/8。

其余用户提供页面没有被强行入库：痴呆不属于急性神经危险信号；乙肝对应的感染
主题已经达标；全球患者安全行动计划属于政策框架；2026 患者安全日是未来活动页；
国家卫健委链接因自动访问返回 412，无法完成页面级元数据核验，暂时隔离。这里的
暂缓是覆盖范围和治理决定，不代表否定来源权威性。

开发集从 83 条 / 1.3.0 升级为 88 条 / 1.4.0。17 文档组件回放中，Keyword 与
BM25 的 Recall@3 均为 73.5%，No-hit Accuracy 均为 89.7%；BM25 的 MRR 为
75.0%，略高于 Keyword 的 73.5%，但没有 Recall@3 增益。旧阈值 4.5 虽有 77.5%
Recall@3，却把 No-hit Accuracy 降至 82.8%，因此阈值调整到 5.5，生产默认继续
保持 Keyword，等待作者隔离的盲测 Holdout。
