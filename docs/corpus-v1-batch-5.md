# Corpus v1 Batch 5: Allergy and Medication Safety

**Review date:** 2026-08-15

**Mechanical status:** passed

**Clinical review:** not performed

## Decision summary

Batch 5 adds two project-authored Chinese summaries and completes the
`allergy_and_medication_safety` cluster. The corpus advances from 17/24 to
19/24 records; six of eight clusters now meet both the document-count and
source-diversity targets. The NMPA is added as a fifth approved issuer.

All records remain `project_summary_unverified_by_clinician`; evidence grade is
`not_assessed`, and source reuse is `source-terms-apply`.

## Selected evidence

| Record | Canonical source | Source date captured | Intended use | Boundary |
|---|---|---|---|---|
| `nmpa-ganmaoling-label-safety-2026-08-review` | [NMPA: revision of Ganmaoling oral-product labels](https://www.nmpa.gov.cn/xxgk/ggtg/ypggtg/ypqtggtg/20260720095207120.html) | Announcement no. 66 of 2026; page dated 2026-07-20; project reviewed 2026-08-15 | China-specific label warnings about alcohol, duplicate cold-medicine ingredients, driving, and contraindications | Product-specific safety communication; no dose, interaction clearance, or individualized stop/switch advice |
| `nhs-anaphylaxis-warning-signs-2026-08-review` | [NHS: Anaphylaxis](https://www.nhs.uk/conditions/anaphylaxis/) | Page last reviewed 2023-06-21; project reviewed 2026-08-15 | Recognition of rapidly developing severe-allergy warning signs and urgent escalation | The source's 999 number is UK-specific; the summary directs other jurisdictions to local emergency services and does not diagnose ordinary rashes |

The NMPA host returned HTTP 412 to automated extraction. The canonical URL,
announcement identity, publication date, and label-revision details were
cross-checked through search indexing and pages reproducing the regulator's
announcement. This access limitation is recorded instead of implying that a
machine-readable NMPA page was captured.

## Review of the supplied links

| Supplied page | Decision | Reason |
|---|---|---|
| [NMPA prescription-drug online retail compliance interpretation](https://www.nmpa.gov.cn/xxgk/zhcjd/zhcjdyp/20260525142837100.html) | Exclude from runtime corpus | Useful product/regulatory context for platform governance, but aimed at regulated businesses rather than patient questions |
| [NMPA pregnancy and lactation allergy-medication tips](https://www.nmpa.gov.cn/xxgk/kpzhsh/kpzhshzh/20250427101227177.html) | Defer | Highly relevant topic and an official patient-education asset, but the indexed page is primarily a video entry and did not expose an auditable transcript during review |
| [NMPA Ganmaoling label revision](https://www.nmpa.gov.cn/xxgk/ggtg/ypggtg/ypqtggtg/20260720095207120.html) | Include | Concrete, current, product-specific safety communication that fills the medication-safety gap |
| [NMPA commentary on the revised drug-administration regulation](https://www.nmpa.gov.cn/zhuanti/zt2026/ypglfshshtl/ypglfshshtljdpl/20260127194050107.html) | Exclude from runtime corpus | Legal and industry-policy analysis rather than patient guidance |
| [Drug Administration Law implementation regulation](https://www.nmpa.gov.cn/xxgk/fgwj/flxzhfg/20260127172639127.html) | Exclude from runtime corpus | Authoritative law, but not evidence for answering individual health-information questions |
| [WHO Child health](https://www.who.int/health-topics/child-health#tab=tab_1) | Discovery portal | Useful for selecting concrete child-health fact sheets; too broad to ingest as one evidence record |
| [WHO Mental health](https://www.who.int/health-topics/mental-health#tab=tab_1) | Discovery portal | Useful for finding concrete crisis guidance; the current cluster also needs non-WHO source diversity |

Exclusion is a product-scope decision, not a judgment that the issuer or page is
unreliable. Deferred sources can be reconsidered when auditable text or a
stable transcript is available.

## Evaluation impact

Two source-specific retrieval cases were added. The development set advances
from 88 cases / version `1.4.0` to 90 cases / version `1.5.0`. Historical
provider runs remain attached to their original datasets.

The 19-document component replay uses no model or API calls:

| Strategy | Recall@3 | MRR | No-hit accuracy |
|---|---:|---:|---:|
| Keyword | 75.0% | 73.6% | 89.7% |
| BM25 (`minimum_score=6.5`) | 75.0% | 76.4% | 89.7% |

Corpus growth introduced a BM25 false hit in which an allergic-rhinitis query
retrieves the severe-anaphylaxis record. The development sweep raised the BM25
threshold from 5.5 to 6.5 to restore aggregate no-hit accuracy, but the cohort
error remains visible. Keyword stays the production default because BM25 does
not improve Recall@3 and has different failure cases. These are development
results, not holdout or clinical estimates.

See the generated
[`retrieval_experiment.md`](../evaluation/reports/corpus-v1-batch-5/retrieval_experiment.md)
for case-level misses and false hits.

## Validation

- 19 documents from 5 approved sources passed governance and freshness checks;
- coverage is 19/24 with a 5-document gap and 6/8 clusters meeting both targets;
- the dataset contains 90 synthetic, project-reviewed cases and no personal data;
- regression tests cover both new records and retain the allergic-rhinitis BM25 failure as an explicit known limitation;
- no summary is marked clinician-reviewed, evidence-graded, or openly licensed.

---

# 中文摘要：Corpus v1 第五批过敏与用药安全资料

第五批新增两条项目自编中文摘要：国家药监局的感冒灵口服制剂说明书修订公告，
以及 NHS 的严重过敏反应危险信号页面。过敏与用药安全主题达到 3/3，并拥有 WHO、
NMPA、NHS 三个来源；总语料从 17/24 提升到 19/24，达标主题从 5/8 提升到 6/8。

用户提供的其余链接按用途分层：处方药网络销售解读和药品管理法规适合产品治理
研究，不适合作为患者问答证据；妊娠/哺乳期过敏用药科普很有价值，但当前主要是
视频入口且未取得可审计文字稿，因此暂缓；WHO 儿童健康和心理健康页保留为下一批
具体指南的发现入口。

开发集升级为 90 条 / 1.5.0。19 文档组件回放中，Keyword 与 BM25 的 Recall@3
均为 75.0%，No-hit Accuracy 均为 89.7%；BM25 的 MRR 为 76.4%，但仍把过敏性
鼻炎查询误召回到严重过敏反应记录。阈值从 5.5 调整到 6.5 后恢复了总体 No-hit
护栏，但没有消除该分群错误，因此生产默认继续使用 Keyword，并把失败案例公开
保留到盲测阶段。
