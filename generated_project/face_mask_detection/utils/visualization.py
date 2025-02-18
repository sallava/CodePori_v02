import cv2
import numpy as np

def draw_bbox(frame, bbox, color, thickness=2):
    x, y, w, h = bbox
    cv2.rectangle(frame, (x, y), (x+w, y+h), color, thickness)

def draw_text(frame, text, position, color, scale=0.5, thickness=2):
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, text, position, font, scale, color, thickness)

def create_status_bar(frame, status_text, color):
    height, width = frame.shape[:2]
    cv2.rectangle(frame, (0, height-30), (width, height), color, -1)
    draw_text(frame, status_text, (10, height-10), (255, 255, 255))

def overlay_mask_status(frame, prediction):
    status = prediction['label']
    confidence = prediction['confidence']
    color = (0, 255, 0) if status == "Mask" else (0, 0, 255)
    text = f"{status}: {confidence:.2f}"
    create_status_bar(frame, text, color)