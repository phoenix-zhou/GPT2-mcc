# ClearCare Health Brand and Ownership Architecture

[English](#english) | [简体中文](#简体中文)

## English

### Decision

The repository and product identity is **ClearCare Health**.

```text
ClearCare Health — Governed Healthcare Information AI Agent
Safety · Governed RAG · Agent Evaluation · Evidence Governance
```

The code keeps reusable governed-agent abstractions, but **Governed Agent Lab
is no longer the repository headline or a product-level platform claim**. One
implemented health vertical is not sufficient evidence for a horizontal
platform. This decision improves recruiter comprehension and preserves
portfolio separation from horizontal evaluation/infrastructure projects.

### Product and architecture boundary

```text
ClearCare Health
├── Health product identity and user journey
├── Domain policy
│   ├── non-diagnosis boundary
│   ├── emergency routing
│   └── clarification and refusal policy
├── Reusable governed-agent architecture
│   ├── bounded runtime
│   ├── provider adapters
│   ├── governed evidence validation and retrieval
│   └── provider-neutral evaluation contract
└── Health-specific evidence and evaluation
    ├── governed health corpus
    └── health_mvp_v1
```

Reusable components may be described as *domain-extensible abstractions*.
They must not be described as a validated general platform until another
product domain has its own user boundary, policy, governed corpus, frozen
evaluation, provider run, and appropriate human review.

### Naming policy

| Layer | Name | Scope |
|---|---|---|
| Repository and product | ClearCare Health | health-information experience, policy, corpus, and results |
| Product descriptor | Governed Healthcare Information AI Agent | concise recruiter-facing category |
| Internal runtime | `GovernedEvidenceAgent` | reusable bounded orchestration abstraction |
| Python distribution | `clearcare-health-agent` | repository package metadata |
| Configuration prefix | `GOVERNED_AGENT_*` | reusable technical configuration |
| Compatibility prefixes | `CLEARCARE_*`, `GPT2_MCC_*` | existing local setups only |
| Evaluation dataset | `health_mvp_v1` | health-specific development contract |

Keeping `GovernedEvidenceAgent` and `GOVERNED_AGENT_*` is intentional: internal
abstraction does not require turning the product into a platform brand.

### Ownership boundary

**Implemented in the modernization:** professional web experience,
multi-turn memory, Qwen/OpenAI providers, safety routing, bounded agent runtime,
governed evidence, retrieval experiments, evaluation harness/reports, evidence
Skill, product documentation, and security hardening.

**Inherited:** the repository starting point and remaining GPT-2
training/inference, vocabulary, and configuration material from
[`phoenix-zhou/GPT2-mcc`](https://github.com/phoenix-zhou/GPT2-mcc). The
upstream repository declares no open-source license; inherited work is not
presented as original.

**Removed or quarantined:** raw legacy medical datasets, Pickles, bytecode,
duplicate/scratch assets, unsafe deserialization, default raw-chat logging,
and the GPT-2 web provider.

### Repository strategy

The current GitHub repository name already reflects ClearCare, so no rename is
needed. If explicit permission for inherited code cannot be obtained, the
safest long-term portfolio path is a clean-room repository containing only
newly implemented ClearCare code, governed content with verified reuse rights,
and an attribution note that does not copy unlicensed source.

## 简体中文

### 决策

仓库与产品品牌恢复为 **ClearCare Health / 澄心循证健康智能体**：

```text
ClearCare Health — 受控循证健康信息 AI Agent
安全分流 · Governed RAG · Agent Evaluation · Evidence Governance
```

代码继续保留可复用的可治理 Agent 抽象，但 **Governed Agent Lab 不再作为仓库
Headline，也不再构成横向平台产品声明**。只有一个已实现健康场景，不足以证明
通用平台能力。这样能让招聘者更快理解产品，也能与横向评测/基础设施项目形成区分。

### 产品与架构边界

ClearCare 负责健康产品身份、用户旅程、非诊断边界、急症分流、澄清策略、健康
语料和 `health_mvp_v1` 结果。内部 Runtime、Provider Adapter、证据校验和评测
协议可以称为“可扩展抽象”；在第二个产品领域拥有独立用户边界、策略、语料、冻结
评测、Provider Run 和合适人工审核前，不能称为已经验证的通用平台。

### 命名规则

- 仓库和产品：ClearCare Health / 澄心循证健康智能体
- 产品描述：Governed Healthcare Information AI Agent
- 内部 Runtime：`GovernedEvidenceAgent`
- Python Distribution：`clearcare-health-agent`
- 技术配置：`GOVERNED_AGENT_*`
- 兼容配置：`CLEARCARE_*`、`GPT2_MCC_*`
- 健康评测集：`health_mvp_v1`

保留内部 `GovernedEvidenceAgent` 与 `GOVERNED_AGENT_*` 是有意的：技术抽象可复用，
并不要求把垂直产品包装成平台品牌。

### 所有权边界

现代化新增内容包括专业 Web 体验、多轮记忆、Qwen/OpenAI Provider、安全分流、
有界 Agent、受控证据、检索实验、Evaluation Harness/报告、证据 Skill、产品文档
和安全加固。

继承内容来自 [`phoenix-zhou/GPT2-mcc`](https://github.com/phoenix-zhou/GPT2-mcc)，
包括仓库起点与保留的 GPT-2 训练/推理、词表和配置。上游没有声明开源许可证，
这些内容不会作为我的原创成果宣传。

已移除或隔离历史原始医疗数据、Pickle、字节码、重复/草稿资源、不安全反序列化、
默认原始聊天日志和 GPT-2 Web Provider。

### 仓库策略

当前 GitHub 仓库名已经体现 ClearCare，无需重命名。如果无法取得继承代码的明确
许可，最稳妥的长期方案是建立 Clean-room 仓库：只包含全新实现的 ClearCare 代码、
具有明确复用权的受控资料，以及不复制无许可源码的来源说明。
