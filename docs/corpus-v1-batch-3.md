# Corpus v1 Batch 3: Fever and Infection

**Review date:** 2026-08-14

**Mechanical status:** passed

**Clinical review:** not performed

## Decision summary

Batch 3 adds three project-authored Chinese summaries to
`fever_and_infection`. The records cover distinct intents: fever and respiratory
infection escalation in the Chinese context, severe infection/sepsis warning
signs, and routine infection prevention through handwashing. The cluster meets
its three-document target with three issuers and introduces the first governed
Chinese-government source.

All summaries remain `project_summary_unverified_by_clinician`, their evidence
grade is `not_assessed`, and source reuse is `source-terms-apply`.

## Source review

| Record | Canonical source | Source date captured | Intended use | Boundary |
|---|---|---|---|---|
| `nhc-fever-infection-warning-signs-2026-08-review` | [NHC: 19 December 2025 press briefing](https://www.nhc.gov.cn/xcs/c100122/202512/36f4eefdf88444d2bd571b1a4b6b6ef1.shtml) | Published 2025-12-19; project reviewed 2026-08-14 | Fever, worsening respiratory symptoms, higher-risk groups, and escalation in China | Official health communication, not a clinical guideline; no pathogen inference or medication advice |
| `who-sepsis-warning-signs-2026-08-review` | [WHO: Sepsis](https://www.who.int/news-room/fact-sheets/detail/sepsis) | Fact sheet dated 2024-05-03; project reviewed 2026-08-14 | Severe infection warning signs and vulnerable groups | Recognition and urgent help only; no self-diagnosis or treatment selection |
| `cdc-handwashing-infection-prevention-2026-08-review` | [CDC: About Handwashing](https://www.cdc.gov/handwashing/) | Page dated 2024-02-16; project reviewed 2026-08-14 | Key handwashing times, method, and sanitizer limitation | General prevention; U.S. publisher; no claim that handwashing prevents every infection |

The older 2016 NHC child-fever article and outbreak-era COVID isolation pages
were not selected. Their age, population overlap, or superseded context made
them weaker fits than the current briefing. The NMPA database was also excluded
from this topic because regulatory product records do not answer general fever
or infection questions.

## Chinese-source workflow

The bilingual [Chinese official-source discovery guide](china-official-source-discovery.md)
records reusable search queries, portal roles, page-level metadata checks, PDF
handling, and the NMPA regulatory boundary. The NHC source was registered only
after the concrete article was reviewed; the broad information portal itself
is not a runtime evidence record.

## Evaluation impact

Three source-specific retrieval cases were added for the NHC, WHO, and CDC
records. The development set changes from 80 cases / version `1.2.0` to 83
cases / version `1.3.0`. Historical provider runs remain attached to their
original 80-case datasets and are not presented as current end-to-end results.

The twelve-document component replay uses no model or API calls:

| Strategy | Recall@3 | MRR | No-hit accuracy |
|---|---:|---:|---:|
| Keyword | 65.5% | 63.8% | 89.7% |
| BM25 (`minimum_score=4.5`) | 69.0% | 67.2% | 89.7% |

At the previous BM25 threshold of 4.0, no-hit accuracy fell to 82.8%. The
development sweep selected 4.5 as the highest-recall tested point that restored
the Keyword guardrail. Keyword remains the production default pending an
independent holdout.

Known lexical misses and false hits remain visible in the generated
[`retrieval_experiment.md`](../evaluation/reports/corpus-v1-batch-3/retrieval_experiment.md).

## Validation

- 12 documents from 4 approved sources passed governance and freshness checks;
- coverage is 12/24 with a 12-document gap and 3/8 clusters meeting both targets;
- retrieval regression tests cover China-specific fever guidance, sepsis
  warnings, infection prevention, and an unrelated code hard negative;
- all 94 automated regression and security tests passed;
- no summary is marked clinician-reviewed, evidence-graded, or openly licensed.

---

# 中文摘要：Corpus v1 第三批发热与感染资料

第三批新增国家卫生健康委、WHO 和 CDC 各一条项目自编中文摘要，分别覆盖中国
语境下的发热与呼吸道感染升级信号、严重感染和脓毒症警示、洗手预防感染。该主题
群达到 3 条文档和 3 个来源，整体语料达到 12/24。

本批首次登记国家卫生健康委为受治理来源，但只绑定已核验的具体文章，不把信息
门户首页视为证据。2016 年儿童发热旧文、疫情时期的新冠居家筛查页及药监局查询
首页没有入库。药监局适合核验产品监管状态，不适合回答一般发热、感染或个体用药
问题。具体检索方法见[中国官方来源发现指南](china-official-source-discovery.md)。

开发集新增三条来源级检索案例，从 80 条 / 1.2.0 升级到 83 条 / 1.3.0。十二文档
回放中，Keyword 的 Recall@3 / No-hit Accuracy 为 65.5% / 89.7%；BM25 在阈值
4.5 时为 69.0% / 89.7%。旧阈值 4.0 会把 No-hit Accuracy 降到 82.8%，因此本批
再次完成阈值回归校准。Keyword 继续作为生产默认，等待独立 Holdout。
