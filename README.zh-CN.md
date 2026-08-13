# Governed Agent Lab / 可控智能体实验平台

[English](README.md) | [简体中文](README.zh-CN.md)

这是一个面向作品集的可控 AI Agent 构建与评测平台，核心包括受控资料、明确的
工具边界、与 Provider 无关的评测、失败分层和可复用 Codex Skills。
**ClearCare Health / 澄心循证健康智能体**是第一个垂直案例，用来展示这些控制
如何应用在高风险健康信息场景。

平台架构允许扩展到其他领域；在新的垂直领域拥有独立受控语料、冻结案例和实测
报告之前，仓库中已经提交的产品与评测结论仍只适用于健康案例。

> [!WARNING]
> 本项目仅用于研究与教学，不提供医疗诊断、处方或治疗建议，不能替代有资质
> 的医疗专业人员。不要输入真实患者姓名、证件号码、联系方式或其他敏感信息。

## 平台主要能力

- 与 Provider 无关的评测产物、场景指标和失败分类。
- 单次有界“规划—工具—回答”循环、白名单动作和只读工具。
- 带来源、时效性、审核状态与哈希校验的受控证据记录。
- 可复用的资料治理 Skill，以及 Evaluation Skill 路线图。
- 本地优先推理与明确选择的云端模型对比。

## ClearCare Health 垂直案例

- 默认使用本地 Qwen，不产生按 Token 计费的 API 调用。
- OpenAI 云端增强默认关闭，必须由服务器允许，并由用户逐次明确选择。
- 模型规划器只能选择检索资料、请求补充或无需工具回答三种白名单动作。
- 智能体最多执行一次只读工具调用，并输出不含思维链的可检查执行记录。
- 明显急症信号在调用生成模型之前进行分流。
- 非急症问题可检索仓库内版本化的医学资料，并单独显示资料来源。
- 后续补充会自动携带最近四轮对话上下文，页面最多保留六轮咨询记录。
- 包含 Flask 应用工厂、模型延迟加载、健康检查、输入校验、受控错误处理、
  Pytest 测试和 GitHub Actions CI。

## 请求流程

```text
浏览器问题
  → 输入校验
  → 急症风险分流
      ├─ 高风险：固定急救提示，不调用模型
      └─ 非急症：有界智能体规划
          ├─ 请求必要补充
          ├─ 调用受控资料检索工具
          └─ 无需工具直接回答
              → 本地 Qwen（默认）
              → OpenAI GPT（服务器允许且用户单次选择）
  → 回答与参考资料
  → 可展开的动作与工具记录
```

## 快速启动：本地 Qwen

需要 Python 3.10 或更新版本。首次运行会下载模型权重，并需要足够的内存或
显存。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[inference]'

export GOVERNED_AGENT_MODEL_PROVIDER="qwen-local"
export GOVERNED_AGENT_QWEN_MODEL="mlx-community/Qwen3-4B-Instruct-2507-4bit"

flask --app app run
```

启动后访问 <http://127.0.0.1:5000>。

## 后续补充与会话记忆

首次回答后，只需要输入新的信息，例如“已经持续两天，每天大约五次，没有
发热”。不需要删除、复制或重复之前的问题。模型会收到最近四轮对话作为
上下文，页面最多显示六轮记录。

咨询内容只暂存在当前 Flask 进程的内存中，不会写入仓库或数据库。重启服务，
或点击“开始新咨询”后，记录就会清除。该设计适合本地演示；如果部署给外部
用户，应该改用加密、有访问控制且有明确保留期限的服务端会话存储。

## 可选：OpenAI 云端增强

OpenAI API 与 ChatGPT 订阅分开计费。密钥只通过环境变量读取，不应写入代码、
`.env` 文件或 Git 历史。

```bash
python -m pip install -e '.[openai]'

export OPENAI_API_KEY="your_api_key"
export GOVERNED_AGENT_OPENAI_MODEL="gpt-5.6-luna"
export GOVERNED_AGENT_CLOUD_ENHANCEMENT_ENABLED=true

