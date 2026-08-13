# RAG V2 Experiment: Keyword Baseline vs BM25 Candidate

[English](#english) | [简体中文](#简体中文)

## English

### Decision summary

BM25 passes the **development candidate gate**, but keyword retrieval remains
the production default. On the frozen 80-case health MVP, the BM25 end-to-end
capture increased the deterministic task-success proxy from **72.50% to
78.75%** and prediction source recall from **62.50% to 75.00%**. Emergency
recall and citation-ID validity remained 100%, provider errors remained zero,
and local API cost remained zero.

This is not yet sufficient to claim that BM25 caused the full improvement.
The threshold was selected on the same development set, and keyword and BM25
Qwen outputs were captured in separate runs. Planner variation is therefore a
confounder. The next promotion gate is an independently labelled holdout or a
paired deterministic replay that isolates retrieval context.

### Product hypothesis and guardrails

**Hypothesis:** dependency-free Chinese lexical retrieval can recover useful
paraphrases that exact keyword matching misses, without making unsupported
sources appear for unrelated questions.

The candidate must improve retrieval and end-to-end task outcomes while not
regressing:

- emergency recall and false-positive rate;
- irrelevant-query no-hit accuracy;
- citation-ID validity and provider error rate;
- local-first operating cost;
- bounded tool and safety-routing behavior.

### Experiment design

- Corpus: three governed, project-authored Chinese health summaries.
- Dataset: frozen `health_mvp_v1`, 80 synthetic and project-reviewed cases.
- Component slice: 55 non-emergency cases with retrieval checks; 24 have a
  relevant governed document and 31 expect no hit.
- Baseline: the original exact keyword/token scorer, preserved unchanged.
- Candidate: dependency-free BM25 over Latin tokens and deterministic Chinese
  character bi/trigrams.
- Candidate threshold: `minimum_score=2.0`, selected by a declared development-
  set sweep.
- End-to-end model: local `Qwen3-4B-Instruct-2507-4bit` on an Apple M1 Pro with
  16 GB unified memory; no paid API calls.

### Results

#### Isolated retrieval

| Metric | Keyword | BM25 | Delta |
|---|---:|---:|---:|
| Recall@3 | 0.6250 | 0.7083 | +0.0833 |
| MRR | 0.6250 | 0.7083 | +0.0833 |
| No-hit accuracy | 0.9032 | 0.9677 | +0.0645 |
| P95 retrieval latency | 0.0123 ms | 0.0192 ms | +0.0069 ms |
| Materialized index | none | 15,967 bytes | +15,967 bytes |

#### Local-Qwen end to end

| Metric | Keyword | BM25 | Delta |
|---|---:|---:|---:|
| Task-success proxy | 0.7250 | 0.7875 | +0.0625 |
| Planner route accuracy | 0.8125 | 0.8375 | +0.0250 |
| Prediction source recall | 0.6250 | 0.7500 | +0.1250 |
| Citation-ID validity | 1.0000 | 1.0000 | 0 |
| Emergency recall | 1.0000 | 1.0000 | 0 |
| Emergency false-positive rate | 0.0909 | 0.0909 | 0 |
| Provider errors | 0 | 0 | 0 |
| Model calls | 95 | 94 | -1 |
| Local API cost | 0 | 0 | 0 |
| P95 end-to-end latency | 13.44 s | 17.51 s | +4.06 s |

Latency was observed in two separate local runs and is sensitive to machine
load. It is not a controlled causal benchmark.

### Failure analysis

BM25 reduced source-recall failures from nine to six, missing seven relevant
component cases instead of nine. It also reduced false hits on expected no-hit
cases from three to one. Remaining misses concentrate on paraphrases and
synonyms for stroke, heart attack, and crisis support. At the Agent layer,
failure categories still include evidence-route misses, missing clarification,
scope-control failures, and conservative unnecessary escalation. Those are
Planner, policy, or safety-router problems—not all RAG problems.

### Why embeddings and hybrid retrieval are deferred

The corpus currently contains only three short records. Adding an embedding
model and vector store now would add download size, memory, latency, and
evaluation complexity without proving value over a strong lexical candidate.
Chunking, Chinese embeddings, fusion, and reranking remain roadmap experiments
for a larger governed corpus with an independent retrieval holdout.

### Reproduce

```bash
python scripts/run_retrieval_experiment.py

python scripts/capture_predictions.py \
  --output evaluation/predictions/qwen-local-bm25-health-mvp-v1.jsonl \
  --retrieval-strategy bm25 \
  --model-label mlx-community/Qwen3-4B-Instruct-2507-4bit

python scripts/run_evaluation.py \
  --predictions evaluation/predictions/qwen-local-bm25-health-mvp-v1.jsonl \
  --output-dir evaluation/reports/qwen-local-bm25-health-mvp-v1

python scripts/compare_evaluation_reports.py \
  evaluation/reports/qwen-local-health-mvp-v1/health_mvp_v1.json \
  evaluation/reports/qwen-local-bm25-health-mvp-v1/health_mvp_v1.json \
  --output-dir evaluation/reports/rag-v2
```

Machine-readable and Markdown artifacts are committed under
`evaluation/reports/rag-v2/`.

## 简体中文

### 决策摘要

BM25 已通过**开发集候选门槛**，但 Keyword 仍是生产默认方案。在冻结的 80 个
健康 MVP 案例中，BM25 端到端运行将确定性任务成功代理指标从 **72.50% 提升到
78.75%**，预测来源召回从 **62.50% 提升到 75.00%**。急症召回和引用 ID
有效性保持 100%，Provider 错误仍为 0，本地 API 成本仍为 0。

目前不能声称全部提升都由 BM25 因果导致：阈值和评估使用了同一开发集，Keyword
与 BM25 的 Qwen 输出也来自两次独立运行，Planner 波动属于混杂因素。下一道晋级
门槛应是独立标注的留出集，或固定 Planner 输出、只替换检索上下文的成对回放。

### 产品假设与护栏

**假设：** 不引入额外依赖的中文 lexical retrieval，可以找回精确关键词匹配遗漏
的同义表达，同时不会为无关问题返回不受支持的资料。

候选方案必须改善检索和端到端任务结果，并且不得损害急症指标、无命中准确率、
引用有效性、Provider 错误率、本地优先成本，以及有界工具和安全路由行为。

### 实验设计与结果

- 语料：3 篇受治理的项目自编中文健康摘要。
- 数据集：冻结的 `health_mvp_v1`，80 个合成且经项目复核的案例。
- 组件切片：55 个包含检索检查的非急症案例，其中 24 个应命中文档，31 个应无命中。
- 基线：原有 Keyword scorer，行为保持不变。
- 候选：对英文 token 和中文二/三字 n-gram 计算 BM25，无外部依赖。
- 阈值：`minimum_score=2.0`，由公开记录的开发集 sweep 选择。
- 模型：Apple M1 Pro、16 GB 统一内存上的本地 Qwen 4-bit；无付费 API。

组件实验中，Recall@3 从 0.6250 提升到 0.7083，无命中准确率从 0.9032
提升到 0.9677；端到端任务成功代理指标从 0.7250 提升到 0.7875，预测来源
召回从 0.6250 提升到 0.7500。急症召回、急症误报率、引用 ID 有效性、错误数
和 API 成本没有退化。两次运行的 P95 延迟从 13.44 秒变为 17.51 秒，但本地
机器负载不可控，因此不能把该差值当作 BM25 的严格延迟因果效应。

### 失败分析与下一步

BM25 将来源召回失败从 9 个降到 6 个，将无关问题误命中从 3 个降到 1 个。
剩余检索失败集中在卒中、心梗和危机支持的同义/改写表达。Agent 仍存在工具路由、
澄清、范围控制和保守升级错误；这些并不全是 RAG 问题。

当前语料只有 3 篇短文档，立即加入 Embedding 模型和向量数据库会增加下载、内存、
延迟与评估成本，却未必产生可验证收益。因此 Chunking、中文 Embedding、Hybrid
Fusion 和 Reranker 保留到语料扩充并建立独立留出集之后。完整可复现命令见上方
英文部分，报告位于 `evaluation/reports/rag-v2/`。
