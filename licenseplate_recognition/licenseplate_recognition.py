from tensorflow.python import util
from helpers.utilities import get_segments, process_characters, classify_characters, decode_predictions
from tensorflow.python.keras.models import load_model
from darkflow.net.build import TFNet
import character_segmentation
import sys, getopt
import cv2
import numpy as np
import os
from tqdm import tqdm


def load_models():

    options = {
        "pbLoad": "./licenseplate_recognition/weights/licenseplate_localizer/yolo-licenseplate.pb",
        "metaLoad": "./licenseplate_recognition/weights/licenseplate_localizer/yolo-licenseplate.meta",
        "threshold": 0.1,
        "gpu": 0.0,
    }

    licenseplate_localizer = TFNet(options)
    character_classifier = load_model("./licenseplate_recognition/weights/character_classifier/character_classifier.h5")

    return licenseplate_localizer, character_classifier


def main(imagedir):
    licenseplate_localizer, character_classifier = load_models()

    licenseplates = []
    for image_filename in tqdm(os.listdir(imagedir)):
        image = cv2.imread(os.path.join(imagedir, image_filename))
        image = np.array(image)
        result = licenseplate_localizer.return_predict(image)
        result.sort(key=lambda x: float(x["confidence"]), reverse=True)

        x = result[0]["topleft"]["x"]
        y = result[0]["topleft"]["y"]
        w = result[0]["bottomright"]["x"] - result[0]["topleft"]["x"]
        h = result[0]["bottomright"]["y"] - result[0]["topleft"]["y"]

        licenseplates.append(cv2.cvtColor(get_segments(image, [[x, y, w, h]])[0], cv2.COLOR_BGR2GRAY))

    # cv2.imshow("plate", licenseplates[-1])
    # if cv2.waitKey(0) & 0xFF == 27:
    #     cv2.destroyAllWindows()

    license_plate_segments = character_segmentation.process_images(license_plate_images=licenseplates)

    for characters in license_plate_segments:
        characters = process_characters(characters)
        # licenseplate_number = classify_characters(characters)
        preds = character_classifier.predict(characters)
        licenseplate_number = decode_predictions(preds)
        print(licenseplate_number)

    # for segment in license_plate_segments[0]:
    #     cv2.imshow("character", segment)
    #     if cv2.waitKey(0) & 0xFF == 27:
    #         cv2.destroyAllWindows()


if __name__ == "__main__":
    argv = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argv, "", ["imgdir="])
    except:
        print("--imgdir option is required")

    imagedir = None
    for opt, arg in opts:
        if opt == "--imgdir":
            imagedir = arg
    main(imagedir)
