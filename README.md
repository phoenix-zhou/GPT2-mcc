
# 🏥 GPT-2 Medical Consultation Chatbot

> [!WARNING]
> This repository is a research and education demo. Its output is not medical
> advice and must not replace diagnosis or treatment by qualified clinicians.

## Quick start

Python 3.10 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[inference]'
flask --app app run
```

The original model weights are not included in this repository. Place a
Transformers-compatible checkpoint in `save_model/epoch97`, or set
`GPT2_MCC_INFERENCE_MODEL_PATH` to a checkpoint directory. Until a checkpoint
is configured, the web application will return a clear service-unavailable
message instead of failing during startup.

For development and tests:

```bash
python -m pip install -e '.[dev]'
pytest
```

## Model providers

The web application uses an interchangeable model provider. OpenAI is the
default and reads its API key from the environment:

```bash
python -m pip install -e '.[openai]'
export OPENAI_API_KEY="your_api_key"
export GPT2_MCC_MODEL_PROVIDER="openai"
export GPT2_MCC_OPENAI_MODEL="gpt-5.6-luna"
flask --app app run
```

API requests set `store=False`. Do not submit real patient identifiers or
other sensitive medical information to this research demo.

To run Qwen locally without per-token API charges:

```bash
python -m pip install -e '.[inference]'
export GPT2_MCC_MODEL_PROVIDER="qwen-local"
export GPT2_MCC_QWEN_MODEL="Qwen/Qwen3-4B-Instruct-2507"
flask --app app run
```

The first local run downloads the selected model and requires enough memory
for its weights. The original implementation remains available with
`GPT2_MCC_MODEL_PROVIDER=legacy-gpt2`.
This project aims to build an intelligent medical consultation chatbot using the GPT-2 pre-trained model. The system is designed to simulate a doctor's natural language communication style, understand users' descriptions of their conditions or medical inquiries, and provide accurate, efficient, and professional medical advice.
## ✨ Project Overview
As an intelligent dialogue system based on Natural Language Processing (NLP) technology, chatbots are playing a significant role in various fields. While they are commonly used for online customer service and personal assistants, their application in the medical field demands higher professionalism and rigor.
The core objectives of this project are:
- **Intelligent Interaction**: To provide a friendly and natural conversational experience, moving beyond mechanical keyword matching.
- **Professional Knowledge Base**: To be fine-tuned on real doctor-patient consultation corpora, ensuring the medical relevance of its responses.
- **End-to-End Implementation**: To cover the complete development lifecycle, from data crawling, preprocessing, and model training to evaluation and web deployment.
## 🛠️ Architecture
The technical implementation of this project follows the process outlined below (refer to the project architecture diagram):
1.  **Raw Data**: Doctor-patient consultation corpora are acquired via web crawlers.
2.**Data Processing**: The data undergoes format conversion and vectorization (Tokenization/Vectorization).
3. **Model Construction**: Based on the GPT-2 model architecture, hyperparameters are set, and Gradient Clipping is used to optimize training stability.
4. **Evaluation**: Evaluation metrics are established, and the model's performance is verified through a combination of automated metrics and human assessment.
5. **Interaction**: The model is deployed online with a user interface developed using web technologies.
## 📂 Project Structure
```
├── config/                 # Configuration directory
│   └── config.json         # Model and training configuration
├── data/                   # Dataset directory
│   ├── medical_train.pkl   # Training set (serialized object)
│   ├── medical_train.txt   # Training set (text)
│   ├── medical_valid.pkl   # Validation set (serialized object)
│   └── medical_valid.txt   # Validation set (text)
├── data_preprocess/        # Data preprocessing module
│   ├── dataloader.py       # Data loader
│   ├── dataset.py          # Dataset definition
│   └── preprocess.py       # Preprocessing logic
├── sample/                 # Sample examples
├── save_model/             # Model save directory
│   └── epoch97/            # Model weights saved at epoch 97
│       ├── config.json
│       └── pytorch_model.bin
├── templates/              # Web frontend templates (HTML, etc.)
├── vocab/                  # Vocabulary files
│   ├── vocab.txt
│   └── vocab2.txt
├── app.py                  # Web application entry point (Flask/Streamlit, etc.)
├── flask_predict.py        # Flask prediction interface logic
├── functions_tools.py      # General utility functions
├── interact.py             # Interactive dialogue script (for command-line testing)
├── parameter_config.py     # Parameter configuration script
├── pytorch_tools.py        # PyTorch-related utilities
├── train.py                # Main model training script
└── test_model.py           # Model testing script
```
## 🔗 Links
### Download Link for pytorch_model.bin in save_model/epoch97/:
```
https://pan.baidu.com/s/1CBWmrspoGenggJ2-GyOirA?pwd=2mrv (Extraction Code: 2mrv)
```
### Corresponding Project Blog Post:
```
https://blog.csdn.net/zhoupenghui168/article/details/162314485
```

---------------------------------------------------------------------

# 🏥 GPT-2 Medical Consultation Chatbot (基于GPT-2的智能医疗问答系统)

本项目旨在利用 **GPT-2** 预训练模型，构建一个智能医疗问诊聊天机器人。该系统能够模拟医生的自然语言交流方式，理解用户的病情描述或咨询问题，并给出准确、高效、专业的医疗建议。

## ✨ 项目简介 (Project Overview)

聊天机器人作为一种基于自然语言处理（NLP）技术的智能对话系统，正在多个领域发挥重要作用。虽然它们常用于在线客服和个人助手，但在医疗领域的应用具有更高的专业性和严谨性要求。

本项目的核心目标是：
- **智能化交互**：提供友好、自然的对话体验，而非机械的关键词匹配。
- **专业知识库**：基于真实的医患问诊语料进行微调，确保回答的医学相关性。
- **全流程实现**：涵盖了从数据爬取、预处理、模型训练、评估到 Web 部署的完整开发流程。

## 🛠️ 技术架构 (Architecture)

本项目的技术实现遵循以下流程（参考项目架构图）：

1.  **原始数据 (Raw Data)**: 通过网络爬虫获取医患问诊语料。
2.  **数据处理 (Data Processing)**: 进行格式转换与向量化表示 (Tokenization/Vectorization)。
3.  **模型构建 (Model Construction)**: 基于 GPT-2 模型架构，设置超参数，并使用梯度裁剪 (Gradient Clipping) 优化训练稳定性。
4.  **模型评估 (Evaluation)**: 制定评估指标，结合人工评估与自动指标验证模型效果。
5.  **人机交互 (Interaction)**: 通过 Web 开发技术将模型上线，提供用户界面。

## 📂 项目结构 (Project Structure)
```
├── config/                 # 配置文件目录
│   └── config.json         # 模型与训练配置
├── data/                   # 数据集目录
│   ├── medical_train.pkl   # 训练集 (序列化对象)
│   ├── medical_train.txt   # 训练集 (文本)
│   ├── medical_valid.pkl   # 验证集 (序列化对象)
│   └── medical_valid.txt   # 验证集 (文本)
├── data_preprocess/        # 数据预处理模块
│   ├── dataloader.py       # 数据加载器
│   ├── dataset.py          # 数据集定义
│   └── preprocess.py       # 预处理逻辑
├── sample/                 # 样本示例
├── save_model/             # 模型保存目录
│   └── epoch97/            # 第97轮保存的模型权重
│       ├── config.json
│       └── pytorch_model.bin
├── templates/              # Web前端模板 (HTML等)
├── vocab/                  # 词表文件
│   ├── vocab.txt
│   └── vocab2.txt
├── app.py                  # Web应用入口 (Flask/Streamlit等)
├── flask_predict.py        # Flask预测接口逻辑
├── functions_tools.py      # 通用工具函数
├── interact.py             # 交互式对话脚本 (命令行测试用)
├── parameter_config.py     # 参数配置脚本
├── pytorch_tools.py        # PyTorch相关工具
├── train.py                # 模型训练主脚本
└── test_model.py           # 模型测试脚本
```

#### save_model.epoch97下面的pytorch_model.bin下载链接: https://pan.baidu.com/s/1CBWmrspoGenggJ2-GyOirA?pwd=2mrv 提取码: 2mrv
#### 项目对应的博客: 
```
https://blog.csdn.net/zhoupenghui168/article/details/162314485
```
