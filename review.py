# logit = logit[..., :-1, :].contiguous().view(-1, logit.size(-1))
# labels = target[..., 1:].contiguous().view(-1)

# import torch
# pred = torch.randn(2, 3, 4) # 模型预测结果
# print(f'pred--》{pred}')
# labels = torch.randn(2, 3)
# print(f'labels-->{labels}')
# print(labels[..., 1:].shape)
# print(labels[:, 1:].shape)
# new_labels = labels[..., 1:].contiguous().view(-1)
# print(new_labels.shape)
# logit = pred[..., :-1, :]
# # print(f'logit-->{logit}')
# # print(f'logit-->{logit.shape}')
# # # # logit = pred[:, :-1, :]
# new_logit  = logit.contiguous().view(-1, pred.size(-1))
# # print(logit.shape)
# print(new_logit.shape)

# a = [1, 2, 3]
# input = a
# labels = a
#
# # loss计算的时候，错位的
# input1 = input[:-1]
# labels = labels[1:]
# print(f'input1-->{input1}')
# print(f'labels-->{labels}')
# list1 = [1, 2]
# list2 = [2,34]
# list1.extend(list2)
# from transformers import GPT2LMHeadModel, GPT2Config
# from parameter_config import *
# params = ParameterConfig()
# # 创建模型
# if params.pretrained_model:
#     # 加载预训练模型
#     model = GPT2LMHeadModel.from_pretrained(params.pretrained_model)
# else:
#     # 初始化模型
#     print("没有使用预训练模型")
#     model_config = GPT2Config.from_json_file(params.config_json)
#     model = GPT2LMHeadModel(config=model_config)
# print(model)
#
#
# from  datetime import datetime
# epoch_start_time = datetime.now()
# print(epoch_start_time)
# import torch
# a = torch.randn(1)
# print(a)
# print(a.mean())
# from datetime import datetime
#
# print(datetime.now())
#
# print(a[:1].shape) # [1, 3, 4]
# print(a[:1, :].shape) # [1, 3, 4]+4
# print(a[:1, :, :].shape) # [1, 3, 4]+4
#
# # print(a[2, :].shape) #  会报错+2
#
# print(a[:1, 2, :2].shape)  # [1, 2]
# print(a[:, 1].shape) # [2, 4]
# print(a[0, :2, 3].shape) # [2]
# print(a[0, 2].shape) # [4]
# 进行张量切片操作的时候，先看维度选择是否对齐，如果没有对齐，默认的维度全选；如果全部对齐，就看有几个冒号，最后的切片结果维度就是几

# import torch
# a = torch.tensor([[3.9, 6.4],
#                   [2.3, 9.6]])
# b = torch.tensor([False, True, False, True, True, True])
# print(b.sum())
# a.shape(2, 2)
# print(a.max(dim=-1))
# _, idx = a.max(dim=-1)
# print(idx)

# print(a.argmax(dim=-1))
# print(a.topk(1, dim=1))
import torch
torch.manual_seed(1)
logits = torch.tensor([1.2, 3.6, 2.4, 4.8])
print(logits)
a, c = torch.topk(logits, k=2)
print(f'a-->{a}')
print(a[..., -1, None])
print(a[-1])
# list1 = [1, 2]
# list2 = [2, 3]
# # list1.extend(list2)
# # print(list1)
# print(list1[:-4])
print(torch.tensor([2]))

print(logits < a[..., -1, None])
print(logits < a[-1])
bb = logits < a[..., -1, None]
filter_value=-float('Inf')
logits[bb] = filter_value
print(logits)