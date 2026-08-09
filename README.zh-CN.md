# 🏥 本地优先的医疗健康信息聊天机器人

[English](README.md) | [简体中文](README.zh-CN.md)

这是一个基于 Flask 的医疗健康信息聊天机器人研究项目。当前版本默认在本地
运行 Qwen 指令模型，可由用户为单次请求显式启用 OpenAI 云端增强，并保留
原始 GPT‑2 实现作为教学与效果对照基线。

> [!WARNING]
> 本项目仅用于研究与教学，不提供医疗诊断、处方或治疗建议，不能替代有资质
> 的医疗专业人员。不要输入真实患者姓名、证件号码、联系方式或其他敏感信息。

## 主要能力

- 默认使用本地 Qwen，不产生按 Token 计费的 API 调用。
- OpenAI 云端增强默认关闭，必须由服务器允许，并由用户逐次明确选择。
- 保留原 GPT‑2 推理入口，作为兼容和对照基线。
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
      └─ 非急症：本地知识检索
          → 最近对话上下文（最多四轮）
          → 本地 Qwen（默认）
          → OpenAI GPT（服务器允许且用户单次选择）
  → 回答与参考资料
```

## 快速启动：本地 Qwen

需要 Python 3.10 或更新版本。首次运行会下载模型权重，并需要足够的内存或
显存。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[inference]'

export GPT2_MCC_MODEL_PROVIDER="qwen-local"
export GPT2_MCC_QWEN_MODEL="mlx-community/Qwen3-4B-Instruct-2507-4bit"

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
export GPT2_MCC_OPENAI_MODEL="gpt-5.6-luna"
export GPT2_MCC_CLOUD_ENHANCEMENT_ENABLED=true

flask --app app run
```

OpenAI 请求设置 `store=False`。这不等同于完整的零数据保留承诺；生产部署前
仍需审查账户数据控制、适用法规和医疗数据处理要求。

## 原始 GPT‑2 基线

```bash
export GPT2_MCC_MODEL_PROVIDER="legacy-gpt2"
export GPT2_MCC_INFERENCE_MODEL_PATH="/path/to/gpt2/checkpoint"
python -m pip install -e '.[legacy-inference]'
flask --app app run
```

上游仓库没有直接提交大型 `pytorch_model.bin` 文件。原作者发布的资源：

- [百度网盘模型权重](https://pan.baidu.com/s/1CBWmrspoGenggJ2-GyOirA?pwd=2mrv)，提取码 `2mrv`
- [原项目 CSDN 文章](https://blog.csdn.net/zhoupenghui168/article/details/162314485)

## 安全分流与本地检索

`safety.py` 对严重呼吸困难、卒中征象、无法控制的出血、意识丧失和立即自伤
风险等强信号进行保守分流。它不是诊断模型，可能漏报或误报，不能作为医疗
器械使用。

`knowledge/medical_guidance.json` 是一个小型、可审查的本地资料库。初始资料
引用 CDC、NHS 和 WHO 指南。`knowledge.py` 目前使用无外部依赖的关键词检索，
以后可以在不改变 Web 层接口的情况下替换为向量检索。

## 开发与测试

```bash
python -m pip install -e '.[dev]'
pytest
```

测试使用模拟 Provider，不会下载 Qwen，也不会调用付费 API。

## 主要文件

```text
app.py                          Flask 应用与请求编排
chat_models.py                  Qwen、OpenAI 和 GPT‑2 Provider
conversation.py                 有界的内存多轮上下文
safety.py                       急症风险分流
knowledge.py                    本地检索与上下文构造
knowledge/medical_guidance.json 版本化资料与来源
templates/index.html            Web 页面
data_preprocess/                原 GPT‑2 数据处理代码
train.py                        原 GPT‑2 训练入口
tests/                          自动化测试
```

## 后续路线

- 扩充医学资料库并进行专业内容审核。
- 使用中文向量嵌入和重排模型升级 RAG。
- 增加流式输出和结构化回答。
- 建立安全性、事实性、引用准确率、延迟和成本评测。
- 增加容器、生产 WSGI 服务、可观测性和部署文档。

## 许可证

上游项目目前没有声明开源许可证。在获得原作者明确许可前，请勿假设代码或
数据可以用于再分发或商业用途。
