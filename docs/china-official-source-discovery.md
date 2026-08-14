# Finding Governed Health Sources on Chinese Official Websites

This guide describes a reproducible discovery workflow for Chinese government
health sources. It is a research and provenance workflow, not medical advice.

## Start with the evidence need

Define the exact coverage gap before searching. For example:

- topic: fever and infection;
- intent: ordinary information, escalation warning, or prevention;
- population: general public, children, older adults, or another stated group;
- excluded content: diagnosis, prescriptions, dosing, and individualized care.

This prevents a broad portal search from turning into an arbitrary collection
of documents.

## Use domain-restricted search

Government sites can have limited internal search and JavaScript-heavy result
pages. A search engine with `site:` is often the fastest discovery layer:

```text
site:nhc.gov.cn 发热 感染 "发布时间"
site:nhc.gov.cn/xcs/c100122 发热 咳嗽 就医
site:nhc.gov.cn/ylyjs 流感 2025 诊疗方案
site:chinacdc.cn 流感 发热 健康提示
site:nmpa.gov.cn 药品通用名称 批准文号
```

Quotation marks help locate a phrase; adding a year helps prefer newer
material. Search results are only leads. Always open the final canonical page.

## Choose the correct Chinese portal

| Portal | Good use | Do not use it as |
|---|---|---|
| [National Health Commission information portal](https://www.nhc.gov.cn/wjw/xinx/xinxi.shtml) | Discover policies, public-health communications, press briefings, standards, and linked guidance | A single evidence record representing all NHC content |
| [NHC health-science platform](https://www.nhc.gov.cn/kppypt/index.shtml) | Discover public-facing educational material and fact checks | Proof that a summary is clinically reviewed |
| [NMPA data search](https://www.nmpa.gov.cn/datasearch/home-index.html) | Verify a product name, approval number, manufacturer or marketing-authorization holder, and regulatory status | Evidence that a product is suitable for a user, superior, or recommended |
| [Chinese Center for Disease Control and Prevention](https://www.chinacdc.cn/) | Discover surveillance reports and infectious-disease education | A substitute for checking the date, audience, and exact issuing unit |

## Verify the concrete page

For every candidate, record:

1. exact title and issuing organization;
2. canonical HTTPS URL, not a search-results URL;
3. explicit publication or update date—never infer one from a URL;
4. intended audience, population, jurisdiction, and setting;
5. whether it is public education, a policy, a clinical guideline, a standard,
   a press briefing, or a regulatory database record;
6. whether it is current, superseded, withdrawn, or obviously outbreak-specific;
7. reuse terms, or `source-terms-apply` when no open licence is stated.

Prefer a specific current page over a portal homepage or an undated repost.
For PDFs, locate the parent announcement as well as the attachment so the
issuer and publication date remain traceable.

## Apply the project boundary

A selected page can support a concise project-authored summary, but it does not
automatically justify `clinician_reviewed` or a high evidence grade. Keep
unsupported fields as `null`, `not_assessed`, or
`project_summary_unverified_by_clinician`.

NMPA records require a separate boundary: they can verify regulatory identity
and status, but cannot justify diagnosis, efficacy comparisons, prescribing,
dose calculation, or patient-specific medication recommendations.

---

# 在中国官方站点寻找受治理健康资料

先写清楚“缺什么”，再开始搜索。例如本批需要的是发热与感染主题下的一般信息、
升级警示和感染预防，不需要诊断、处方、剂量或个体化治疗。这样可以避免把门户里
所有出现“发热”的页面都收进项目。

## 最实用的搜索方式

政府网站的站内搜索有时依赖 JavaScript，使用搜索引擎的 `site:` 限定通常更快：

```text
site:nhc.gov.cn 发热 感染 "发布时间"
site:nhc.gov.cn/xcs/c100122 发热 咳嗽 就医
site:nhc.gov.cn/ylyjs 流感 2025 诊疗方案
site:chinacdc.cn 流感 发热 健康提示
site:nmpa.gov.cn 药品通用名称 批准文号
```

加入年份可以优先发现较新的材料，使用引号可以检索完整短语。但搜索结果只能作为
线索，必须打开具体正文页核验。

## 卫健委页面怎么选

优先选择具有以下信息的具体页面：

- 明确标题、发布机构和发布时间；
- 正文或可追溯附件，而不是栏目首页；
- 适用人群与场景清楚；
- 没有被新版本替代；
- 内容属于公众科普、政策解读或可明确识别的指南类型。

如果正文是 PDF，应同时保存发布通知页与 PDF 链接。只保存 PDF 下载地址，后续可能
无法说明是谁、何时、基于什么版本发布的。

## 药监局页面怎么用

国家药监局数据查询适合核验药品或器械的通用名称、批准文号、生产企业或上市许可
持有人和监管状态。应进入具体查询记录并保存关键字段，不能只保存查询首页。

“已获批”不等于“适合这个用户”，更不等于“疗效更好”。药监局数据不能直接转化
成诊断、处方、剂量或个体化用药建议。

## 最终入库前检查

每条候选必须核对：标题、发布者、规范 URL、发布日期、适用人群、地区、文档类型、
版本状态和复用条款。无法确认的内容必须保留为未知或未评估。项目自行编写的摘要
始终与原文分开，并继续标记为“未经临床人员审核”，直到有合格审核证据为止。
