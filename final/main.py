from typing import List

import cv2
import easyocr
import numpy as np
import torch
from ultralytics import YOLO
from PIL import Image
import os


def get_cropped_from_image(imgs,
                           model: torch.nn.Module,
                           device: str = "cpu",
                           ):
    result = []

    model = model.to(device)
    predict = model(imgs)

    for pred_img in predict:

        # if pred_img.boxes.xyxy.shape != (0, 4):
        print(pred_img.boxes.xyxy.shape)
        if pred_img:
            dims = []
            for dim in pred_img.boxes.xyxy[0].cpu():
                dims.append(int(dim.item()))
            result.append(pred_img.orig_img[dims[1]:dims[3], dims[0]:dims[2]])
    return result


def increase_contrast(imgs: Image):
    result = []
    for i, image in enumerate(imgs):
        contrast_matrix = np.ones(image.shape) * 1.5

        image_con = np.uint8(np.clip(cv2.multiply(np.float64(image), contrast_matrix), 0, 255))
        # image_canny = cv2.Canny(image_con, 80, 150)
        cv2.imwrite(os.path.join("pre-ocr", f"{i}.jpg"), image_con)
        result.append(image_con)
    return result


def get_labels_from_cropped(imgs, ocr: easyocr.Reader):
    result = []
    for image in imgs:
        res = ocr.readtext(image)
        if res:
            result.append(res[0][1])
    return result



def check_labels(labels: List[str]):
    """ Результаты для каждого номера:
        0 - Проверка пройдена
        1 - Проверка не пройдена
        2 - Номер не распознан или распознан не полностью
    """
    check_weights = np.array([2, 1, 2, 1, 2, 1, 2])
    result = []
    for label in labels:
        if not label.isdigit() or len(label) != 8:
            result.append((label, 2))
        else:
            digits = np.array([int(i) for i in label])
            dot = np.dot(digits[:-1], check_weights)
            if (dot + digits[-1]) % 10 == 0:
                result.append((label, 0))
            else:
                result.append((label, 1))
    return result


if __name__ == '__main__':
    device = "cuda" if torch.cuda.is_available() else "cpu"
    img_folder = "images"

    model = YOLO("yolov8n.pt")
    reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())

    inputs = [Image.open(os.path.join(img_folder, img)) for img in os.listdir(img_folder)]

    cropped = get_cropped_from_image(inputs,
                                     model,
                                     device)
    cropped = increase_contrast(cropped)
    labels = get_labels_from_cropped(cropped, reader)
    result = check_labels(labels)
    print(result)
    print(len(result))

    count = 0
    for item in result:
        a, b = item
        if b == 0:
            count += 1
    print(count)
