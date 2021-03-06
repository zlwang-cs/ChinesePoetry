import pickle

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

from Model import Model
from DataStructure import PoetryDataSet

OUTPUT_FILE = open("checkpoint/output.txt", "w", encoding="utf-8")


def OUTPUT(string):
    OUTPUT_FILE.write("{}\n".format(string))
    OUTPUT_FILE.flush()


word_dict_file = open("data/proc/dict.pkl", "rb")
word_dict = pickle.load(word_dict_file)
word_matrix = torch.load("data/proc/matrix.torch")

dataset_name = ["train", "val"]
dataset_file = [open("data/proc/{}.pkl".format(n), "rb") for n in dataset_name]
dataset_list = [pickle.load(f) for f in dataset_file]

epoch_num = 100
batch_size = 100
vocabulary_size = len(word_dict)
embedding_dim = 128
fc_dim = 256
hidden_size = 64

train_dataset = PoetryDataSet(dataset_list[0])
valid_dataset = PoetryDataSet(dataset_list[1])

train_dataloader = DataLoader(train_dataset, shuffle=True, batch_size=batch_size, drop_last=True)
valid_dataloader = DataLoader(valid_dataset, shuffle=True, batch_size=batch_size, drop_last=True)

model = Model(vocab_size=vocabulary_size, embedding_dim=embedding_dim, batch_size=batch_size, fc_dim=fc_dim,
              hidden_size=hidden_size, word_vec_matrix=word_matrix).cuda()
optimizer = optim.RMSprop(model.parameters(), lr=0.01, weight_decay=0.0001)
loss_func = nn.NLLLoss(reduce=True, size_average=True)


def train(epoch_id):
    model.train()
    running_loss = 0.
    running_acc = 0.
    for poem in train_dataloader:
        optimizer.zero_grad()
        project = model(poem[0])

        loss_four = 0.
        acc_four = 0.
        for project_batch, tag_batch in zip(project, poem):
            loss_batch = sum([loss_func(p, t) for p, t in zip(project_batch, tag_batch)])
            loss_four += loss_batch / batch_size

            pred_batch = project_batch.max(dim=2)[1]
            acc_batch = sum([sum([1 if p == t else 0 for p, t in zip(pred, tag)]) / 7
                             for pred, tag in zip(pred_batch, tag_batch)])
            acc_four += acc_batch / batch_size

        loss = loss_four / 4
        acc = acc_four / 4

        print("Loss: {:.5f}, Acc: {:.5f}".format(loss, acc))

        running_loss += float(loss)
        running_acc += float(acc)

        loss.backward()
        optimizer.step()

    running_loss /= (train_dataset.length // batch_size)

    print("Train: [%d/%d] Loss: %.5f, Acc: %.5f" % (epoch_id + 1, epoch_num, running_loss, running_acc))
    OUTPUT("Train: [%d/%d] Loss: %.5f, Acc: %.5f" % (epoch_id + 1, epoch_num, running_loss, running_acc))


def valid(epoch_id):
    model.eval()
    running_loss = 0.
    running_acc = 0.
    for poem in valid_dataloader:
        project = model(poem[0])

        loss_four = 0.
        acc_four = 0.
        for project_batch, tag_batch in zip(project, poem):
            loss_batch = sum([loss_func(p, t) for p, t in zip(project_batch, tag_batch)])
            loss_four += loss_batch / batch_size

            pred_batch = project_batch.max(dim=2)[1]
            acc_batch = sum([sum([1 if p == t else 0 for p, t in zip(pred, tag)]) / 7
                             for pred, tag in zip(pred_batch, tag_batch)])
            acc_four += acc_batch / batch_size

        loss = loss_four / 4
        acc = acc_four / 4

        running_loss += float(loss)
        running_acc += float(acc)

    running_loss /= (valid_dataset.length // batch_size)
    running_loss /= (valid_dataset.length // batch_size)

    print("Valid: [%d/%d] Loss: %.5f, Acc: %.5f" % (epoch_id + 1, epoch_num, running_loss, running_acc))
    OUTPUT("Valid: [%d/%d] Loss: %.5f, Acc: %.5f" % (epoch_id + 1, epoch_num, running_loss, running_acc))


for epoch_id in range(epoch_num):
    valid(epoch_id)
    train(epoch_id)

    if (epoch_id + 1) % 5 == 0:
        torch.save(model.state_dict(), "checkpoint/EPOCH_{}_model.torch".format(epoch_id))
