# ClearCare Health / 澄心循证健康智能体

**一个具有安全边界和证据约束的健康信息 AI Agent**

安全分流 · Governed RAG · Agent Evaluation · Evidence Governance

[English](README.md) | [简体中文](README.zh-CN.md)

ClearCare Health 是一个垂直 Applied AI 产品案例，研究的问题是：LLM 如何帮助
用户整理健康问题、识别重要危险信号并查看一般健康资料，同时不把自己包装成医生？

代码中包含可复用的可治理 Agent 组件，但本仓库**不声称已经成为经过验证的通用
Agent 平台**。当前产品行为、资料库、安全策略和实测结论都只属于 ClearCare
健康信息场景。

> [!WARNING]
> 本项目仅用于研究和教学，不提供诊断、处方或治疗选择，也不能替代医生。
> 不要输入真实姓名、证件、联系方式或其他敏感信息。

## 产品命题

通用 LLM 的健康回答可能比证据表现得更确定、漏掉紧急信号、编造或误用引用，
也可能在信息不足时直接猜测。ClearCare 把这些风险转化为明确的产品约束：

- 强急症信号在模型生成前进入确定性分流；
- 单次白名单规划—工具—回答循环，最多一次只读工具调用；
- 资料具备出处、时效、域名、复核状态和哈希校验；
- 引用链接与生成文本分开呈现；
- 默认使用本地 Qwen，OpenAI 必须由服务器开启并由用户当次明确选择；
- 使用 Provider 无关评测，并公开限制和失败分层。

## 当前实现

| 能力 | 当前状态 |
|---|---|
| 安全分流 | 确定性强信号路由；可测量，但不是诊断分类器 |
| 有界 Agent | 单次规划—工具—回答；校验动作/原因组合；最多一次只读证据工具 |
| 多轮会话 | 有界内存上下文和明确的重置动作 |
| Governed RAG | 版本化覆盖合同、受控主题群、获准来源注册、URL 域名绑定、复核日期、语料上限和 SHA-256 完整性 |
| Evaluation | 83 条开发集案例、Provider 无关预测捕获、失败分类和 Keyword/BM25 对照 |
| 模型 | 固定 Revision 的本地 Qwen 默认、OpenAI 可选；GPT-2 不进入 Web Runtime |
| Web Demo | 本地单进程 Flask 页面，包含 Trace、引用、CSRF、请求限制和安全响应头 |
| 临床验证 | 未完成；当前 12 条项目摘要均未经临床人员审核 |
| 生产部署 | 不支持；尚无认证授权、分布式控制、加密持久化和合规体系 |

## 用户与 Agent 流程

```text
用户健康信息问题
  → 输入与同意边界校验
  → 确定性急症分流
      ├─ 强信号：固定急救提示，不调用模型
      └─ 非急症：有界 Planner
          ├─ 请求必要补充
          ├─ 检索受控证据
          └─ 不使用工具直接回答
              → 默认本地 Qwen
              → 开启且当次选择时使用 OpenAI
  → 回答 + 独立来源链接 + 可检查动作记录
  → 有界追问上下文或明确重置
```

Trace 只展示动作和结果数量，不包含隐藏思维链。

## 架构：可以复用，但不夸大

```text
ClearCare Health
├── 产品策略
│   ├── 非诊断边界
│   ├── 急症分流
│   └── 澄清与领域外策略
├── 可治理 Agent 架构
│   ├── 有界 Planner / Tool / Responder Runtime
│   ├── 模型 Provider Adapter
│   ├── 证据校验与检索
│   └── 隐私与 Web 护栏
├── Evaluation
│   ├── 冻结健康案例与预测协议
│   ├── 安全、检索、引用、延迟和成本指标
│   └── 分层失败报告
└── 开发者工作流
    └── curate-health-evidence Codex Skill
```

Runtime 和 Evaluation 协议按照可复用方向设计，但在第二个产品领域拥有独立策略、
语料、冻结评测和人工审核前，只能称为“可扩展抽象”，不能称为已经验证的横向平台。

## 实测结果与限制

下表是最后一次完整的 Qwen 端到端结果，使用数据集 v1.0.0 和此前的三文档语料。
它是历史工程回归结果，不代表当前十二文档语料的性能，也不是独立 Benchmark 或
临床性能结论。

