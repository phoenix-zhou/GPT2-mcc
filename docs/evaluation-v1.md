# Evaluation v1: Provider Prediction Contract

[English](#english) | [简体中文](#简体中文)

## English

### Outcome

Evaluation v1 extends the deterministic component baseline with a provider-neutral
prediction contract. Captured Qwen, OpenAI, or future provider outputs can be
evaluated by the same harness without importing a provider SDK or rerunning a
paid model. Prediction files are resumable, versioned artifacts and reference
evaluation cases by ID instead of copying raw prompts.

This stage implements the contract, resumable capture, deterministic scoring,
and one complete local-Qwen run. It does **not** claim clinical validation or
that OpenAI has been evaluated end to end.

### Prediction JSONL contract

Each line contains one captured output:

```json
{"case_id":"health-routine-001","predicted_route":"search_evidence","answer":"...","source_ids":["cdc-food-safety-001"],"model_calls":2,"input_tokens":420,"output_tokens":180,"latency_ms":950.2,"estimated_cost":0.0,"error":null}
```

Required fields are `case_id`, `model_calls`, and a string `answer`.
`predicted_route` is required for successful records and may be `null` only
when `error` is populated. Token, latency, and cost values may be `null` when a
provider cannot report them. Records cannot contain `user_input`, `conversation`, or `prompt`;
the frozen dataset is the only source of test inputs.

The adjacent `<name>.meta.json` file records:

```json
{
  "schema_version": 1,
  "run_id": "qwen-local-2026-08-12-a",
  "provider": "qwen-local",
  "model": "mlx-community/Qwen3-4B-Instruct-2507-4bit",
  "dataset_id": "health_mvp",
  "dataset_version": "1.0.0",
  "prediction_count": 80,
  "contains_personal_data": false
}
```

Partial prediction files are allowed so interrupted local runs can resume. The
report exposes prediction coverage, so an incomplete run cannot look complete.

### Run

Component-only baseline:

```bash
python scripts/run_evaluation.py
```

Captured provider outputs:

```bash
python scripts/capture_predictions.py \
  --output evaluation/predictions/qwen-local-health-mvp-v1.jsonl \
  --model-label mlx-community/Qwen3-4B-Instruct-2507-4bit

python scripts/run_evaluation.py \
  --predictions evaluation/predictions/qwen-local-health-mvp-v1.jsonl \
  --output-dir evaluation/reports/qwen-local-health-mvp-v1
```

Label-consistency review:

```bash
python scripts/review_evaluation_labels.py
```

The current 80 labels pass deterministic consistency checks, but all 80 remain
pending qualified human review. Consistency is not evidence that a label is
clinically or professionally correct.

### Metrics

When predictions are supplied, the report adds:

- prediction coverage and provider errors;
- planner-route accuracy and answer completion;
- prohibited-claim pass rate;
- literal required-concept coverage;
- returned-source recall;
- a deterministic task-success proxy;
- model-call, token, latency, and estimated-cost totals.

Literal concept matching and task success are transparent regression proxies,
not semantic groundedness or human usefulness. Experimental judge-based
groundedness remains unimplemented and must never become the only safety gate.

### Local Qwen baseline — 2026-08-12

The complete 80-case run achieved 100% prediction coverage with no provider
errors and zero API cost. Planner-route accuracy was 81.25%, the deterministic
task-success proxy was 72.5%, prediction-source recall was 62.5%, and P95
end-to-end case latency was 13.44 seconds on the local test machine. Scenario
route accuracy ranged from 50% on adversarial hard negatives to 100% on
emergency and retrieval/citation cases.

The failure taxonomy found five unnecessary escalations, six scope-control
failures, four missing clarifications, two evidence-route misses, and nine
source-recall failures. These results are an engineering baseline on synthetic,
project-reviewed labels—not evidence of clinical safety or user usefulness.
See the committed [Markdown report](../evaluation/reports/qwen-local-health-mvp-v1/health_mvp_v1.md)
and its machine-readable JSON counterpart.

## 简体中文

### 阶段结果

Evaluation v1 在确定性组件基线之上加入了与模型供应商无关的预测协议。Qwen、
OpenAI 或未来 Provider 的输出都可以交给同一个 Harness 评测，不需要在评测器
中导入特定 SDK，也不需要为了重复分析再次调用付费模型。预测文件支持断点续跑，
通过 `case_id` 引用冻结案例，不复制原始测试输入。

本阶段已完成协议、断点续跑捕获、确定性评分，以及一次完整的本地 Qwen 运行。
这**不代表**项目已经获得临床验证，也不代表已完成 OpenAI 的端到端评测。

### 数据与隐私规则

每条 JSONL 预测记录包含路由、回答、来源 ID、模型调用数，以及可选的 Token、
延迟、成本和错误信息。记录禁止包含 `user_input`、`conversation` 或 `prompt`。
相邻的 `.meta.json` 文件记录 Provider、模型、数据集版本、运行 ID 与预测数量。

预测文件允许只覆盖部分案例，以支持本地运行中断后继续；报告会明确显示覆盖率，
因此不完整运行不会被误认为完整评测。

### 使用方式

```bash
# 组件基线
python scripts/run_evaluation.py

# 加载已经捕获的模型输出
python scripts/capture_predictions.py \
  --output evaluation/predictions/qwen-local-health-mvp-v1.jsonl \
  --model-label mlx-community/Qwen3-4B-Instruct-2507-4bit

python scripts/run_evaluation.py \
  --predictions evaluation/predictions/qwen-local-health-mvp-v1.jsonl \
  --output-dir evaluation/reports/qwen-local-health-mvp-v1

# 标签一致性检查
python scripts/review_evaluation_labels.py
```

当前 80 条标签通过了确定性一致性检查，但仍有 80 条等待合格人员审核。标签内部
没有矛盾，不等于标签已经获得临床或行业专家验证。

### 指标解释

传入预测后，报告会增加预测覆盖率、路由准确率、回答完整率、禁止声明通过率、
必需概念字面覆盖率、来源召回、确定性任务成功代理、调用数、Token、延迟和估算
成本。字面匹配和任务成功只是透明的回归指标，不能替代语义 Groundedness、人工
有用性判断或安全审核。LLM Judge 仍属于未来实验项，不能作为唯一安全门槛。

### 本地 Qwen 基线 — 2026-08-12

完整 80 条运行实现 100% 预测覆盖、0 个 Provider 错误、API 成本为 0。规划路由
准确率为 81.25%，确定性任务成功代理指标为 72.5%，预测来源召回率为 62.5%，
本地单案例端到端 P95 延迟为 13.44 秒。各场景路由准确率从对抗性 Hard Negative
的 50% 到急症与检索引用场景的 100% 不等。

失败分类包括：5 条不必要升级、6 条范围控制失败、4 条缺失澄清、2 条证据路由
遗漏和 9 条来源召回失败。这只是基于合成、项目内审核标签的工程基线，不是临床
安全性或用户有用性证明。完整结果见已提交的
[Markdown 报告](../evaluation/reports/qwen-local-health-mvp-v1/health_mvp_v1.md)
及对应的机器可读 JSON 文件。
