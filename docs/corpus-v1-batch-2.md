# Corpus v1 Batch 2: Respiratory Symptoms

**Review date:** 2026-08-14

**Mechanical status:** passed

**Clinical review:** not performed

## Decision summary

Batch 2 adds three independently authored Chinese summaries to the
`respiratory_symptoms` cluster. The records intentionally cover three different
retrieval intents: general respiratory illness and higher-risk groups, urgent
breathlessness triage, and child-pneumonia warning signs. The cluster now meets
its target of three documents and its minimum of two sources, with one record
each from CDC, NHS, and WHO.

This is a governed-coverage milestone, not a claim of medical completeness or
clinical validity. Every record remains
`project_summary_unverified_by_clinician`, its evidence grade is
`not_assessed`, and source reuse is `source-terms-apply`.

## Source review

| Record | Canonical source | Source date captured | Intended use | Boundary |
|---|---|---|---|---|
| `cdc-respiratory-illnesses-2026-08-review` | [CDC: About Respiratory Illnesses](https://www.cdc.gov/respiratory-viruses/about/index.html) | Page dated 2025-08-18; project reviewed 2026-08-14 | Common symptoms, higher-risk groups, adult emergency warnings | U.S. public-health framing; no treatment selection |
| `nhs-shortness-of-breath-2026-08-review` | [NHS: Shortness of breath](https://www.nhs.uk/symptoms/shortness-of-breath/) | Page reviewed 2024-01-30; project reviewed 2026-08-14 | Urgent and emergency escalation for breathlessness | NHS 111, 999, and A&E apply only to the UK |
| `who-child-pneumonia-2026-08-review` | [WHO: Pneumonia in children](https://www.who.int/news-room/fact-sheets/detail/pneumonia) | Fact sheet dated 2022-11-11; project reviewed 2026-08-14 | Child respiratory warning signs and risk factors | No diagnosis, antibiotic choice, or dosing |

The summaries are concise project-authored transformations rather than copied
source passages. They do not diagnose the cause of cough or breathlessness,
recommend antibiotics, calculate doses, or provide patient-specific treatment.

## Chinese-government discovery portals

The user supplied two official Chinese portals for future source discovery:

- [National Health Commission information portal](https://www.nhc.gov.cn/wjw/xinx/xinxi.shtml)
- [National Medical Products Administration data search](https://www.nmpa.gov.cn/datasearch/home-index.html)

They are not added to the runtime source registry in this batch. The NHC page
is an index for locating a specific guidance document; the NMPA application is
a regulatory-record lookup interface. A portal URL alone does not provide the
title, publication date, applicability, and stable content needed for a
governed evidence record. Future batches may register `nhc` or `nmpa` only
after a concrete canonical page is reviewed. NMPA records may verify a product's
regulatory status but must not be converted into patient-specific medication
advice.

## Evaluation impact

Corpus expansion invalidated two existing labels. “普通感冒一般需要关注什么” now
has a relevant CDC document, while the NHS query about chest tightness and
breathlessness now has two relevant NHS documents. The development dataset was
therefore versioned from `1.1.0` to `1.2.0`; historical provider prediction runs
remain historical and are not presented as results for the new corpus.

The nine-document component replay uses no model or API calls:

| Strategy | Recall@3 | MRR | No-hit accuracy |
|---|---:|---:|---:|
| Keyword | 61.5% | 59.6% | 89.7% |
| BM25 (`minimum_score=4.0`) | 65.4% | 63.5% | 89.7% |

At the previous BM25 threshold of 3.0, no-hit accuracy fell to 79.3%. The
development-set sweep selected 4.0 as the highest-recall tested point that
restored the Keyword no-hit guardrail. This is tuning evidence, not an unbiased
performance estimate. Keyword remains the production default until an
independent holdout confirms the comparison.

Known misses and false hits remain visible in the generated
[`retrieval_experiment.md`](../evaluation/reports/corpus-v1-batch-2/retrieval_experiment.md).
Most notably, the ordinary-cold query still misses under both lexical methods,
showing that adding a relevant document does not guarantee its retrieval.

## Validation

- 9 documents from 3 approved sources passed governance and freshness checks;
- coverage is 9/24 with a 15-document gap and 2/8 clusters meeting both targets;
- respiratory intent regression tests cover general symptoms, emergency
  breathlessness, child warning signs, and an unrelated code hard negative;
- all 92 automated regression and security tests passed;
- no summary is marked clinician-reviewed, evidence-graded, or openly licensed.

---

# 中文摘要：Corpus v1 第二批呼吸系统资料

第二批新增 CDC、NHS、WHO 各一条项目自编中文摘要，分别覆盖一般呼吸道症状与
高风险人群、呼吸困难紧急分级、儿童肺炎警示信号。呼吸系统主题群现已达到三条
文档和至少两个来源的门槛；整个语料为 9/24，仍有 15 条缺口。

所有摘要都保持“未经临床人员审核”“证据等级未评估”“来源条款适用”。它们
不诊断咳嗽或气短的原因，不推荐抗生素，不计算剂量。NHS 的 111、999 和 A&E
只适用于英国，其他地区必须使用当地医疗或急救服务。

国家卫健委信息页和国家药监局数据查询页被记录为后续的发现与核验入口，但本批
没有把门户首页直接写入语料。只有具备具体标题、稳定正文、发布日期和适用范围的
权威页面，才能先登记来源再进入运行时语料；药监局记录只能支持监管状态核验，
不能据此生成个体化用药建议。

语料变化使两个旧标签失效，因此开发集升级到 1.2.0。九文档回放中，Keyword 的
Recall@3 / No-hit Accuracy 为 61.5% / 89.7%；BM25 在阈值 4.0 时为 65.4% /
89.7%。旧阈值 3.0 会使 No-hit Accuracy 降至 79.3%，所以不能继续沿用。BM25
仍只是开发候选，生产默认保持 Keyword，等待独立 Holdout 验证。
