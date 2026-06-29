# -*- coding: utf-8 -*-
import os
# import sys
import torch.nn.utils.rnn as rnn_utils  # 导入rnn_utils模块，用于处理可变长度序列的填充和排序
from torch.utils.data import Dataset, DataLoader  # 导入Dataset和DataLoader模块，用于加载和处理数据集
import torch  # 导入torch模块，用于处理张量和构建神经网络
import pickle  # 导入pickle模块，用于序列化和反序列化Python对象
from dataset import *  # 导入自定义的数据集类

# 获取当前文件的父目录（即项目根目录），并加入系统路径
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parameter_config import ParameterConfig

# 超参数配置类
params = ParameterConfig()


def load_dataset(train_path, valid_path):
    """
    数据集加载函数: 加载训练集和验证集
    :return:
    :param train_path: 训练数据集路径
    :param valid_path: 验证数据集路径
    :return: 训练数据集和验证数据集
    """
    with open(train_path, "rb") as f:
        train_input_list = pickle.load(f)  # 使用 pickle.load 将训练集和验证集的 Token ID 列表加载到内存: 从文件中加载输入列表

    with open(valid_path, "rb") as f:
        valid_input_list = pickle.load(f)  # 从文件中加载输入列表
    # 划分训练集与验证集
    # print(len(train_input_list))  # 打印输入列表的长度
    # print(train_input_list[0])
    # 实例化自定义的 MyDataset，传入数据列表和最大长度参数 params.max_len，分别构建训练集和验证集对象并返回
    train_dataset = MyDataset(train_input_list, params.max_len)  # 创建训练数据集对象
    val_dataset = MyDataset(valid_input_list, params.max_len)  # 创建验证数据集对象
    return train_dataset, val_dataset  # 返回训练数据集和验证数据集


def collate_fn(batch):
    """
    自定义的collate_fn函数，用于将数据集中的样本进行批处理
    这是解决变长序列问题的关键函数。当 DataLoader 提取出一个 Batch 的样本时，会自动将这个 Batch 传入此函数
    :param batch: 样本列表
    :return: 经过填充的输入序列张量和标签序列张量
    """
    # print(f'batch-->{batch}') # batch的长度-->4
    # print(f'batch的长度-->{len(batch)}')
    # print(f'batch的第一个样本的长度--》{batch[0].shape}') # batch的第一个样本的长度--》torch.Size([202])
    # print(f'batch的第二个样本的长度--》{batch[1].shape}') # batch的第二个样本的长度--》torch.Size([17])
    # print(f'batch的第三个样本的长度--》{batch[2].shape}') # batch的第三个样本的长度--》torch.Size([234])
    # print(f'batch的第四个样本的长度--》{batch[3].shape}') # batch的第四个样本的长度--》torch.Size([25])
    # print(f'*'*80)
    # rnn_utils.pad_sequence：将根据一个batch中，最大句子长度，进行补齐
    """
    处理输入序列 (input_ids)：调用 rnn_utils.pad_sequence(batch, batch_first=True, padding_value=0)。
    它会自动寻找当前 Batch 中最长的序列长度，并将其他较短的序列在末尾填充 0（即 [PAD] 的 ID），使它们对齐。
    batch_first=True 表示输出的张量形状为 [Batch_Size, Seq_Len]
    """
    input_ids = rnn_utils.pad_sequence(batch, batch_first=True, padding_value=0)  # 对输入序列进行填充，使其长度一致
    # print(f'batch的第一个样本的长度--》{input_ids[0].shape}') # batch的第一个样本的长度--》torch.Size([222])
    # print(f'batch的第二个样本的长度--》{input_ids[1].shape}') # batch的第二个样本的长度--》torch.Size([222])
    # print(f'batch的第三个样本的长度--》{input_ids[2].shape}') # batch的第三个样本的长度--》torch.Size([222])
    # print(f'batch的第四个样本的长度--》{input_ids[3].shape}') # batch的第四个样本的长度--》torch.Size([222])
    """
    处理标签序列 (labels)：同样调用 pad_sequence，但填充值设置为 -100。
    关键点：在 PyTorch 的 CrossEntropyLoss 中，标签为 -100 的位置会被自动忽略，不参与损失（Loss）的计算和梯度更新。
    这完美防止了模型去学习预测无意义的填充符
    """
    labels = rnn_utils.pad_sequence(batch, batch_first=True, padding_value=-100)  # 对标签序列进行填充，使其长度一致
    """
    labels-->tensor([[ 101, 3791, 2225,  ..., -100, -100, -100],
        [ 101,  704, 7599,  ..., -100, -100, -100],
        [ 101, 5519, 5310,  ..., 1317,  511,  102],
        [ 101, 5513,  677,  ..., -100, -100, -100]])
    """
    # print(f'labels-->{labels}'
    return input_ids, labels  # 返回经过填充的输入序列张量和标签序列张量


def get_dataloader(train_path, valid_path):
    """
    数据加载器构建: 获取训练数据集和验证数据集的DataLoader对象
    :param train_path: 训练数据集路径
    :return: 训练数据集的DataLoader对象和验证数据集的DataLoader对象
    """

    train_dataset, val_dataset = load_dataset(train_path, valid_path)  # 加载训练数据集和验证数据集
    # print(f'train_dataset-->{len(train_dataset)}')
    # print(f'val_dataset-->{len(val_dataset)}')
    train_dataloader = DataLoader(train_dataset,
                                  batch_size=params.batch_size,
                                  shuffle=True, # shuffle=True：每个 Epoch 打乱数据顺序，防止模型记住数据顺序，提升泛化能
                                  collate_fn=collate_fn, # 指定自定义的批处理函数，替代默认的堆叠（stack）操作
                                  drop_last=True)  # 创建训练数据集的DataLoader对象: 丢弃最后一个不完整的 Batch。这在分布式训练或使用 Batch Normalization 时非常有用，可防止因 Batch 大小不一致导致的报错或统计偏差
    validate_dataloader = DataLoader(val_dataset,
                                     batch_size=params.batch_size,
                                     shuffle=True,
                                     collate_fn=collate_fn,
                                     drop_last=True)  # 创建验证数据集的DataLoader对象
    return train_dataloader, validate_dataloader  # 返回训练数据集的DataLoader对象和验证数据集的DataLoader对象


if __name__ == '__main__':
    train_dataloader, validate_dataloader = get_dataloader(params.train_path, params.valid_path)
    for input_ids, labels in train_dataloader:
        print(f'input_ids--》{input_ids.shape}')
        print(f'labels--》{labels.shape}')
        break
