import os
from datetime import datetime
from transformers import GPT2LMHeadModel
from transformers import BertTokenizerFast
import torch
import torch.nn.functional as F
from parameter_config import ParameterConfig

PAD = '[PAD]'
pad_id = 0


def top_k_top_p_filtering(logits, top_k=0, filter_value=-float('Inf')):
    """
    使用top-k和/或nucleus（top-p）筛选来过滤logits的分布
    实现了 Top-k 采样策略，用于在生成文本时增加多样性，避免模型总是输出最保守、概率最高的词
        参数:
            logits: logits的分布，形状为（词汇大小）
            top_k > 0: 保留概率最高的top k个标记（top-k筛选）。）。
    核心逻辑：
        安全检查：确保 top_k 的值不会超过词表大小。
        获取阈值：使用 torch.topk(logits, top_k) 找到概率最高的 k 个 token。[..., -1, None] 取出这 k 个 token 中概率最低的那个值作为阈值。
        过滤：创建一个布尔掩码 indices_to_remove，标记出所有概率低于该阈值的 token。
        置为负无穷：将这些被标记的 token 的 logits 值设为 filter_value（默认为负无穷）。这样在后续的 Softmax 操作中，它们的概率会变为 0，从而不会被采样到
    """
    assert logits.dim() == 1  # batch size 1 for now - could be updated for more but the code would be less clear
    top_k = min(top_k, logits.size(-1))  # Safety check：确保top_k不超过logits的最后一个维度大小

    if top_k > 0:
        # 移除概率小于top-k标记
        # torch.topk()返回最后一维中最大的top_k个元素，返回值为二维(values, indices)
        # ...表示其他维度由计算机自行推断
        # print(f'torch.topk(logits, top_k)--->{torch.topk(logits, top_k)}')
        # print(f'torch.topk(logits, top_k)[0]-->{torch.topk(logits, top_k)[0]}')
        # print(f'torch.topk(logits, top_k)[0][..., -1, None]-->{torch.topk(logits, top_k)[0][..., -1, None]}')
        # print(f'torch.topk(logits, top_k)[0][-1]-->{torch.topk(logits, top_k)[0][-1]}')
        # print(f'logits-->{logits}')
        indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
        # print(f'indices_to_remove--->{indices_to_remove}')
        logits[indices_to_remove] = filter_value  # 对于topk之外的其他元素的logits值设为负无穷
        # print(f'logits--->{logits}')
    return logits


