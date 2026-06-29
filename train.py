import torch
import os
# import sys

# 时间
from datetime import datetime
import transformers
# 配置定义GPT2模型
from transformers import GPT2LMHeadModel, GPT2Config
# 使用BERT的分词器
from transformers import BertTokenizerFast
# 导入自定义的工具类函数（计算损失和准确率）
from functions_tools import *

# 获取当前文件的父目录（即项目根目录），并加入系统路径
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目的配置文件（训练数据集路径和训练的轮次参数等）
from parameter_config import ParameterConfig

# 导入数据：dataloader
from data_preprocess.dataloader import *
from tqdm import tqdm


def train_epoch(model, train_dataloader, optimizer, scheduler, epoch, args):
    '''
    单轮训练
    :param model: GPT2模型
    :param train_dataloader: 训练数据集
    :param optimizer: 优化器：更新参数
    :param scheduler: 学习率预热
    :param epoch: 当前的轮次
    :param args: 模型配置文件的参数对象
    :return:
    '''
    # 1.指明模型训练
    # 模型状态：model.train()，开启 Dropout 和 BatchNorm 的训练模式
    model.train()
    device = args.device
    # 对于ignore_index的label token不计算梯度
    ignore_index = args.ignore_index
    epoch_start_time = datetime.now()
    total_loss = 0  # 记录下整个epoch的loss的总和

    # epoch_correct_num:每个epoch中,output预测正确的word的数量
    # epoch_total_num: 每个epoch中,output预测的word的总数量
    epoch_correct_num, epoch_total_num = 0, 0

    for batch_idx, (input_ids, labels) in enumerate(tqdm(train_dataloader)):
        input_ids = input_ids.to(device)
        # print(input_ids.shape)
        labels = labels.to(device)
        # print(f'input_ids-->{input_ids.shape}')
        # print(f'labels-->{labels.shape}')
        # print(f'将数据送入模型中。。。。。。。。。。。。。。。。')
        # print(f'labels0---->{labels.shape}')
        # 如果对模型输入不仅包含input还包含标签，那么得到结果直接就有loss值
        # outputs = model(input_ids, labels=labels)
        # # print(f'outputs-->{outputs}')
        # print(f'outputs-->{outputs.keys()}')
        # print(f'outputs.logits-->{outputs.logits.shape}')
        # print(f'outputs.loss-->{outputs.loss}')
        # # 如果对模型的输入只有input，那么模型的结果不会含有loss值，此时，可以自定义函数来计算损失
        outputs = model(input_ids, labels=labels)
        logits = outputs.logits
        # print(f'logits-->{logits.shape}')
        loss = outputs.loss
        loss = loss.mean()  # 可以省略

        # 统计该batch的预测token的正确数与总数
        # 调用 calculate_acc 函数（来自 functions_tools）计算每个批次的预测准确率
        batch_correct_num, batch_total_num = calculate_acc(logits, labels, ignore_index=ignore_index)
        # print(f'batch_correct_num-->{batch_correct_num}')
        # print(f'batch_total_num-->{batch_total_num}')
        # break
        # 计算该batch的accuracy
        batch_acc = batch_correct_num / batch_total_num
        # 统计该epoch的预测token的正确数与总数
        epoch_correct_num += batch_correct_num
        epoch_total_num += batch_total_num
        #
        total_loss += loss.item()
        # self.gradient_accumulation_steps = 4， 累积的步数
        if args.gradient_accumulation_steps > 1:
            # 损失缩放：loss = loss / args.gradient_accumulation_steps，确保累积梯度的尺度正确
            loss = loss / args.gradient_accumulation_steps
        # 前向传播
        loss.backward()

        # 梯度裁剪
        # 避免梯度爆炸的方式。梯度乘以缩放系数。self.max_grad_norm = 2.0
        # 这个梯度裁剪函数一般来说只需要调整max_norm 和norm_type这两个参数。
        # clip_grad_norm_最后就是对所有的梯度乘以一个clip_coef，
        # 而且乘的前提是clip_coef=max_norm/total_norm一定是小于1的
        # torch.nn.utils.clip_grad_norm_ 用于防止梯度爆炸，将梯度的范数限制在 args.max_grad_norm 以内
        torch.nn.utils.clip_grad_norm_(model.parameters(), args.max_grad_norm)
        #
        # 更新时机：每累积 gradient_accumulation_steps 个批次后，执行 optimizer.step()、scheduler.step() 和 optimizer.zero_grad()。
        # 进行一定step的梯度累计之后，更新参数
        if (batch_idx + 1) % args.gradient_accumulation_steps == 0:
            # 更新参数
            optimizer.step()
            # 更新学习率
            scheduler.step()
            # 清空梯度信息
            optimizer.zero_grad()
        #
        if (batch_idx + 1) % args.loss_step == 0:
            print(
                "batch {} of epoch {}, loss {}, batch_acc {}, lr {}".format(
                    batch_idx + 1, epoch + 1, loss.item() * args.gradient_accumulation_steps, batch_acc,
                    scheduler.get_lr()))

        # del input_ids, outputs

    # 记录当前epoch的平均loss与accuracy
    epoch_mean_loss = total_loss / len(train_dataloader)
    epoch_mean_acc = epoch_correct_num / epoch_total_num
    print(
        "epoch {}: loss {}, predict_acc {}".format(epoch + 1, epoch_mean_loss, epoch_mean_acc))

    # save model
    if epoch % 10 == 0 or epoch == args.epochs:
        print('saving model for epoch {}'.format(epoch + 1))
        model_path = os.path.join(args.save_model_path, 'bj_epoch{}'.format(epoch + 1))
        if not os.path.exists(model_path):
            os.mkdir(model_path)
        # 保存预训练模型的方式
        model.save_pretrained(model_path)
        print('epoch {} finished'.format(epoch + 1))
        epoch_finish_time = datetime.now()
        print('time for one epoch: {}'.format(epoch_finish_time - epoch_start_time))

    return epoch_mean_loss


