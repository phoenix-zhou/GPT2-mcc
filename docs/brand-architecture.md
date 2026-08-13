# Governed Agent Lab Brand Architecture

[English](#english) | [简体中文](#简体中文)

## English

### Decision

The repository-level identity is **Governed Agent Lab**. It describes the
reusable system being built: bounded agent execution, governed evidence,
provider-neutral evaluation, failure analysis, and developer Skills.

**ClearCare Health / 澄心循证健康智能体** remains the first reference vertical.
It owns the current web experience, emergency policy, health corpus, medical
disclosures, and `health_mvp_v1` evaluation dataset.

```text
Governed Agent Lab
├── Agent runtime: bounded actions and read-only tools
├── Evaluation: frozen cases, provider captures, metrics, failure taxonomy
├── Evidence governance: provenance, freshness, review status, hashes
├── Developer workflows: curation and evaluation Skills
└── Reference verticals
    └── ClearCare Health
        ├── health-information web demo
        ├── deterministic emergency router
        ├── governed health corpus
        └── health_mvp_v1 evaluation
```

### Why a two-level brand

A full replacement of ClearCare would discard a coherent high-stakes product
case. Keeping ClearCare as the repository identity, however, would make the
evaluation harness and Skills appear less transferable than they are. The
two-level structure preserves measured health-domain work while making the
platform capabilities legible for AI Product, Data Analytics, and Applied AI
roles.

### Claim boundary

Platform components may be described as domain-extensible. They must not be
described as proven across domains until another vertical has:

1. an explicit user and product boundary;
2. a governed, versioned evidence source;
3. a frozen domain evaluation set;
4. a captured provider run and segmented report; and
5. domain-appropriate human review status.

The current 72.5% task-success proxy and all safety/retrieval metrics apply only
to `health_mvp_v1`. They are not platform-wide quality claims.

### Naming policy

| Layer | Current name | Scope |
|---|---|---|
| Portfolio platform | Governed Agent Lab | runtime, evaluation, governance, Skills |
| Reference product | ClearCare Health | health-information experience and policy |
| Python distribution | `governed-agent-lab` | repository package metadata |
| New environment prefix | `GOVERNED_AGENT_*` | platform configuration |
| Compatibility prefixes | `CLEARCARE_*`, `GPT2_MCC_*` | existing local setups only |
| Health dataset | `health_mvp_v1` | frozen health evaluation contract |

`GovernedEvidenceAgent` is the preferred runtime class.
`ClearCareEvidenceAgent` remains an import alias during migration so existing
integrations do not break silently.

### Repository migration sequence

1. **Completed in this stage:** display identity, package metadata, preferred
   class name, configuration prefix, documentation, and compatibility tests.
2. Merge the stacked roadmap, evaluation, and brand PRs in order.
3. Rename the GitHub repository only after those PRs merge; GitHub redirects
   should not substitute for updating README and Skill installation URLs.
4. Update the installed Skill source URL and run a clean-install smoke test.
5. Retire compatibility names only in a documented major version, after a
   deprecation window.

The GitHub repository is deliberately not renamed inside this code PR because
doing so while stacked PRs are open would add review and URL risk without
improving the product behavior.

## 简体中文

### 决策

仓库级品牌统一为 **Governed Agent Lab / 可控智能体实验平台**。它描述的是可复用
系统：有界 Agent 执行、受控证据、与 Provider 无关的评测、失败分析和开发者
Skills。

**ClearCare Health / 澄心循证健康智能体**继续作为第一个参考垂直案例，负责当前
网页体验、急症策略、健康资料库、医疗免责声明和 `health_mvp_v1` 评测集。

### 为什么使用双层品牌

彻底删除 ClearCare 会损失一个已经形成闭环的高风险产品案例；继续让 ClearCare
代表整个仓库，又会让评测 Harness 与 Skills 看起来只能用于医疗。双层结构既保留
实测的健康领域成果，也能清楚展示对 AI 产品、数据分析和 Applied AI 岗位有价值
的可迁移能力。

### 声明边界

平台组件可以称为“可扩展到其他领域”，但在新垂直领域具备明确用户与边界、受控
版本化证据、冻结评测集、模型预测报告和合适的人工审核状态之前，不能声称已经在
多个领域得到验证。当前 72.5% 的任务成功代理指标和其他安全/检索指标只适用于
`health_mvp_v1`，不是平台整体质量结论。

### 命名与兼容

- 平台品牌：Governed Agent Lab / 可控智能体实验平台
- 健康产品：ClearCare Health / 澄心循证健康智能体
- Python Distribution：`governed-agent-lab`
- 新环境变量：`GOVERNED_AGENT_*`
- 兼容环境变量：`CLEARCARE_*`、`GPT2_MCC_*`
- 首选运行时类：`GovernedEvidenceAgent`
- 兼容类名：`ClearCareEvidenceAgent`

### 仓库迁移顺序

本阶段只迁移代码和文档中的品牌、包元数据、首选类名与环境变量，并用测试保证
兼容。应先按顺序合并 Roadmap、Evaluation 和 Brand PR，再重命名 GitHub 仓库、
更新 README 与 Skill 安装链接并完成干净安装测试。兼容命名只能在有明确弃用周期
的主版本升级中移除。

在堆叠 PR 仍打开时不直接重命名 GitHub 仓库，是为了避免额外的评审与 URL 风险；
这不是品牌迁移遗漏，而是有意安排的发布顺序。
