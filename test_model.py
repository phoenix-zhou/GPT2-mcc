# GPT2LMHeadModel, GPT2Config：从 Hugging Face 的 transformers 库导入 GPT-2 的语言建模头部模型和配置类
from transformers import GPT2LMHeadModel, GPT2Config


import os
import sys

# 获取当前文件的父目录（即项目根目录），并加入系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parameter_config import ParameterConfig

params = ParameterConfig()
# 创建模型
if params.pretrained_model: #  判断配置中是否指定了预训练模型路径
    # 加载预训练模型: 从本地路径或 Hugging Face Hub 加载预训练的权重（包括词嵌入、Transformer 各层参数等），通常用于微调（Fine-tuning）或继续预训练
	model = GPT2LMHeadModel.from_pretrained(params.pretrained_model)
else:
    # 从头初始化模型
    model_config = GPT2Config.from_json_file(params.config_json) # 从 JSON 配置文件加载模型结构超参数（如层数、隐藏层维度、注意力头数、词表大小等）
    # 调用 GPT2LMHeadModel(config=model_config) 使用这些配置初始化模型
    # 作用：创建一个具有指定结构但权重完全随机的模型，通常用于从零开始预训练（Pre-training from scratch
    model = GPT2LMHeadModel(config=model_config)

print(f'model-->{model}')
