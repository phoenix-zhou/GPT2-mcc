
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
#### save_model.epoch97下面的pytorch_model.bin下载链接: https://pan.baidu.com/s/1CBWmrspoGenggJ2-GyOirA?pwd=2mrv 提取码: 2mrv
#### 项目对应的博客: https://blog.csdn.net/zhoupenghui168/article/details/162314485
```