# Health Corpus v1 Coverage Specification

**Status:** planning

**Corpus ID:** `health_corpus_v1`

**Target:** 24 governed records across 8 topic clusters

## Purpose

This specification defines what the first credible ClearCare retrieval corpus
must cover before documents are collected. It prevents document count from
becoming a proxy for quality and separates three different artifacts:

1. **Evidence records** contain project-authored summaries of approved public
   guidance.
2. **Retrieval evaluation cases** test paraphrases, synonyms, no-hit behavior,
   hard negatives, ambiguity, and jurisdiction differences.
3. **Clinical review** is a separate human process and is not implied by either
   of the above.

The machine-readable contract is
[`knowledge/coverage_plan.json`](../knowledge/coverage_plan.json). The coverage
report compares the live corpus with that contract.

## Product boundary

### Included

- General health information for members of the public and caregivers.
- Recognition of important warning signs and appropriate escalation language.
- Information needed to clarify an underspecified question.
- Official public-health or patient-guidance pages with traceable issuer,
  jurisdiction, review date, reuse status, and canonical HTTPS URL.
- Short Chinese summaries authored by this project and linked to the original
  source.

### Excluded

- Diagnosis, prognosis, prescribing, dose calculation, treatment selection,
  or individualized risk scoring.
- Patient records, user conversations, scraped forums, marketing pages,
  anonymous articles, model-generated sources, and unverifiable documents.
- Claims of clinician review, evidence grading, licensing, or currentness that
  are not supported by explicit records.
- Large copied passages from source pages.

## Topic coverage

| Cluster ID | Topic | Current | Target | Gap |
|---|---|---:|---:|---:|
| `neurological_warning_signs` | Neurological warning signs / 神经系统危险信号 | 1 | 3 | 2 |
| `cardiovascular_warning_signs` | Cardiovascular warning signs / 心血管危险信号 | 1 | 3 | 2 |
| `gastrointestinal_symptoms` | Gastrointestinal symptoms / 胃肠道症状 | 0 | 3 | 3 |
| `respiratory_symptoms` | Respiratory symptoms / 呼吸系统症状 | 0 | 3 | 3 |
| `fever_and_infection` | Fever and infection / 发热与感染 | 0 | 3 | 3 |
| `allergy_and_medication_safety` | Allergy and medication safety / 过敏与用药安全 | 0 | 3 | 3 |
| `child_health` | Child health / 儿童健康 | 0 | 3 | 3 |
| `mental_health_crisis` | Mental-health crisis / 心理健康危机 | 1 | 3 | 2 |
| **Total** |  | **3** | **24** | **21** |

The targets are portfolio experiment requirements, not medical completeness
claims. A cluster is not “covered” merely because one record exists.

## Query-phenomenon matrix

The following phenomena belong in versioned evaluation data. They are not
extra evidence documents and must not contaminate source summaries.

| Phenomenon | Required test behavior | Corpus dependency |
|---|---|---|
| Ordinary information | Retrieve relevant general guidance | Positive record in a named cluster |
| Warning signs | Surface relevant evidence without replacing deterministic safety routing | Warning-sign record plus safety cases |
| Clarification needed | Ask only for information necessary to continue safely | Ambiguous or underspecified cases |
| Paraphrase | Retrieve semantically equivalent wording | Positive case variants |
| Synonym | Handle common Chinese and English terms | Governed keyword aliases and cases |
| No hit | Return no source instead of a weakly related citation | Out-of-corpus cases |
| Hard negative | Reject a lexically similar but irrelevant record | Paired positive/negative cases |
| Jurisdiction difference | Keep issuer and jurisdiction visible; do not merge incompatible guidance | Comparable records from documented jurisdictions |

## Source and reuse gate

Before a record can be added:

- the issuer must be a primary government, public-health, national health
  service, or intergovernmental health authority appropriate to the topic;
- its `source_id` and canonical domain must be approved in
  `source_manifest.json` before content is collected;
- the direct page must be inspected, and metadata that cannot be verified must
  remain `null`, `not_assessed`, `source-terms-apply`, or explicitly unverified;
- the summary must be independently authored, concise, non-diagnostic, and
  hashed by the curation workflow;
- each record must declare one controlled `topic_cluster` and the coverage gap
  it closes;
- a second source is required before a cluster can be described as
  multi-source; differing jurisdictions must remain distinguishable.

Source authority improves provenance. It does not by itself prove that the
project summary is clinically correct or that a generated answer is grounded.

## Freeze and acceptance criteria

`health_corpus_v1` may move from `planning` to `frozen` only when:

- 24 records pass schema, source-host, freshness, duplication, size, and hash
  validation;
- all 8 clusters reach their declared target and have at least 2 approved
  sources represented;
- every record has explicit provenance, applicability, reuse, version, review,
  and `topic_cluster` metadata;
- retrieval evaluation contains positive, paraphrase, synonym, no-hit, hard
  negative, ambiguity, and jurisdiction-difference cases;
- a release manifest records the corpus hash, freeze date, reviewer status,
  known gaps, and the exact evaluation split that may use it;
- no documentation describes project review as clinical validation.

Until then, reports must show status `planning` and the remaining gaps.

---

# 中文摘要：健康语料库 v1 覆盖规范

本规范先定义“需要覆盖什么”，再收集资料。目标是 8 个主题群、24 条受控记录；
数量只用于形成可比较的检索实验，不代表医疗完整性或临床可靠性。

核心边界如下：

- 知识记录只保存由项目撰写、链接到权威原始页面的一般健康信息摘要；
- Paraphrase、同义词、No-hit、Hard Negative、歧义和地区差异属于评测案例，
  不能为了凑数写进证据正文；
- 不提供诊断、处方、剂量、治疗选择或个人风险判断；
- 新来源必须先登记机构、域名、地区和复用状态，再添加内容；
- 无法确认的发布日期、证据等级、许可或临床审核状态必须明确留空或标为未确认；
- 每条记录必须声明一个受控 `topic_cluster`，并说明它填补了哪个覆盖缺口；
- 只有达到全部验收条件并记录语料哈希、冻结日期和审核状态后，才能将
  `health_corpus_v1` 从 `planning` 改为 `frozen`。

当前只有 3 条记录，分别覆盖神经系统危险信号、心血管危险信号和心理健康危机，
距离 24 条目标还差 21 条。因此本阶段的准确表述是“覆盖规范已建立、语料扩充待完成”。
