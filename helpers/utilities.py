import cv2
import numpy as np
import os
from pytesseract import *
from . import filters


def get_image(image_path, is_grayscale=True, show=False, title="original"):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if is_grayscale else image
    if show:
        cv2.imshow(title, image)
    return image


def save_image(image, image_filepath):
    cv2.imwrite(image_filepath, image)


def resize(image, scale=2, dims=None, show=False, title="resize"):
    if dims is None:
        image = cv2.resize(image, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    else:
        image = cv2.resize(image, dims, interpolation=cv2.INTER_CUBIC)

    if show:
        cv2.imshow(title, image)
    return image


def square_pad(image, show=False, title="square_pad"):
    height, width, _ = image.shape
    h_pad = max(0, height - width)
    v_pad = max(0, width - height)
    image = cv2.copyMakeBorder(image, v_pad, v_pad, h_pad, h_pad, cv2.BORDER_CONSTANT, value=(255, 255, 255))

    if show:
        cv2.imshow(title, image)
    return image


def get_bboxes(image, original, threshold_h=0.15, threshold_w=0.15, step_size=1, show=False, save=False, title="filtered"):
    contours, hierarchy = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    bboxes = []
    max_height, min_height = 0, image.shape[0]
    max_width, min_width = 0, image.shape[1]

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        bboxes.append([x, y, w, h])
        max_height, min_height = max(max_height, h), min(min_height, h)
        max_width, min_width = max(max_width, w), min(min_width, w)

    if show:
        draw_bboxes(original.copy(), bboxes, "unfiltered")

    bboxes = filter_bboxes(bboxes, min_height, max_height, min_width, max_width, threshold_h, threshold_w, step_size, show=False)
    bboxes.sort(key=lambda x: x[0])

    if show or save:
        draw_bboxes(original.copy(), bboxes, title, save=save)

    return bboxes


def filter_bboxes(bboxes, min_height, max_height, min_width, max_width, threshold_h, threshold_w, step_size, show=False):
    filtered_bboxes = []

    for base_h in range(min_height, max_height):
        thresh_h = base_h + int(base_h * threshold_h)

        if show:
            print(base_h, thresh_h)

        temp = list(filter(lambda bbox: bbox[3] in range(base_h, thresh_h), bboxes))

        if len(temp) > len(filtered_bboxes):
            filtered_bboxes = temp

    bboxes = filtered_bboxes.copy()

    filtered_bboxes = []

    for base_w in range(min_width, max_width):
        thresh_w = base_w + int(base_w * threshold_w)

        if show:
            print(base_w, thresh_w)

        temp = list(filter(lambda bbox: bbox[2] in range(base_w, thresh_w), bboxes))

        if len(temp) > len(filtered_bboxes):
            filtered_bboxes = temp

    temp = []
    for i in range(len(filtered_bboxes)):
        bbox1 = filtered_bboxes[i]
        overlap = False

        for j in range(i + 1, len(filtered_bboxes)):
            bbox2 = filtered_bboxes[j]

            if iou(bbox1, bbox2) > 0.95:
                overlap = True
                break

        if not overlap:
            temp.append(bbox1)

    filtered_bboxes = temp

    if show:
        print(len(bboxes), len(filtered_bboxes))

    return filtered_bboxes


def get_segments(image, bboxes):
    segments = []

    for [x, y, w, h] in bboxes:
        segments.append(image[y : y + h, x : x + w])

    return segments


def draw_bboxes(image, bboxes, title="bbox", save=False):
    for (x, y, w, h) in bboxes:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 0))

    if save:
        save_path = os.path.join(os.getcwd(), "bboxes", title)
        save_image(image, save_path)
    else:
        cv2.imshow(title, image)


def iou(bbox1, bbox2):
    [x1, y1, w1, h1] = bbox1
    [x2, y2, w2, h2] = bbox2

    xmin = max(x1, x2)
    ymin = max(y1, y2)
    xmax = min(x1 + w1, x2 + w2)
    ymax = min(y1 + h1, y2 + h2)

    intersection = (xmax - xmin) * (ymax - ymin)
    union = (w1 * h1) + (w2 * h2) - intersection

    if union == 0:
        return 0
    return intersection / union


def add_padding(image, color):
    h, w = image.shape

    top = int(max(w - h, 0) / 2)
    bottom = max(w - h, 0) - top
    left = int(max(h - w, 0) / 2)
    right = max(h - w, 0) - left

    image = cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return image


def add_border(image, thickness, color):
    image = cv2.copyMakeBorder(image, thickness, thickness, thickness, thickness, cv2.BORDER_CONSTANT, value=color)
    return image


