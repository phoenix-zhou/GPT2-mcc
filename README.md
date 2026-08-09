# 🏥 Local-first Medical Chatbot

基于 Flask 的医疗健康信息聊天机器人研究项目。当前版本默认在本地运行
Qwen 指令模型，可由用户为单次请求显式启用 OpenAI 云端增强，并保留原始
GPT‑2 实现作为教学和效果对照基线。

> [!WARNING]
> 本项目仅用于研究与教学，不提供医疗诊断、处方或治疗建议，不能替代有资质
> 的医疗专业人员。不要输入真实患者姓名、证件号码、联系方式或其他敏感信息。

## 当前能力

- 本地 Qwen 为默认模型，不产生按 Token 计费的 API 调用。
- OpenAI 云端增强默认关闭，必须由服务器启用且由用户逐次勾选。
- 原 GPT‑2 推理入口继续保留，用作兼容与对照基线。
- 明显急症信号先经过确定性规则分流，不调用任何生成模型。
- 非急症问题可检索仓库内版本化的医学资料，并在页面单独展示来源。
- Flask 应用工厂、延迟模型加载、健康检查、输入校验和受控错误页面。
- Pytest 自动化测试与 GitHub Actions CI。

## 请求流程

```text
浏览器问题
  → 输入校验
  → 急症风险分流
      ├─ 高风险：固定急救提示，不调用模型
      └─ 非急症：本地知识检索
          → 本地 Qwen（默认）
          → OpenAI GPT（服务器允许且用户单次选择）
  → 回答与参考资料
```

## 快速启动：本地 Qwen

需要 Python 3.10 或更新版本。首次运行会从模型仓库下载权重，并需要足够的
内存或显存。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[inference]'

export GPT2_MCC_MODEL_PROVIDER="qwen-local"
export GPT2_MCC_QWEN_MODEL="Qwen/Qwen3-4B-Instruct-2507"

flask --app app run
```

启动后访问 <http://127.0.0.1:5000>。

## 可选：OpenAI 云端增强

OpenAI API 与 ChatGPT 订阅分开计费。密钥只通过环境变量读取，不应写入代码、
`.env` 或 Git 历史。

```bash
python -m pip install -e '.[openai]'

export OPENAI_API_KEY="your_api_key"
export GPT2_MCC_OPENAI_MODEL="gpt-5.6-luna"
export GPT2_MCC_CLOUD_ENHANCEMENT_ENABLED=true

flask --app app run
```

OpenAI 请求设置 `store=False`。这不等同于完整的零数据保留承诺；生产部署前
仍需审查账户数据控制、地区法规和医疗数据处理要求。

## 原始 GPT‑2 基线

```bash
export GPT2_MCC_MODEL_PROVIDER="legacy-gpt2"
export GPT2_MCC_INFERENCE_MODEL_PATH="/path/to/gpt2/checkpoint"
flask --app app run
```

原仓库没有直接提交大型 `pytorch_model.bin` 权重文件。原作者提供的下载链接：

- 模型权重：[百度网盘](https://pan.baidu.com/s/1CBWmrspoGenggJ2-GyOirA?pwd=2mrv)，提取码 `2mrv`
- 原项目博客：[CSDN](https://blog.csdn.net/zhoupenghui168/article/details/162314485)

## 安全分流与本地检索

`safety.py` 对严重呼吸困难、卒中征象、无法控制的出血、意识丧失和立即自伤
风险等强信号进行保守分流。这套规则不是诊断模型，可能漏报或误报，不能作为
医疗器械使用。

`knowledge/medical_guidance.json` 是一个小型、可审查的本地资料库。当前示例
资料来自 CDC、NHS 和 WHO。`knowledge.py` 使用无外部依赖的关键词检索，后续
可在保持接口不变的情况下升级为向量检索。

## 开发与测试

```bash
python -m pip install -e '.[dev]'
pytest
```

测试使用模拟 Provider，不会下载 Qwen，也不会调用付费 API。

## 主要文件

```text
app.py                         Flask Web 应用与请求编排
chat_models.py                 Qwen、OpenAI 和 GPT‑2 Provider
safety.py                      急症风险分流
knowledge.py                   本地资料检索与上下文构造
knowledge/medical_guidance.json 版本化资料与来源
templates/index.html           Web 页面
data_preprocess/               原 GPT‑2 数据处理代码
train.py                       原 GPT‑2 训练入口
tests/                         自动化测试
```

## 路线图

- 扩充并由专业人员审核医学资料库。
- 使用中文向量嵌入和重排模型升级 RAG。
- 增加多轮会话、流式输出和结构化回答。
- 建立安全性、事实性、引用准确率和模型成本评测。
- 增加容器化、生产 WSGI 服务、监控和部署文档。

## 许可证

上游项目当前没有声明开源许可证。在获得作者明确许可前，请勿假设代码或数据
可以用于再分发或商业用途。
