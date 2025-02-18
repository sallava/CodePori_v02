import cv2
import numpy as np

def resize_image(image, target_size):
    return cv2.resize(image, target_size)

def normalize_image(image):
    return image.astype('float32') / 255.0

def prepare_face_roi(face_roi, target_size=(224, 224)):
    resized = resize_image(face_roi, target_size)
    normalized = normalize_image(resized)
    return normalized

def augment_image(image):
    augmented = []
    augmented.append(image)
    augmented.append(cv2.flip(image, 1))
    return augmented