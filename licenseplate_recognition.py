from helpers.utilities import get_segments, process_characters, decode_predictions
import character_segmentation
from helpers.load_models import load_models
import sys, getopt
import cv2
import numpy as np
import os
from tqdm import tqdm


def recognize(images):
    licenseplate_localizer, character_classifier = load_models()

    licenseplates = []
    for image in images:
        result = licenseplate_localizer.return_predict(image)
        result.sort(key=lambda x: float(x["confidence"]), reverse=True)

        x = result[0]["topleft"]["x"]
        y = result[0]["topleft"]["y"]
        w = result[0]["bottomright"]["x"] - result[0]["topleft"]["x"]
        h = result[0]["bottomright"]["y"] - result[0]["topleft"]["y"]

        licenseplates.append(cv2.cvtColor(get_segments(image, [[x, y, w, h]])[0], cv2.COLOR_BGR2GRAY))

    license_plate_segments = character_segmentation.process_images(license_plate_images=licenseplates)

    # cv2.imshow("plate", licenseplates[-1])
    # if cv2.waitKey(0) & 0xFF == 27:
    #     cv2.destroyAllWindows()

    licenseplate_numbers = []
    for characters in license_plate_segments:
        characters = process_characters(characters)
        # licenseplate_number = classify_characters(characters)
        preds = character_classifier.predict(characters)
        licenseplate_number = decode_predictions(preds)
        licenseplate_numbers.append(licenseplate_number)
        print(licenseplate_number)
    return licenseplate_numbers[0]

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

    images = []
    for image_filename in tqdm(os.listdir(imagedir)):
        image = cv2.imread(os.path.join(imagedir, image_filename))
        image = np.array(image)
        images.append(image)

    recognize(images, licenseplate_localizer, character_classifier)
