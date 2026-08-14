# -*- coding: utf-8 -*-
# orch.utils.data.Dataset：PyTorch 官方提供的数据集抽象基类。所有自定义数据集都必须继承它，
# 以便后续能无缝接入 DataLoader 进行批量加载
from torch.utils.data import Dataset  # 导入Dataset模块，用于定义自定义数据集
import torch  # 导入torch模块，用于处理张量和构建神经网络
from data_preprocess.safe_pickle import load_token_id_sequences


class MyDataset(Dataset):
    """
    自定义数据集类，继承自Dataset类
    接收两个参数：input_list（包含所有对话 Token ID 的二维列表）和 max_len（模型允许的最大序列长度）
    """

    def __init__(self, input_list, max_len):
        super().__init__()
        """
        初始化函数，用于设置数据集的属性
        :param input_list: 输入列表，包含所有对话的tokenize后的输入序列
        :param max_len: 最大序列长度，用于对输入进行截断或填充
        """
        # print(f'input_list--->{len(input_list)}')
        self.input_list = input_list  # 将输入列表赋值给数据集的input_list属性
        self.max_len = max_len  # 将最大序列长度赋值给数据集的max_len属性

    def __len__(self):
        """
        获取数据集的长度
        :return: 数据集的长度
        """
        return len(self.input_list)  # 返回数据集的长度

    def __getitem__(self, index):
        """
        根据给定索引获取数据集中的一个样本
        :param index: 样本的索引
        :return: 样本的输入序列张量
        """
        # print(f'当前取出的索引是--》{index}')
        input_ids = self.input_list[index]  # 获取给定索引处的输入序列
        # print(f'input_ids--》{input_ids}')
        input_ids = input_ids[:self.max_len]  # 根据最大序列长度对输入进行截断或填充
        input_ids = torch.tensor(input_ids, dtype=torch.long)  # 将输入序列转换为张量long类型, NLP 模型在处理 Token ID 时通常要求输入必须是 long 类型
        return input_ids  # 返回样本的输入序列张量


if __name__ == '__main__':
    train_input_list = load_token_id_sequences('../data/medical_train.pkl')

    # print(f'train_input_list-->{len(train_input_list)}')
    # print(f'train_input_list-->{type(train_input_list)}')
    # print(f'train_input_list-->{train_input_list[0]}')
    mydataset = MyDataset(input_list=train_input_list, max_len=300)
    print(f'mydataset-->{len(mydataset)}')
    result = mydataset[0]
    print(result)