def validate_epoch(model, validate_dataloader, epoch, args):
    """
    单轮验证
    :param model:
    :param validate_dataloader:
    :param epoch:
    :param args:
    :return:
    """
    print("start validating")
    # 模型状态：model.eval()，关闭 Dropout 和 BatchNorm 的训练模式
    model.eval()
    device = args.device
    ignore_index = args.ignore_index
    epoch_start_time = datetime.now()
    total_loss = 0
    # 捕获cuda out of memory exception
    with torch.no_grad():  # 禁用梯度：with torch.no_grad():，在验证阶段不计算梯度，以节省显存和加速计算
        # 仅计算验证集上的平均损失（Loss），不进行反向传播和参数更新
        for batch_idx, (input_ids, labels) in enumerate(tqdm(validate_dataloader)):
            input_ids = input_ids.to(device)
            labels = labels.to(device)
            outputs = model.forward(input_ids, labels=labels)

            # logits = outputs.logits
            loss = outputs.loss
            loss = loss.mean()

            total_loss += loss.item()
            # del input_ids, outputs

        # 记录当前epoch的平均loss
        epoch_mean_loss = total_loss / len(validate_dataloader)
        print(
            "validate epoch {}: loss {}".format(epoch + 1, epoch_mean_loss))
        epoch_finish_time = datetime.now()
        print('time for validating one epoch: {}'.format(epoch_finish_time - epoch_start_time))
        return epoch_mean_loss


def train(model, train_dataloader, validate_dataloader, args):
    """
    主训练流程
    :param model:
    :param train_dataloader:
    :param validate_dataloader:
    :param args:
    :return:
    """
    # len(train_dataloader)-->训练一次完整的数据，需要迭代多少步7544
    # t_total模型训练完毕，一共要迭代多少步
    # 总步数计算：t_total 计算了整个训练过程的总更新步数，用于调度器。
    t_total = len(train_dataloader) // args.gradient_accumulation_steps * args.epochs

    # eps，为了增加数值计算的稳定性而加到分母里的项，其为了防止在实现中除以零
    # 优化器：使用 AdamW，这是 Transformer 模型的标准优化器
    optimizer = transformers.AdamW(model.parameters(), lr=args.lr, eps=args.eps)
    '''
    这里对于模型的参数，分别进行权重参数的衰减优化：防止过拟合，以及学习率预热处理优化：
        预热：在训练初期，学习率从 0 线性增加到预设的 args.lr。
        衰减：预热结束后，学习率从 args.lr 线性衰减到 0       
        在初始阶段将学习率从较小的值逐步增加到设定的初始值，然后按照设定的学习率调整策略进行训练。
        学习率预热 的目的是让模型在初始阶段更快地适应数据，避免训练过程中因为学习率过大导致的梯度爆炸等问题，
        从而提高模型的训练效果和泛化性能。
    optimizer： 优化器
    num_warmup_steps：初始预热步数
    num_training_steps：整个训练过程的总步数
    '''
    '''
    参数的解析如下：
get_linear_schedule_with_warmup：学习率从0线性（也可非线性）增加到优化器中的初始预设lr，之后使其学习率从优化器中的初始lr线性降低到0
optimizer：这个参数需要传入一个优化器对象（optimizer object）。它代表在训练过程中用于更新模型参数的优化器，比如Adam或SGD等。

num_warmup_steps：这个参数确定学习率在开始阶段从0线性增加到初始值的步数。在Transformer模型中，通过逐渐增加学习率来稳定和加速训练过程是常见的做法。通常，这个值是总训练步数的一小部分。

num_training_steps：这个参数指定了总的训练步数或迭代次数。它表示优化器将在给定数据集上进行多少次参数更新。
    '''
    scheduler = transformers.get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=args.warmup_steps, num_training_steps=t_total
    )

    print('starting training')

    # 用于记录每个epoch训练和验证的loss
    train_losses, validate_losses = [], []
    # 记录验证集的最小loss
    best_val_loss = 10000
    # 开始训练
    for epoch in range(args.epochs):
        # ========== train ========== #
        train_loss = train_epoch(
            model=model, train_dataloader=train_dataloader,
            optimizer=optimizer, scheduler=scheduler,
            epoch=epoch, args=args)
        # train_losses.append(train_loss)
        # ========== validate ========== #
        validate_loss = validate_epoch(model=model, validate_dataloader=validate_dataloader, epoch=epoch, args=args)
        # validate_losses.append(validate_loss)

        # 保存当前困惑度最低的模型，困惑度低，模型的生成效果不一定会越好
        # 记录验证集损失最低的模型，并保存为 min_ppl_model_bj。困惑度（PPL）越低，通常意味着模型生成效果越好
        if validate_loss < best_val_loss:
            best_val_loss = validate_loss
            print('saving current best model for epoch {}'.format(epoch + 1))
            model_path = os.path.join(args.save_model_path, 'min_ppl_model_bj'.format(epoch + 1))
            if not os.path.exists(model_path):
                os.mkdir(model_path)
            model.save_pretrained(model_path)