| 指标 | Keyword 基线 | BM25 候选 |
|---|---:|---:|
| 本地 Qwen 任务成功代理指标 | 72.5% | 78.75% |
| Retrieval Recall@3 | 62.5% | 75.0% |
| 急症召回率 | 100% | 100% |
| Citation ID 有效率 | 100% | 100% |

由于方案选择和测量使用同一个开发集，BM25 仍只是候选。Citation ID 有效只说明
ID 存在，不能证明 Claim-level Entailment 或回答 Groundedness。晋级需要更完整的
受控语料、作者隔离的盲测 Holdout，以及人工审核的 Groundedness 结果。

详见 [Evaluation v1](docs/evaluation-v1.md)、
[RAG V2](docs/rag-v2-experiment.md) 与
[Evaluation MVP](docs/evaluation-mvp.md)。第一批六文档、无模型调用的组件回放作为
历史里程碑保存在 [Corpus v1 第一批审计](docs/corpus-v1-batch-1.md)：Keyword 与
BM25 的 Recall@3 分别为 64% 和 72%，No-hit Accuracy 均为 90%。当前十二文档的
组件回放记录在 [Corpus v1 第三批审计](docs/corpus-v1-batch-3.md)：Keyword 与
BM25 的 Recall@3 分别为 65.5% 和 69.0%，No-hit Accuracy 均为 89.7%。

## 我的工作、继承内容与已移除内容

### 本次现代化实现

- 专业 Flask 体验、有界多轮记忆和明确的云端同意流程；
- 本地 Qwen 与可选 OpenAI Provider 抽象；
- 确定性急症分流和有界 Agent 编排；
- 受控证据 Schema、来源 Manifest、校验和检索实验；
- Provider 无关评测捕获、指标、失败分析和报告；
- 证据治理 Codex Skill、Product Case Study、路线图和安全加固。

### 继承的起点

