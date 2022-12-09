const cors = require('cors');
const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs');
const logger = require('simple-node-logger').createSimpleLogger('project.log');
const { exec } = require("child_process");
const CronJob = require('cron').CronJob;
const path = require("path");

const app = express();
app.use(cors());
app.use(bodyParser.urlencoded({
    extended: true
}));
app.use(express.json())

logger.info("*************** Starting Server ***************");

const rawdata = fs.readFileSync('../assets/json/config.json');
const config = JSON.parse(rawdata);

app.listen(8080, () => {
    logger.info("Successfully started server on port 8080");
});

var trainCron = new CronJob(
    '0 * * * *',
    retrain,
    null,
    true
);

var grabAndClassifyCron = new CronJob(
    '30 1,22 * * *',
    grabImagesAndClassify,
    null,
    true
);

trainCron.start();
grabAndClassifyCron.start();

// Get the list of cameras.
app.get('/cameras', (req, res) => {
    try {
        logger.info("GET - /cameras");
        let rawdata = fs.readFileSync(config.camerasJSONPath);
        let cameras = JSON.parse(rawdata);
        res.json({ 'cameras': cameras });
    } catch (ex) {
        logger.error("Could not get list of cameras: ", ex);
        res.sendStatus(500);
    }
});

// Get the image file for a camera.
app.get('/images/:imageFile', (req, res) => {
    try {
        logger.info("GET - /images/" + req.params.imageFile);
        let file = path.join(config.predictionPath, sanitizeFileName(req.params.imageFile));

        if (!fs.existsSync(file)) {
            logger.info("Attempted to get an image file that does not exist: " + file);
            res.sendStatus(404);
        }

        res.sendFile(file);
    } catch (ex) {
        logger.error("Could not get the image file: ", ex);
        res.sendStatus(500);
    }
});

// Get the list of all possible classifications.
app.get('/classifications', (req, res) => {
    try {
        logger.info("GET - /classifications")
        let listOfClassifications = fs.readdirSync(config.trainPath);
        res.json({ 'classifications': listOfClassifications });
    } catch (ex) {
        logger.error("Failed to get list of classifications: ", ex);
        res.sendStatus(500);
    }
});

// Get the classification for a specific image id.
app.get('/classification/:id', (req, res) => {
    try {
        logger.info("GET - /classification/" + req.params.id);
        let rawdata = fs.readFileSync(config.camerasJSONPath);
        let cameras = JSON.parse(rawdata);
        res.json({ 'classification': cameras.find(x => x.id == req.params.id).classification });
    } catch (ex) {
        logger.error("Failed to get classification for image with id: ", req.params.id, ". With Exception: ", ex);
        res.sendStatus(500);
    }
});

// Report an incorrect classification.
app.post('/report', (req, res) => {
    try {
        logger.info("POST - /report");

        let rawdata = fs.readFileSync(config.reportsJSONPath);
        let reports = JSON.parse(rawdata);

        if (reports == undefined || reports == null) {
            reports = [];
        }

        if (fs.readdirSync(config.trainPath).find(x => x == sanitizeFileName(req.body.status)) == undefined) {
            res.sendStatus(400);
        }

        let report = reports.find(x => x.id == req.body.id);

        if (report == null) {
            logger.info("Adding new report for camera " + req.body.id + " of status " + req.body.status);
            reports.push({ id: req.body.id, classification: req.body.status });
            fs.writeFile(config.reportsJSONPath, JSON.stringify(reports), 'utf8', () => {
                try {
                    fs.copyFile(path.join(config.predictionPath, sanitizeFileName(req.body.id)) + ".jpg", path.join(config.trainPath, sanitizeFileName(req.body.status), + Date.now() + "-" + sanitizeFileName(req.body.id) + ".jpg"), () => {
                        res.sendStatus(200);
                    });
                } catch (ex) {
                    console.log(ex);
                }
            });
        } else {
            res.sendStatus(200);
        }
    } catch (ex) {
        logger.error("Failed to report incorrect classification: ", ex);
        res.sendStatus(500);
    }
});

function retrain() {
    logger.info("Running retrain cron...");
    let rawdata = fs.readFileSync(config.reportsJSONPath);
    let reports = JSON.parse(rawdata);

    if (reports == undefined || reports == null) {
        logger.warn("Retrain cron found an undefined, or null reports.json file. returning.");
        return;
    }

    if (reports.length > 5) {
        logger.info("Retrain cron calling python training file.");
        exec("python3 \"" + config.trainScriptPath + "\"", (error, stdout, stderr) => {
            if (error) {
                logger.error("Retrain cron encountered an error: ", error.message);
                return;
            }

            if (stdout) {
                logger.info(stdout);
            }

            if (stderr) {
                logger.warn(stderr);
            }

            classifyImages();

            fs.writeFileSync(config.reportsJSONPath, "[]");
        });
    }
}

async function classifyImages() {
    logger.info("classifyImages");

    fs.readdir(config.predictionPath, async (err, files) => {
        if (err) throw err;

        for (const file of files) {
            fs.unlinkSync(path.join(config.predictionPath, file))
        }

        logger.info("classifyImages: Finished deleting all files. Copying over files from images directory.");

        fs.readdir(config.scrapePath, async (err, files2) => {
            if (err) throw err;

            for (const file of files2) {
                fs.copyFileSync(path.join(config.scrapePath, file), path.join(config.predictionPath, file))
            }

            logger.info("classifyImages: Finished copying all files. Runing classification.");

            exec("python3 \"" + config.classifyScriptPath + "\"", (error, stdout, stderr) => {
                if (error) {
                    logger.error("Classify encountered an error: ", error.message);
                    return;
                }

                if (stdout) {
                    logger.info(stdout);
                }

                if (stderr) {
                    logger.warn(stderr);
                }

                logger.info("classifyImages: Finished.");
            });
        });
    });
}

function grabImagesAndClassify() {
    logger.info("grabImagesAndClassify");

    fs.readdir(config.scrapePath, async (err, files) => {
        if (err) throw err;

        for (const file of files) {
            fs.unlinkSync(path.join(config.scrapePath, file))
        }

        logger.info("grabImagesAndClassify: Successfully deleted all images. ");

        exec("python3 \"" + config.sceapeScriptPath + "\"", (error, stdout, stderr) => {
            if (error) {
                logger.error("grabImagesAndClassify: Classify encountered an error: ", error.message);
                return;
            }

            if (stdout) {
                logger.info(stdout);
            }

            if (stderr) {
                logger.warn(stderr);
            }

            logger.info("grabImagesAndClassify: Successfully grabbed all images.");

            classifyImages();
        });
    });
}

function sanitizeFileName(fileName) {
    if (fileName == null) {
        return;
    }

    fileName.replaceAll('/', '');
    fileName.replaceAll('..', '');
    return fileName;
}