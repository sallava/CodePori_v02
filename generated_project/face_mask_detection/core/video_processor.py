import cv2
import numpy as np

class VideoProcessor:
    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.colors = {
            "Mask": (0, 255, 0),  # Green
            "No Mask": (0, 0, 255),  # Red
            "Error": (255, 255, 0)  # Yellow
        }
    
    def preprocess_frame(self, frame):
        return cv2.resize(frame, (640, 480))
    
    def extract_face_roi(self, frame, face):
        x, y, w, h = face
        return frame[y:y+h, x:x+w]
    
    def draw_prediction(self, frame, face, prediction):
        x, y, w, h = face
        label = prediction["label"]
        confidence = prediction["confidence"]
        
        color = self.colors.get(label, (255, 255, 0))
        
        # Draw rectangle around face
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        
        # Draw label and confidence
        label_text = f"{label}: {confidence:.2f}"
        cv2.putText(frame, label_text, (x, y-10),
                    self.font, 0.5, color, 2)