import os
import sys
import cv2
import filters
import utilities
from tqdm import tqdm


def process_images(license_plate_images, show_index=-1):
    license_plate_predictions = []

    for index, image in tqdm(enumerate(license_plate_images)):
        show = True if index == show_index else False

        original = utilities.resize(image, dims=(800, 200), show=show, title="original")
        image = original.copy()

        image = filters.denoise(image, blur_method="bilateral", kernel=15, sigma=20, show=show, title="bilateral-blur")
        image = filters.binarize(image, inverted=True, adaptive=False, show=show)
        image = filters.denoise(image, blur_method="median", kernel=3, show=show, title="median-blur")
        image = filters.get_canny_edges(image, show=show)

        image_title = "img_" + str(index) + ".jpg"
        bboxes = utilities.get_bboxes(image, original.copy(), threshold_w=2.5, threshold_h=0.25, show=show, save=False, title=image_title)

        license_plate_predictions.append((original.copy(), bboxes))
        if show:
            if cv2.waitKey(0) & 0xFF == 27:
                cv2.destroyAllWindows()

    return license_plate_predictions


def find_accuracy(license_plate_predictions, license_plate_numbers, image_folder_path, show=False, save=False):
    correct = 0
    partial = 0

    correct_savepath = os.path.join(image_folder_path, "correct")
    wrong_savepath = os.path.join(image_folder_path, "wrong")

    if save:
        os.mkdir(correct_savepath)
        os.mkdir(wrong_savepath)

    for (image, bboxes), plate_number in zip(license_plate_predictions, license_plate_numbers):
        if len(plate_number) == len(bboxes):
            image_filepath = os.path.join(correct_savepath, str(plate_number) + ".jpg")
            if save:
                utilities.save_image(image, image_filepath)
            correct += 1
        else:
            image_filepath = os.path.join(wrong_savepath, str(plate_number) + ".jpg")
            if save:
                utilities.save_image(image, image_filepath)
        partial += 1 - abs(len(plate_number) - len(bboxes)) / len(plate_number)

    accuracy_license_plate = (correct / len(license_plate_predictions)) * 100
    accuracy_characters = (partial / len(license_plate_predictions)) * 100

    if show:
        print("total accuracy = {:.2f}%".format(accuracy_license_plate))
        print("accuracy per plate = {:.2f}%".format(accuracy_characters))

    return accuracy_license_plate, accuracy_characters


def main(image_folder_path):
    license_plate_images = []
    license_plate_numbers = []
    for filename in os.listdir(image_folder_path):
        image_path = os.path.join(image_folder_path, filename)
        image = utilities.get_image(image_path)
        plate_number = filename.split(".")[0]
        license_plate_images.append(image)
        license_plate_numbers.append(plate_number)

    license_plate_predictions = process_images(license_plate_images, show_index=3)
    accuracy_license_plate, accuracy_characters = find_accuracy(license_plate_predictions, license_plate_numbers, image_folder_path, show=True, save=False)


if __name__ == "__main__":
    image_folder_path = sys.argv[1]
    main(image_folder_path)