flask --app app run
```

OpenAI 请求设置 `store=False`。这不等同于完整的零数据保留承诺；生产部署前
仍需审查账户数据控制、适用法规和医疗数据处理要求。一次智能体请求可能包含
一次规划调用和一次回答调用，因此云端模式可能产生两次模型调用费用。

## 原始 GPT‑2 基线

```bash
export GOVERNED_AGENT_MODEL_PROVIDER="legacy-gpt2"
export GOVERNED_AGENT_INFERENCE_MODEL_PATH="/path/to/gpt2/checkpoint"
python -m pip install -e '.[legacy-inference]'
flask --app app run
```

上游仓库没有直接提交大型 `pytorch_model.bin` 文件。原作者发布的资源：

- [百度网盘模型权重](https://pan.baidu.com/s/1CBWmrspoGenggJ2-GyOirA?pwd=2mrv)，提取码 `2mrv`
- [原项目 CSDN 文章](https://blog.csdn.net/zhoupenghui168/article/details/162314485)

迁移期间仍兼容健康案例的 `CLEARCARE_*` 和原始 `GPT2_MCC_*` 变量，但新增
平台配置应统一使用 `GOVERNED_AGENT_*`。

## 健康案例的安全与受控证据

`safety.py` 对严重呼吸困难、卒中征象、无法控制的出血、意识丧失和立即自伤
风险等强信号进行保守分流。它不是诊断模型，可能漏报或误报，不能作为医疗
器械使用。

`agent_runtime.py` 实现白名单内的规划、工具和回答循环。规划结果必须是 JSON；
无法解析或未注册的动作会回退为一次只读资料检索。执行记录只包含动作名称和
工具结果数量，不包含模型隐藏推理。

`knowledge/medical_guidance.json` 当前包含 3 条由项目编写的中文摘要，分别链接
CDC、NHS 和 WHO 页面。它们明确标记为“尚未经临床人员审核”，不能宣传为已经
验证的临床建议。每条记录包含来源、地区、审查日期、版本、适用人群、复用状态
及 SHA‑256 内容哈希。`knowledge/source_manifest.json` 定义获准来源与复核政策；
缺少元数据、未知来源、非 HTTPS 链接、错误日期、重复 ID 或哈希失配都会导致
加载失败。

## 可安装的 Codex Skill

仓库包含 `curate-health-evidence`，用于添加受控资料、审计来源与时效性并生成
知识库覆盖率报告。它是开发者维护工作流，不是面向患者的医疗建议 Skill。

可以让 Codex 安装：

```text
请从以下 GitHub 地址安装 Codex Skill：
https://github.com/yuanzou0/clearcare-health-agent/tree/main/skills/curate-health-evidence
```

安装后的下一轮可通过 `$curate-health-evidence` 调用。Skill 内只包含
`SKILL.md`、界面元数据、确定性脚本和参考规范，不重复打包 Flask 应用或模型
权重。

## 开发与测试

```bash
python -m pip install -e '.[dev]'
python scripts/validate_knowledge.py
pytest
```

测试使用模拟 Provider，不会下载 Qwen，也不会调用付费 API。

无需加载模型即可运行 80 条案例的确定性 Evaluation MVP：

```bash
python scripts/run_evaluation.py
python scripts/review_evaluation_labels.py
```

当前组件基线在合成、项目内审核的数据上得到：急症召回率 1.000、急症误报率
0.0909、Retrieval Recall@3 为 0.625。这些不是临床性能结论。方法、失败样例和
限制见 [Evaluation MVP 文档](docs/evaluation-mvp.md)。
Evaluation v1 进一步加入了与 Provider 无关、隐私安全的预测协议。已提交的完整
本地 Qwen 基线得到：规划路由准确率 81.25%、确定性任务成功代理指标 72.5%，
Provider 错误为 0，API 成本为 0。这些是工程回归指标，不是临床结论。详见双语
[Evaluation v1 报告与协议](docs/evaluation-v1.md)。

## 产品案例与升级计划

- [品牌架构（中英双语）](docs/brand-architecture.md)：平台与垂直案例边界、命名
  规则、兼容策略和仓库迁移顺序。
- [产品 Case Study（英文）](docs/product-case-study.md)：问题、用户、用户旅程、
  产品决策、权衡、指标、失败场景与非目标。
- [作品集升级路线图（英文）](docs/portfolio-upgrade-roadmap.md)：包含评测、RAG
  实验、数据分析、Skills 与部署的日期、勾选状态和验收标准。
- [Evaluation MVP（英文）](docs/evaluation-mvp.md)：数据集设计、基线结果、已发现
  的失败与尚未测量的指标。
- [Evaluation v1（中英双语）](docs/evaluation-v1.md)：模型预测协议、端到端代理
  指标、标签审核门槛与隐私规则。
- [RAG V2 实验（中英双语）](docs/rag-v2-experiment.md)：Keyword/BM25 对照、
  本地 Qwen 端到端结果、失败分析和晋级决策。

## 主要文件

```text
app.py                          Flask 应用与请求编排
agent_runtime.py                有界规划器、工具与回答运行时
chat_models.py                  Qwen、OpenAI 和 GPT‑2 Provider
conversation.py                 有界的内存多轮上下文
safety.py                       急症风险分流
knowledge.py                    本地检索与上下文构造
knowledge/medical_guidance.json 版本化资料与来源
knowledge/source_manifest.json  获准来源与复核政策
scripts/validate_knowledge.py    独立的来源与完整性检查
scripts/capture_predictions.py  支持断点续跑的模型评测捕获
skills/curate-health-evidence/   可安装的证据治理 Codex Skill
evaluation/                     冻结案例、模型预测与评测报告
templates/index.html            Web 页面
data_preprocess/                原 GPT‑2 数据处理代码
train.py                        原 GPT‑2 训练入口
tests/                          自动化测试
```

## 后续路线

本地 Qwen Evaluation v1 基线、第一阶段品牌迁移，以及 Keyword/BM25 RAG V2
实验已经完成。BM25 将任务成功代理指标从 72.5% 提升到 78.75%，但由于阈值和
评估使用同一开发集，目前只晋级为候选方案，生产默认仍为 Keyword。Embedding 和
Hybrid Retrieval 将继续作为需要实验证明的方案，而不是默认升级。优先级、验收标准
和时间线见
[可勾选作品集路线图](docs/portfolio-upgrade-roadmap.md)。

## 许可证

上游项目目前没有声明开源许可证。在获得原作者明确许可前，请勿假设代码或
数据可以用于再分发或商业用途。
