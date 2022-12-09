import torch
from torchvision.transforms import transforms
from torch.autograd import Variable
from io import open
import os
from PIL import Image
import pathlib
import glob
from PIL import ImageFile
import json
from model import ConvNet

ImageFile.LOAD_TRUNCATED_IMAGES = True

# 1) Load configuration
with open('../assets/json/config.json', 'r') as f:
    config = json.load(f)

trainPath = config['trainPath']
predPath = config['predictionPath']
modelPath = config['modelPath']
camerasJSONPath = config['camerasJSONPath']

trainImageWidth = int(float(config['trainImageWidth']))
trainImageHeight = int(float(config['trainImageHeight']))

# 2) Get categories
root = pathlib.Path(trainPath)
classes = sorted([j.name.split('/')[-1] for j in root.iterdir()])
print("Discovered classes: " + str(classes))

# 3) Load model
checkpoint = torch.load(modelPath)
model = ConvNet(numClasses=len(classes))
model.load_state_dict(checkpoint)
model.eval()

# 4) Transforms
transformer = transforms.Compose([
    transforms.Resize((trainImageWidth, trainImageHeight)),
    transforms.ToTensor(),
    transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
])

# 5) Prediction
def prediction(imgPath, transformer):
    image = Image.open(imgPath)
    imageTensor = transformer(image).float()
    imageTensor = imageTensor.unsqueeze_(0)

    if torch.cuda.is_available():
        imageTensor.cuda()

    input = Variable(imageTensor)
    output = model(input)
    index = output.data.numpy().argmax()
    pred = classes[index]

    return pred


imagesPath = glob.glob(predPath + '/*.jpg')
data = []
count = 0

for i in imagesPath:
    count += 1
    latHelper = i[0:i.index("--")]
    lat = latHelper[latHelper.rindex("-") + 1:len(latHelper)]
    lng = i[i.index("--") + 1: i.rindex(".")]
    camera = {'id': str(count), 'lat': str(lat), 'lng': str(
        lng), 'classification': str(prediction(i, transformer))}

    data.append(camera)

    os.rename(i, predPath + "/" + str(count) + ".jpg")

# 6) Write json
json_data = json.dumps(data)

with open(camerasJSONPath, "w") as outfile:
    outfile.write(json_data)
