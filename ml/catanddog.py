import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.autograd import Variable
from torchvision import datasets, transforms
import numpy as np
import os.path

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
pklfile = "./pkl/catanddog.pkl"
random_state = 1
torch.manual_seed(random_state)
torch.cuda.manual_seed(random_state)
torch.cuda.manual_seed_all(random_state)
np.random.seed(random_state)

use_gpu = torch.cuda.is_available()
epochs = 10
batch_size = 32

# 对元数据归一化 处理为224*224*3 --> 224*224*1
data_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    # channel = (channel - mean) / std
])

train_dataset = datasets.ImageFolder(root='D:\\workstation\\GitHub\\NYU_CS_Homework_Python\\ml\\data\\cats_and_dogs_small\\train', transform=data_transform)
train_loader= torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_dataset = datasets.ImageFolder(root='D:\\workstation\\GitHub\\NYU_CS_Homework_Python\\ml\\data\\cats_and_dogs_small\\test', transform=data_transform)
test_loader= torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

class vgg16(nn.Module):
    def __init__(self):
        super(vgg16, self).__init__()
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(64, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.conv4 = nn.Conv2d(128, 128, kernel_size=3, padding=1)
        self.conv5 = nn.Conv2d(128, 256, kernel_size=3, padding=1)
        self.conv6 = nn.Conv2d(256, 256, kernel_size=3, padding=1)
        self.conv7 = nn.Conv2d(256, 512, kernel_size=3, padding=1)
        self.conv8 = nn.Conv2d(512, 512, kernel_size=3, padding=1)
        self.fc1 = nn.Linear(7 * 7 * 512, 4096)
        self.fc2 = nn.Linear(4096, 4096)
        self.fc3 = nn.Linear(4096, 1000)


    def forward(self, x):
        x = self.pool(F.relu(self.conv2(F.relu(self.conv1(x)))))
        x = self.pool(F.relu(self.conv4(F.relu(self.conv3(x)))))
        x = self.pool(F.relu(self.conv6(F.relu(self.conv6(F.relu(self.conv5(x)))))))
        x = self.pool(F.relu(self.conv8(F.relu(self.conv8(F.relu(self.conv7(x)))))))
        x = self.pool(F.relu(self.conv8(F.relu(self.conv8(F.relu(self.conv8(x)))))))
        x = x.view(-1, 7 * 7 * 512)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)  
        self.pool = nn.MaxPool2d(2, 2)  
        self.conv2 = nn.Conv2d(6, 16, 5)   
        self.fc1 = nn.Linear(53*53*16, 1024)
        self.fc2 = nn.Linear(1024, 512)
        self.fc3 = nn.Linear(512, 64)
        self.fc4 = nn.Linear(64, 2)
    
    def forward(self, x):
        # conv = (inputsize + 2 * padding - kernal_size) / stride + 1
        # maxpool = (inputsize - kernal_size) / stride + 1 
        x = self.pool(F.relu(self.conv1(x))) # 224*224*3 --> 220*220*6 --> 110*110*6
        x = self.pool(F.relu(self.conv2(x))) # 110*110*6 --> 106*106*16 --> 53*53*16
        x = x.view(-1, 53*53*16)
        x = F.relu(self.fc1(x)) 
        x = F.relu(self.fc2(x)) 
        x = F.relu(self.fc3(x)) 
        x = self.fc4(x) 
        return x

net = Net()
if os.path.exists(pklfile):
    net.load_state_dict(torch.load(pklfile))
    print("load model success")
    net.eval()

if use_gpu:
    net = net.cuda()
print(net)

loss = nn.CrossEntropyLoss()
optimizer = optim.SGD(net.parameters(), lr=0.001, momentum=0.9)

for epoch in range(epochs):
    running_loss = 0.0
    train_correct = 0
    train_total = 0
    for i, data in enumerate(train_loader):
        inputs, train_lables = data
        if use_gpu:
            inputs, train_lables = Variable(inputs.cuda()), Variable(train_lables.cuda())
        else:
            inputs, train_lables = Variable(inputs), Variable(train_lables)
        optimizer.zero_grad()
        outputs = net(inputs)
        _, predicted = torch.max(outputs.data, 1)
        train_total += train_lables.size(0)
        train_correct += (predicted == train_lables.data).sum()
        _loss = loss(outputs, train_lables)
        _loss.backward()
        optimizer.step()
        running_loss += _loss.item()

        if (i+1) % 10 == 0:
            print("epoch %d id %d loss: %.3f acc: %.3f" % (epoch+1, i+1, running_loss/train_total, 100*train_correct/train_total))
        if (i+1) % 100 == 0:
            torch.save(net.state_dict(), pklfile)
            print("save model success")

correct = 0
test_loss = 0.0
test_total = 0
for data in test_loader:
    images, labels = data
    if use_gpu:
        images, labels = Variable(images.cuda()), Variable(labels.cuda())
    else:
        images, labels = Variable(images), Variable(labels)
    outputs = net(images)
    _, predicted = torch.max(outputs.data, 1)
    test_total += labels.size(0)
    correct += (predicted == labels.data).sum()
    _loss = loss(outputs, labels)
    test_loss += _loss.item()
print("test loss: %.3f acc: %.3f" % (test_loss/test_total, 100*correct/test_total))