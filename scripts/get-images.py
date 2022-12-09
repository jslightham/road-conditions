import urllib.request
import requests
import json
import time
import os

# Load configuration
with open('../assets/json/config.json', 'r') as f:
    config = json.load(f)

ontarioCameraBaseURL = config['ontarioCameraBaseURL']
ontarioCameraAPI = config['ontarioCameraAPI']
scrapePath = config['scrapePath']

cameraObArray = []

class Camera:
    def __init__(self, lat, lng, url):
        self.lat = lat
        self.lng = lng
        self.url = url

# Call an endpoint on Ontraio's 511 server that lists all cameras, and populate this into the cameraObArray.
def PopulateCameraObArray():
    print("PopulateCameraObArray")
    unparsedCameras = requests.get(ontarioCameraAPI)

    parsedCameras = json.loads(unparsedCameras.content)
    parsedCameraArray = parsedCameras['item2']
    for cam in parsedCameraArray:
        tempURL = ontarioCameraBaseURL + cam["itemId"].replace("0-|", "0-0--")
        tempURL = tempURL.replace("-|", "-p1--")
        tempURL = tempURL.replace("|", "--")
        tempURL = tempURL.replace(" ", "%20")
        
        cameraObArray.append(Camera(cam["location"][0], cam["location"][1], tempURL))
    
    print ("Found: " + str(len(cameraObArray)) + " cameras")
    print("PopulateCameraObArray finished")

# Grab images from all of the cameras in cameraObArray, and store them in the images folder (set in config.json)
def CaptureCameras():
    print("CaptureCameras")
    count = 1
    for cam in cameraObArray:
        print("Capturing camera (" + str(count) + "/" + str(len(cameraObArray)) + "): " + cam.url + " at " + str(cam.lat) + ", " + str(cam.lng))
        epoch_time = int(time.time())
        fullfilename = os.path.join(scrapePath, str(epoch_time) + "-" + str(cam.lat) + "-" + str(cam.lng) + ".jpg")
        urllib.request.urlretrieve(cam.url, fullfilename)
        count = count + 1
        time.sleep(2) # wait 2 seconds to avoid being rate limited by 511ontario

PopulateCameraObArray()
CaptureCameras()
