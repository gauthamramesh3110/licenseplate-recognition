import cv2
import numpy as np
import os


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
    sorted(bboxes, key=lambda x:x[0])

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
        segments.append(image[y:y+h, x:x+w])
    
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
