from tensorflow.python.keras.models import load_model
from darkflow.net.build import TFNet
from character_segmentation import character_segmentation

def load_models():

    options = {
        "pbLoad" : "./weights/licenseplate_localizer/yolo-licenseplate.pb",
        "metaLoad": "./weights/licenseplate_localizer/yolo-licenseplate.meta",
        "threshold": 0.5,
        "gpu": 0.0,
    }

    licenseplate_localizer = TFNet(options)
    character_classifier = load_model("./weights/character_classifier/character_classifier.h5")

    return licenseplate_localizer, character_classifier