def process_characters(characters):

    processed_characters = []

    for character in characters:
        character = filters.denoise(character, blur_method="bilateral", kernel=15, sigma=20)
        character = filters.binarize(character, inverted=True, adaptive=False)
        character = filters.denoise(character, blur_method="median", kernel=3)
        # character = filters.erode(character)

        character = add_padding(character, (0, 0, 0))
        character = resize(character, dims=(22, 22))
        character = add_border(character, 3, (0, 0, 0))
        processed_characters.append(character)

        cv2.imshow("character", character)
        if cv2.waitKey(0) & 0xFF == 27:
            cv2.destroyAllWindows()

    processed_characters = np.array(processed_characters).reshape(-1, 28, 28, 1) / 255.0
    return processed_characters


def decode_predictions(preds):
    characters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    state_codes = [
        "AN",
        "AP",
        "AR",
        "AS",
        "BR",
        "CG",
        "CH",
        "DD",
        "DL",
        "DN",
        "GA",
        "GJ",
        "HR",
        "HP",
        "JH",
        "JK",
        "KA",
        "KL",
        "LD",
        "MH",
        "ML",
        "MN",
        "MP",
        "MZ",
        "NL",
        "OD",
        "PB",
        "PY",
        "RJ",
        "SK",
        "TN",
        "TR",
        "TS",
        "UK",
        "UP",
        "WB",
    ]
    decoded_preds = ""

    # FIRST CHARACTER
    whitelist = [0] * 36
    for sc in state_codes:
        index = characters.index(sc[0])
        whitelist[index] = preds[0][index]

    index = np.argmax(whitelist)
    decoded_preds = decoded_preds + characters[index]

    # SECOND CHARACTER
    whitelist = [0] * 36
    for sc in list(filter(lambda x: x[0] == decoded_preds[0], state_codes)):
        index = characters.index(sc[1])
        whitelist[index] = preds[1][index]

    index = np.argmax(whitelist)
    decoded_preds = decoded_preds + characters[index]

    # THIRD AND FOURTH
    for pred in preds[2:4]:
        whitelist = pred.copy()
        whitelist[10:] = [0] * 26
        index = np.argmax(whitelist)
        decoded_preds = decoded_preds + characters[index]

    # FIFTH AND SIXTH
    for pred in preds[4:6]:
        whitelist = pred.copy()
        whitelist[:10] = [0] * 10
        index = np.argmax(whitelist)
        decoded_preds = decoded_preds + characters[index]

    # REST OF IT
    for pred in preds[6:]:
        whitelist = pred.copy()
        whitelist[10:] = [0] * 26
        index = np.argmax(whitelist)
        decoded_preds = decoded_preds + characters[index]

    return decoded_preds


def classify_characters(characters):
    string = ""
    state_codes = [
        "AN",
        "AP",
        "AR",
        "AS",
        "BR",
        "CG",
        "CH",
        "DD",
        "DL",
        "DN",
        "GA",
        "GJ",
        "HR",
        "HP",
        "JH",
        "JK",
        "KA",
        "KL",
        "LD",
        "MH",
        "ML",
        "MN",
        "MP",
        "MZ",
        "NL",
        "OD",
        "PB",
        "PY",
        "RJ",
        "SK",
        "TN",
        "TR",
        "TS",
        "UK",
        "UP",
        "WB",
    ]

    character_whitelist = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    number_whitelist = "0123456789"
    first_whitelist = ""
    second_whitelist = ""

    for sc in state_codes:
        if sc[0] not in first_whitelist:
            first_whitelist = first_whitelist + sc[0]
    string = string + pytesseract.image_to_string(characters[0], config="--psm 10 -c tessedit_char_whitelist=" + first_whitelist).strip()

    for sc in list(filter(lambda x: x[0] == string, state_codes)):
        if sc[1] not in second_whitelist:
            second_whitelist = second_whitelist + sc[1]
    string = string + pytesseract.image_to_string(characters[1], config="--psm 10 -c tessedit_char_whitelist=" + second_whitelist).strip()

    string = string + "-"

    for c in characters[2:4]:
        string = string + pytesseract.image_to_string(c, lang="eng", config="--psm 10 -c tessedit_char_whitelist=" + number_whitelist).strip()
    string = string + "-"

    for c in characters[4:6]:
        string = string + pytesseract.image_to_string(c, lang="eng", config="--psm 10 -c tessedit_char_whitelist=" + character_whitelist).strip()
    string = string + "-"

    for c in characters[6:]:
        string = string + pytesseract.image_to_string(c, lang="eng", config="--psm 10 -c tessedit_char_whitelist=" + number_whitelist).strip()
    string = string + "-"

    return string
