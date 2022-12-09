import torch
import glob
import torch.nn as nn
from torchvision.transforms import transforms
from torch.utils.data import DataLoader
from torch.optim import Adam
from torch.autograd import Variable
import torchvision
import pathlib
from model import ConvNet
import json

from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

# 1) Load configuration
with open('../assets/json/config.json', 'r') as f:
    config = json.load(f)

trainPath = config['trainPath']
testPath = config['testPath']
predPath = config['predictionPath']
modelPath = config['modelPath']

# 2) Check if we can use cuda cores
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(device)

# 3) Transforms
transformer = transforms.Compose([
    transforms.Resize((350, 350)),
    transforms.RandomHorizontalFlip(),  # add variation in dataset
    transforms.ToTensor(),
    transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
])

# 4) Dataloaders
trainDataloader = DataLoader(
    torchvision.datasets.ImageFolder(trainPath, transform=transformer),
    batch_size=64, shuffle=True
)

testDataloader = DataLoader(
    torchvision.datasets.ImageFolder(testPath, transform=transformer),
    batch_size=64, shuffle=True
)

# 5) Get categories
root = pathlib.Path(trainPath)
classes = sorted([j.name.split('/')[-1] for j in root.iterdir()])
print(classes)


model = ConvNet(numClasses=len(classes)).to(device)

# 6) Optimizer and loss function
optimizer = Adam(model.parameters(), lr=0.001, weight_decay=0.0001)
lossFunction = nn.CrossEntropyLoss()

# 7) Training loop
trainCount = len(glob.glob(trainPath+'/**/*.jpg'))
testCount = len(glob.glob(testPath+'/**/*.jpg'))
print("Train count: " + str(trainCount) + " | Test Count: " + str(testCount))

numEpochs = 10
bestAccuracy = 0.0

for epoch in range(numEpochs):
    model.train()
    trainAccuracy = 0.0
    trainLoss = 0.0

    for i, (images, labels) in enumerate(trainDataloader):
        if torch.cuda.is_available():
            images = Variable(images.cuda())
            labels = Variable(labels.cuda())

        optimizer.zero_grad()

        outputs = model(images)  
        loss = lossFunction(outputs, labels)
        loss.backward()
        optimizer.step() 

        trainLoss += loss.cpu().data * images.size(0)
        _, prediction = torch.max(outputs.data, 1)

        trainAccuracy += int(torch.sum(prediction == labels.data))

    trainAccuracy = trainAccuracy / trainCount
    trainLoss = trainLoss / trainCount

    model.eval()
    testAccuracy = 0.0
    for i, (images, labels) in enumerate(trainDataloader):
        if torch.cuda.is_available():
            images = Variable(images.cuda())
            labels = Variable(labels.cuda())

        outputs = model(images)
        _, prediction = torch.max(outputs.data, 1)
        testAccuracy += int(torch.sum(prediction == labels.data))

    testAccuracy = testAccuracy / testCount

    print('Epoch: ' + str(epoch) + ' Train Loss: ' + str(int(trainLoss)) +
          ' Train Accuracy: ' + str(trainAccuracy) + ' Test Accuracy: ' + str(testAccuracy))

    # Save the best model
    if testAccuracy > bestAccuracy:
        torch.save(model.state_dict(), modelPath)
        bestAccuracy = testAccuracy