项目起源于
[`phoenix-zhou/GPT2-mcc`](https://github.com/phoenix-zhou/GPT2-mcc)。历史 GPT-2
训练/推理脚本、词表和模型配置属于继承内容，不作为我的原创成果宣传。上游仓库
没有声明开源许可证。

### 已移除或隔离

- 来源和去标识质量不明的历史医疗 TXT/Pickle 数据；
- 被跟踪的 Python 字节码、重复模板/词表和实验草稿；
- 不受限 Pickle 加载、默认原始会话日志和 GPT-2 Web Provider；
- 可变的默认模型与 CI 引用。

完整记录见[安全与风险审计](docs/security-and-risk-review.md)。

## 快速开始

需要 Python 3.10+。确定性测试与评测不会下载模型，也不会产生 API 费用。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'

python scripts/validate_knowledge.py
pytest
python scripts/run_evaluation.py
```

### 启动本地 Qwen 网页

MLX 配置面向 Apple Silicon。首次运行会下载固定 Revision 的量化模型，需要足够
内存。

```bash
python -m pip install -e '.[inference]'
export GOVERNED_AGENT_MODEL_PROVIDER="qwen-local"
export GOVERNED_AGENT_QWEN_MODEL="mlx-community/Qwen3-4B-Instruct-2507-4bit"
export GOVERNED_AGENT_QWEN_REVISION="50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b"
flask --app app run
```

访问 <http://127.0.0.1:5000>。追问时只输入新增信息，应用会自动提供有界的近期
上下文；点击“开始新咨询”即可清除。

### 可选 OpenAI 对照

OpenAI API 与 ChatGPT 订阅分开计费。只有服务器开启且用户在当次请求明确选择时，
才会使用云端。

```bash
python -m pip install -e '.[openai]'
export OPENAI_API_KEY="your_api_key"
export GOVERNED_AGENT_OPENAI_MODEL="gpt-5.6-terra"
export GOVERNED_AGENT_CLOUD_ENHANCEMENT_ENABLED=true
flask --app app run
```

请求设置了 `store=False`，但这不等于零数据保留或合规保证。不要提交密钥，也不要
发送敏感健康信息。

## 安全与部署边界

本地 Demo 已包含 CSRF、16 KiB 请求上限、单进程限流、安全 Cookie 默认值、严格
响应头、非持久会话、来源绑定、输入/语料上限、固定模型来源和异常脱敏。生产模式
在缺少 32 位以上稳定密钥或安全 Cookie 时会拒绝启动。

这些控制**不会**让 Flask 开发服务器具备公网生产能力。系统没有认证授权、分布式
限流、加密持久会话、WAF、独立审计服务或医疗合规认证。详见
[SECURITY.md](SECURITY.md)。

## 受控证据与数据策略

当前语料包含 12 条项目自行编写的中文摘要，链接 CDC、NHS、WHO 和国家卫生健康委，
并明确标记为
**未经临床人员审核**。运行时会拒绝未知或冒充来源、过期复核、未来日期、不安全
URL、重复 ID、超长内容和哈希不一致记录。

版本化的 [Corpus v1 覆盖规范](docs/corpus-v1-coverage-spec.md)已经定义 8 个主题群和
24 条记录目标；自动报告会显示当前 12/24 条记录以及每个剩余缺口。胃肠道症状、
呼吸系统症状和发热与感染均已达到文档数与多来源门槛。[第二批审计记录](docs/corpus-v1-batch-2.md)
说明了呼吸资料的筛选、标签变化和检索回归结果。Paraphrase、Hard Negative、No-hit 和
地区差异属于评测现象，不是证据文档类型。增加文档本身
不构成可靠性结论。
[`curate-health-evidence`](skills/curate-health-evidence/) Skill 可以自动执行确定性
治理校验，但不能替代临床审核。
[中国官方来源发现指南](docs/china-official-source-discovery.md)说明了如何使用卫健委
和药监局门户，同时避免把栏目首页或药品获批状态误当作患者指导。

## GPT-2 历史边界

原始 GPT-2 代码只保留为有出处说明的历史 CLI/训练基线，不作为 Web Provider，
也不进入当前 Evaluation。数据加载器拒绝 Pickle 全局对象、类和超大结构；模型
只允许加载本地 Safetensors。当前工作树不再包含历史原始数据，但 Git 历史与上游
快照仍可能保留它们。

## 仓库结构

```text
app.py, web_security.py          Web 编排与请求安全控制
agent_runtime.py                 有界规划、工具、回答 Runtime
chat_models.py                   Qwen 与 OpenAI Web Provider
conversation.py                 有界内存上下文
safety.py                        ClearCare 急症分流
knowledge.py, retrieval.py       受控语料校验与检索
evaluation/, scripts/            案例、捕获、报告与发布检查
skills/curate-health-evidence/   开发者证据治理 Skill
docs/                            产品、评测、RAG、品牌与风险文档
data_preprocess/, train.py       有出处说明且隔离的 GPT-2 历史流程
tests/                           自动化回归与安全测试
```

## 产品文档

- [Product Case Study](docs/product-case-study.md)
- [作品集升级路线图](docs/portfolio-upgrade-roadmap.md)
- [品牌与所有权架构](docs/brand-architecture.md)
- [Evaluation MVP](docs/evaluation-mvp.md) 与 [Evaluation v1](docs/evaluation-v1.md)
- [RAG V2 实验](docs/rag-v2-experiment.md)
- [安全与风险审计](docs/security-and-risk-review.md)
- [Health Corpus v1 中英双语覆盖规范](docs/corpus-v1-coverage-spec.md)
- [Corpus v1 第一批中英双语审计](docs/corpus-v1-batch-1.md)

## 下一阶段

1. 按照已完成的 Coverage Contract 扩充受控语料，只有全部 24 条记录通过准入门槛
   后才冻结 `health_corpus_v1`。
2. 创建作者隔离的盲测 Holdout，使用相同 Planner Decision 做 Keyword/BM25 配对回放。
3. 人工审核 20–30 个代表回答，标注 Citation Entailment、Claim Groundedness、
   Unsupported Claim Rate 和 Usefulness。
4. LLM Judge 只作为校准后的辅助指标，不作为唯一安全门槛。
5. 建立招聘者可快速阅读的 Evaluation Dashboard 和演示视频。

在这些证据缺口关闭之前，Embedding、Hybrid Retrieval、更多工具和更高自主性继续
延后。

## 许可证与复用警告

上游项目没有声明开源许可证，被移除的历史训练数据来源和复用权也未解决。未经
明确许可，不应假设继承代码或数据可以再分发或商用。本次现代化不能消除该法律
风险；如果无法取得授权，Clean-room 独立仓库是最稳妥的长期作品集方案。