def main():
    pconf = ParameterConfig()
    # 当用户使用GPU,并且GPU可用时
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print('using device:{}'.format(device))
    os.environ["CUDA_VISIBLE_DEVICES"] = '0'
    tokenizer = BertTokenizerFast(vocab_file=pconf.vocab_path,
                                  sep_token="[SEP]",
                                  pad_token="[PAD]",
                                  cls_token="[CLS]")
    model = GPT2LMHeadModel.from_pretrained(
        pconf.inference_model_path,
        local_files_only=True,
        use_safetensors=True,
    )
    model = model.to(device)
    model.eval()
    # 保存聊天记录的文件路径
    if pconf.save_samples_path:
        if not os.path.exists(pconf.save_samples_path):
            os.makedirs(pconf.save_samples_path)
        samples_file = open(pconf.save_samples_path + '/samples.txt', 'a', encoding='utf8')
        samples_file.write("聊天记录{}:\n".format(datetime.now()))
    # 存储聊天记录，每个utterance以token的id的形式进行存储
    history = []
    print('你好，我是你的生活助手')

    while True:  # 持续与用户交互
        try:
            text = input("user:")
            # print(f'text---》{text}')
            if pconf.save_samples_path:
                samples_file.write("user:{}\n".format(text))
            text_ids = tokenizer.encode(text, add_special_tokens=False)
            # print(f'text_ids-->{text_ids}')
            # print('*' * 80)
            history.append(text_ids)
            input_ids = [tokenizer.cls_token_id]  # 每个input以[CLS]为开头
            # print(f'history---{history}')
            # print(f'input_ids---{input_ids}')
            # print('*' * 80)
            #
            # 将用户输入和历史对话（由 max_history_len 参数控制保留的轮数）拼接起来，构造成模型的输入序列。
            # 序列格式为 [CLS] + 历史对话1 + [SEP] + 历史对话2 + [SEP] + ..
            # pconf.max_history_len目的：保存历史消息记录
            # eg：history =  [[872, 1962], [872, 1962], [872, 342, 123], [334, 55,234]]-->history[-3:]
            for history_id, history_utr in enumerate(history[-pconf.max_history_len:]):
                # print(f'history_utr--->{history_utr}')
                input_ids.extend(history_utr)
                input_ids.append(tokenizer.sep_token_id)
                # print(f'input_ids---》{input_ids}')
            #
            # print(f'历史对话结束--》{input_ids}')

            # 将拼接好的 ID 列表转换为 PyTorch 张量，并增加一个批次维度
            # input_ids = torch.tensor(input_ids).long().to(device)
            input_ids = torch.tensor(input_ids, dtype=torch.long, device=device)
            input_ids = input_ids.unsqueeze(0)
            # print(f'符合模型的输入--》{input_ids.shape}')
            response = []  # 根据context，生成的response
            for _ in range(pconf.max_len): # 进入一个 for 循环，逐个 token 地生成回复，直到达到最大长度 (max_len) 或生成结束符 [SEP]
                outputs = model.forward(input_ids=input_ids)
                #             outputs = model(input_ids=input_ids)
                logits = outputs.logits
                # print(f'logits---》{logits.shape}')
                #            next_token_logits生成下一个单词的概率值
                # 获取下一个 token 的概率：取出最后一个时间步的 logits (logits[0, -1, :])
                next_token_logits = logits[0, -1, :]
                # print(f'next_token_logits----》{next_token_logits.shape}')
                # 你真好[mask]--》看，美，瘦
                #             # 对于已生成的结果generated中的每个token添加一个重复惩罚项，降低其生成概率
                #             # print(f'set(response)-->{set(response)}')
                # response=[102]
                for id in set(response): # 重复惩罚：遍历已生成的 response，降低其中出现过的 token 的 logits 值，以减少重复
                    # print(f'id--->{id}')
                    next_token_logits[id] /= pconf.repetition_penalty
                # 对于[UNK]的概率设为无穷小，也就是说模型的预测结果不可能是[UNK]这个token
                # 禁用未知词：将 [UNK] token 的 logits 设为负无穷，确保模型不会生成它
                next_token_logits[tokenizer.convert_tokens_to_ids('[UNK]')] = -float('Inf')
                # Top-k 筛选：调用 top_k_top_p_filtering 函数，只保留概率最高的 top_k 个 token，其余 token 的 logits 设为负无穷
                filtered_logits = top_k_top_p_filtering(next_token_logits, top_k=pconf.topk)

                #
                # orch.multinomial表示从候选集合中无放回地进行抽取num_samples个元素，权重越高，抽到的几率越高，返回元素的下标
                # 采样：对筛选后的 logits 进行 Softmax 归一化，然后使用 torch.multinomial 进行多项式采样，随机选择下一个 token。
                next_token = torch.multinomial(F.softmax(filtered_logits, dim=-1), num_samples=1)
                # print(f'next_token-->{next_token}')

                if next_token.item() == tokenizer.sep_token_id:  # 遇到[SEP]则表明response生成结束
                    break
                # 拼接与更新：将采样得到的 token ID 添加到 response 列表和 input_ids 中，作为下一轮生成的上下文
                response.append(next_token.item())
                # print(f'response-->{response}')
                input_ids = torch.cat((input_ids, next_token.unsqueeze(0)), dim=1)
            # 输出与保存：
            #   将生成的 token ID 列表 response 通过 tokenizer.convert_ids_to_tokens 转换回文本并打印。
            #   将本轮的用户输入和机器人回复都添加到 history 中，用于下一轮对话。
            #   （可选）将对话记录写入文件
            history.append(response)
            text = tokenizer.convert_ids_to_tokens(response)
            print("chatbot:" + "".join(text))
        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    main()
