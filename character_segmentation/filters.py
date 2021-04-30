import numpy as np
import cv2


def denoise(image, blur_method="gaussian", kernel=(3, 3), sigma=0, show=False, title="denoise"):
    if blur_method == "gaussian":
        image = cv2.GaussianBlur(image, kernel, sigma)
    elif blur_method == "median":
        image = cv2.medianBlur(image, kernel)
    elif blur_method == "bilateral":
        image = cv2.bilateralFilter(image, kernel, sigma, sigma)
    if show:
        cv2.imshow(title, image)
    return image


def binarize(image, inverted=False, adaptive=True, show=False, title="binarize"):
    binary_threshold = cv2.THRESH_BINARY_INV if inverted else cv2.THRESH_BINARY
    adaptive_threshold = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
    if adaptive:
        image = cv2.adaptiveThreshold(image, 255, adaptive_threshold, binary_threshold, 11, 2)
    else:
        image = cv2.threshold(image, 0, 255, binary_threshold | cv2.THRESH_OTSU)[1]
    if show:
        cv2.imshow(title, image)
    return image

def get_canny_edges(image, min=30, max=200, show=False, title="canny"):
    image = cv2.Canny(image, min, max)
    if show:
        cv2.imshow(title, image)
    return image

def dilate(image, kernel_size=(3, 3), show=False, title="dilate"):
    kernel = np.ones(kernel_size, np.uint8)
    image = cv2.dilate(image, kernel, iterations=1)
    if show:
        cv2.imshow(title, image)
    return image


def erode(image, kernel_size=(3, 3), show=False, title="erode"):
    kernel = np.ones(kernel_size, np.uint8)
    image = cv2.erode(image, kernel, iterations=1)
    if show:
        cv2.imshow(title, image)
    return image


def opening(image, kernel_size=(3, 3), show=False, title="opening"):
    kernel = np.ones(kernel_size, np.uint8)
    image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
    if show:
        cv2.imshow(title, image)
    return image


def invert(image, show=False, title="invert"):
    image = cv2.bitwise_not(image)
    if show:
        cv2.imshow(title, image)
    return image

