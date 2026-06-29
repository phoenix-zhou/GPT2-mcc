# 导入依赖模块
# 导入分词器
# BertTokenizerFast, BertTokenizer：从 Hugging Face 的 transformers 库导入 BERT 分词器。
# Fast 版本基于 Rust 实现，处理速度比标准版快很多
from transformers import BertTokenizerFast, BertTokenizer
import pickle  # # 将数据保存为pkl文件，方便下次读取
from tqdm import tqdm  # 加在进度条
import os

def data_preprocess(train_txt_path, train_pkl_path):
    """
    对原始语料进行tokenizer，将每段对话处理成如下形式："[CLS]sentence1[SEP]sentence2[SEP]sentence3[SEP]"
    :param train_txt_path: 原始文本路径
    :param train_pkl_path: 输出 pkl 文件路径
    :return:
    """

    # 初始化分词器与特殊字符
    # 初始化tokenizer，使用BertTokenizerFast从预训练的中文Bert模型（bert-base-chinese）创建一个tokenizer对象
    # tokenizer = BertTokenizerFast.from_pretrained('/Users/ligang/PycharmProjects/llm/prompt_tasks/bert-base-chinese',
    # 使用 BertTokenizerFast 加载自定义的词汇表文件 ../vocab/vocab.txt，并显式指定了 BERT 的三个特殊 Token：
    # [SEP]：分隔符，用于区分不同的句子或对话轮次。
    # [PAD]：填充符，用于将不同长度的序列对齐到相同长度。
    # [CLS]：起始符，通常放在序列开头，其最终隐藏状态可作为整个序列的聚合表示                                        )
    tokenizer = BertTokenizerFast('../vocab/vocab.txt',
                                  sep_token="[SEP]",
                                  pad_token="[PAD]",
                                  cls_token="[CLS]")
    # 打印词表大小
    print(f'tokenizer.vocab_size-->{tokenizer.vocab_size}')

    sep_id = tokenizer.sep_token_id  # 获取分隔符[SEP]的token ID
    cls_id = tokenizer.cls_token_id  # 获取起始符[CLS]的token ID
    # [SEP] 和 [CLS] 对应的数字 ID
    print(f'sep_id-->{sep_id}')
    print(f'cls_id-->{cls_id}')
    # #
    #
    # # 读取训练数据集, 读取与切分原始语料
    with open(train_txt_path, 'rb') as f:
        data = f.read().decode("utf-8")  # 以UTF-8编码读取文件内容
    # print(data)
    # 根据换行符区分不同的对话段落，需要区分Windows和Linux\mac环境下的换行符
    # 兼容跨平台换行符：通过判断文本中是否包含 \r\n（Windows换行符）来决定按 \r\n\r\n 还是 \n\n 进行切分。
    # 这里以双换行符作为不同对话段落（样本）的分界线
    if "\r\n" in data:
        train_data = data.split("\r\n\r\n")
    else:
        train_data = data.split("\n\n")
    # #
    print(len(train_data))  # 打印对话段落数量
    print(train_data[:2])

    # 核心 Tokenize 逻辑
    # 开始进行tokenize
    # 保存所有的对话数据,每条数据的格式为："[CLS]seq1[SEP]seq2[SEP]seq3[SEP]"
    dialogue_len = []  # 记录所有对话tokenize分词之后的长度，用于统计中位数与均值
    dialogue_list = []  # 记录所有对话: 记录处理后的数据
    # # # # #
    for index, dialogue in enumerate(tqdm(train_data)):
        # print(f'dialogue-->{dialogue}')
        # 同样兼容单换行符，将一段对话按行切分成多个独立的句子（sequences）
        if "\r\n" in dialogue:
            sequences = dialogue.split("\r\n")
        else:
            sequences = dialogue.split("\n")
        # print(f'sequences--》{sequences}')
        # 初始化 input_ids 列表，并将 [CLS] 的 ID 作为序列的开头
        input_ids = [cls_id]  # 每个dialogue以[CLS]seq1[sep]seq2[sep]
        for sequence in sequences:
            # 调用 tokenizer.encode(sequence, add_special_tokens=False) 将文本转为 ID 列表。
            # 关键点：这里必须设置 add_special_tokens=False，因为代码需要手动控制 [SEP] 的插入位置，
            # 防止 BERT 自动在句首句尾添加额外的 [CLS] 或 [SEP]
            input_ids += tokenizer.encode(sequence, add_special_tokens=False)  # 将每个对话句子进行tokenize，并将结果拼接到input_ids列表中
            # input_ids += tokenizer.encode(sequence)  # 将每个对话句子进行tokenize，并将结果拼接到input_ids列表中
            input_ids.append(sep_id)  # 每个seq之后添加[SEP]，表示seqs会话结束

        # 记录当前对话的总长度，并将完整的 input_ids 存入 dialogue_list
        dialogue_len.append(len(input_ids))  # 将对话的tokenize后的长度添加到对话长度列表中
        dialogue_list.append(input_ids)  # 将tokenize后的对话添加到对话列表中

    #保存数据
    with open(train_pkl_path, "wb") as f:
        pickle.dump(dialogue_list, f)


if __name__ == '__main__':
    train_txt_path = '../data/medical_train.txt'
    train_pkl_path = '../data/medical_train.pkl'
    data_preprocess(train_txt_path, train_pkl_path)
