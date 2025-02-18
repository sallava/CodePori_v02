import cv2
import numpy as np
from typing import Optional, Tuple
from config.config import config

class OpenCVProcessor:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(config.opencv.face_cascade_path)
        if self.face_cascade.empty():
            raise ValueError('Failed to load face cascade classifier')

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Optional[Tuple[int, int, int, int]]]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=config.opencv.scale_factor,
            minNeighbors=config.opencv.min_neighbors,
            minSize=config.opencv.min_face_size
        )
        
        if len(faces) == 0:
            return frame, None
            
        # Process the largest face detected
        face = max(faces, key=lambda x: x[2] * x[3])
        x, y, w, h = face
        
        # Draw rectangle around face
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Get forehead ROI
        forehead_roi = self._get_forehead_roi(face)
        cv2.rectangle(frame, 
                      (forehead_roi[0], forehead_roi[1]),
                      (forehead_roi[0] + forehead_roi[2], forehead_roi[1] + forehead_roi[3]),
                      (255, 0, 0), 2)
        
        return frame, forehead_roi

    def _get_forehead_roi(self, face: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
        x, y, w, h = face
        forehead_h = int(h * config.opencv.forehead_roi_ratio)
        forehead_y = y + int(h * 0.1)  # 10% from top of face
        
        return (x, forehead_y, w, forehead_h)

    def extract_temperature(self, thermal_data: np.ndarray, roi: Tuple[int, int, int, int]) -> float:
        x, y, w, h = roi
        roi_temp = thermal_data[y:y+h, x:x+w]
        
        # Return maximum temperature in ROI
        return np.max(roi_temp)

    def overlay_temperature(self, frame: np.ndarray, temp: float, position: Tuple[int, int]):
        cv2.putText(frame,
                    f'{temp:.1f}°C',
                    position,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255) if temp >= config.temperature.fever_threshold else (0, 255, 0),
                    2)