def main():
    # 初始化配置参数
    params = ParameterConfig()

    # 设置使用哪些显卡进行训练:默认为0
    # 如果你的电脑有大于1张的显卡，可以选择使用
    # nvidia-smi:查询当前显卡的状态：4090（16G显存）：L40(48G显存)；L20(24G显存)；A100（80G）; H100（80G）;T4（16G）；V100(16G)
    # os.environ["CUDA_VISIBLE_DEVICES"] = '0'数字0代表你的第一张显卡
    # os.environ["CUDA_VISIBLE_DEVICES"] = '1'数字1代表你的第二张显卡
    # os.environ["CUDA_VISIBLE_DEVICES"] ='0, 1'代表同时利用0和1两张显卡
    os.environ["CUDA_VISIBLE_DEVICES"] = '0'  # 指定第一张显卡

    # 初始化tokenizer
    tokenizer = BertTokenizerFast(params.vocab_path, sep_token="[SEP]", pad_token="[PAD]", cls_token="[CLS]")
    # tokenizer = BertTokenizerFast(params.vocab_path)
    # print(f'tokenizer-->{tokenizer.vocab_size}')
    # sep_id = tokenizer.sep_token_id
    # pad_id = tokenizer.pad_token_id
    # cls_id = tokenizer.cls_token_id
    # # print(f'sep_id--{sep_id}')
    # # print(f'pad_id--{pad_id}')
    # # print(f'cls_id--{cls_id}')

    # 创建模型的输出目录
    # 如果没有创建会自动的创建输出目录
    if not os.path.exists(params.save_model_path):
        os.mkdir(params.save_model_path)
    #
    # 创建模型
    if params.pretrained_model:  # 加载预训练模型
        model = GPT2LMHeadModel.from_pretrained(params.pretrained_model)
    else:  # 初始化模型
        model_config = GPT2Config.from_json_file(params.config_json)
        # print(model_config)
        model = GPT2LMHeadModel(config=model_config)
    # print(f'model-->{model}')
    model = model.to(params.device)
    # print(f'model.config.vocab_size-->{model.config.vocab_size}')
    # print(f'tokenizer.vocab_size-->{tokenizer.vocab_size}')
    # assert这里相当于确认：确保模型的词表大小与分词器的词表大小一致，这是训练能正常进行的前提
    assert model.config.vocab_size == tokenizer.vocab_size

    # 计算模型参数数量
    num_parameters = 0
    parameters = model.parameters()
    for parameter in parameters:
        num_parameters += parameter.numel()
    print(f'模型参数总量---》{num_parameters}')

    # # #
    # # # # 加载训练集和验证集
    # # # # ========= Loading Dataset/Dataloder ========= #
    train_dataloader, validate_dataloader = get_dataloader(params.train_path, params.valid_path)
    print(f'train_dataloader-->{len(train_dataloader)}')
    print(f'validate_dataloader-->{len(validate_dataloader)}')
    train(model, train_dataloader, validate_dataloader, params)

if __name__ == '__main__':
    main()
