# -*- coding: utf-8 -*-

import torch
import torch.nn.functional as F


def caculate_loss(logit, target, pad_idx):
    '''
    计算模型的损失：通过函数解析下，GPT2内部如何计算损失的, 核心逻辑：错位对齐
    GPT-2 的训练目标是“根据前面的词预测下一个词”
    :param logit: 模型预测结果
    :param target: 真实标签
    :param pad_idx:特殊-100忽略计算损失的值
    :return:
    '''
    '''
    核心逻辑：错位对齐
    GPT-2 的训练目标是“根据前面的词预测下一个词”。
    输入 (logit)：模型接收了 [词1, 词2, 词3]，并输出了对 [词1, 词2, 词3, 词4] 的预测概率。
    目标 (target)：我们希望模型预测的是 [词2, 词3, 词4]。
    操作：
        logit = logit[..., :-1, :]：去掉模型预测序列的最后一个（因为它没有对应的真实标签）。
        labels = target[..., 1:]：去掉真实标签序列的第一个（因为它是输入的起始，不需要被预测）。
        这样，预测结果和真实标签就完美对齐了。
    展平操作:
        contiguous().view(-1, ...)：将三维张量 [批次大小, 序列长度, 词表大小] 展平成二维 [批次大小 × 序列长度, 词表大小]。
        这是为了适应 F.cross_entropy 函数的输入要求。
    计算交叉熵:
        F.cross_entropy(..., ignore_index=pad_idx)：计算预测值与真实值之间的交叉熵损失。
        ignore_index 参数告诉损失函数，自动忽略标签中值为 pad_idx 的位置（即填充部分），不计算它们的损失
    '''
    # loss = F.cross_entropy(predict_logit, target, ignore_index=pad_idx)
    logit = logit[..., :-1, :].contiguous().view(-1, logit.size(-1))
    labels = target[..., 1:].contiguous().view(-1)
    loss = F.cross_entropy(logit, labels, ignore_index=pad_idx)
    return loss


def calculate_acc(logit, labels, ignore_index=-100):
    '''
    评估模型预测的准确度，逻辑比损失计算更精细, 步骤:
    1. 数据预处理
    2. 获取预测结果
    3. 构建掩码，过滤填充符
    4. 计算正确数与总数
    :param logit:
    :param labels:
    :param ignore_index:
    :return:
    '''
    # print(f'logit--->原始值的形状{logit.shape}')
    # print(f'labels--->原始值的形状{labels.shape}')
    # print(f' logit.size---{logit.size(-1)}')
    # print(f' logit[:, :-1, :]---{logit[:, :-1, :].shape}')
    #  1. 数据预处理:
    #       同样执行了“错位对齐”和“展平”操作，确保预测值 logit 和标签 labels 在相同的维度上进行比较
    logit = logit[:, :-1, :].contiguous().view(-1, logit.size(-1))
    # print(f'logit改变完形状的--->{logit.shape}')
    # print(f'labels[:, 1:]--->{labels[:, 1:].shape}')
    labels = labels[:, 1:].contiguous().view(-1)
    # print(f'labels真实标签--->{labels.shape}')
    # logit.max(dim=-1)：对每个预测单词，取出最大概率值以及对应索引
    # 2. 获取预测结果
    #       在词表维度上取最大值，获取概率最高的那个词的索引（ID）。此时 logit 从概率分布变成了具体的预测词 ID 序列
    _, logit = logit.max(dim=-1)  # 对于每条数据，返回最大的index
    # print(f'_-->{_}')
    # print(f'logit取出模型预测最大索引值-->{logit}')
    # print(f'logit预测结果---》{logit.shape}')
    '''
    在 PyTorch 中，labels.ne(ignore_index) 表示将标签张量 labels 中的值不等于 ignore_index 的位置标记为 True，等于 ignore_index 的位置标记为 False。
    这个操作，以过滤掉 ignore_index 对损失的贡献
    '''
    # 进行非运算，返回一个tensor，若labels的第i个位置为pad_id，则置为0，否则为1
    # 3. 构建掩码，过滤填充符
    #       创建一个布尔掩码。labels.ne(-100) 会检查标签是否不等于 -100（忽略索引）
    #       结果是一个布尔张量，真实词的位置为 True，填充符（PAD）的位置为 False。这一步至关重要，防止模型通过“瞎猜填充符”来刷高准确率
    non_pad_mask = labels.ne(ignore_index)
    # print(f'non_pad_mask-->{non_pad_mask}')
    '''
    在 PyTorch 中，logit.eq(labels) 表示将模型的预测输出值 logit 中等于标签张量 labels 的位置标记为 True，
    不等于标签张量 labels 的位置标记为 False。以标记出预测输出值和标签值相等的位置。
    masked_select(non_pad_mask) 表示将张量中非填充标记的位置选出来。
    '''
    # print(f'logit.eq(labels)--->{ logit.eq(labels)}')
    # print(f'logit.eq(labels)--->{logit.eq(labels).shape}')
    # 4. 计算正确数与总数
    #       logit.eq(labels)：比较预测 ID 和真实 ID，相等为 True，不等为 False。
    #       masked_select(non_pad_mask)：利用上面的掩码，只保留非填充符位置的比较结果。
    #       sum().item()：统计 True 的数量，即为预测正确的词数 (n_correct)。
    #       non_pad_mask.sum().item()：统计掩码中 True 的数量，即为实际需要预测的总词数 (n_word)。
    n_correct = logit.eq(labels).masked_select(non_pad_mask).sum().item()
    # print(f'n_correct-->{n_correct}')
    n_word = non_pad_mask.sum().item()
    # print(f'non_pad_mask.sum()-->{non_pad_mask.sum()}')
    return n_correct, n_word
