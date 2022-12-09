# Road Conditions
Automatically scrape images from public road condition cameras provided by `https://511on.ca`, and use a convolutional neural network to classify the condition of all roads with cameras. Displays the results on a webpage on a map with coloured markers, photos, and tags. 

## Scripts
### Training
Training is done by `scripts/train.py`, which uses PyTorch to train a CNN. The training images are stored in `assets/images/training`, testing images are stored in `assets/images/testing`. There are no image files in the testing, or training directory (due to GitHub's storage limits). Training will not work until these folders are populated. There is a pretrained model in the assets folder.

### Classification
Classification is performed by the `scripts/classify.py` script. This script will classify any images in the `assets/predict` folder with a filename of `epochTime-lat-long.jpg`, and rename classified images to be `id.jpg`. The classification of each image is stored in `assets/jsons/cameras.json`.

### Image Scraping
Images are scraped by the python file `scripts/get-images.py`, and stored in the `assets/images` directory as a JPEG image with the name `epochTime-lat-long.jpg`. The script waits two seconds between grabbing images to prevent being rate limited. The web server by default only runs image scraping twice daily.

## Server
Written in NodeJS, using express. Controls all of the python scripts, and relays the information to the web interface through rest APIs. Currently, there is no database, instead relevant data is stored in json files in the `assets` folder. The server checks if the model needs to be retrained hourly, and calls for new images & re-classification twice per day.

## Web
### Web Interface
Written in HTML, CSS and JavaScript, with Bootstrap and Leaflet. Communicates with the web server via REST APIs to get the status of all camera nodes. Displays all of the nodes with coloured markers on a leaflet openstreetmap. There is also a modal which allows the user to report incorrect classifications (which get queued by the web server for when the model is automatically retrained). 
