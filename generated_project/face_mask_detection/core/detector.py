import cv2
import numpy as np
from typing import List, Tuple
import logging
from pathlib import Path

from config.configuration import Configuration

class FaceDetector:
    def __init__(self, config: Configuration):
        self.config = config
        self.face_cascade = self._load_face_cascade()
        self.detection_scale_factor = 1.1
        self.min_neighbors = 5
        self.min_face_size = (30, 30)
        
        logging.info("Face detector initialized successfully")

    def _load_face_cascade(self) -> cv2.CascadeClassifier:
        """Load the Haar cascade classifier for face detection"""
        cascade_path = Path(self.config.HAAR_CASCADE_PATH)
        if not cascade_path.exists():
            raise FileNotFoundError(f"Haar cascade file not found at {cascade_path}")
            
        face_cascade = cv2.CascadeClassifier(str(cascade_path))
        if face_cascade.empty():
            raise RuntimeError("Error loading face cascade classifier")
        return face_cascade

    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect faces in the input frame"""
        if frame is None:
            raise ValueError("Input frame cannot be None")
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=self.detection_scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=self.min_face_size
        )
        
        return faces

    def extract_face_roi(self, frame: np.ndarray, face_box: Tuple[int, int, int, int]) -> np.ndarray:
        """Extract face region of interest (ROI) from frame"""
        if frame is None or face_box is None:
            raise ValueError("Invalid input parameters")
            
        x, y, w, h = face_box
        face_roi = frame[y:y+h, x:x+w]
        return face_roi

    def preprocess_face(self, face_roi: np.ndarray) -> np.ndarray:
        """Preprocess face ROI for mask detection"""
        if face_roi is None or face_roi.size == 0:
            raise ValueError("Invalid face ROI")
            
        face_roi = cv2.resize(face_roi, (224, 224))
        face_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
        face_roi = face_roi.astype("float32") / 255.0
        face_roi = np.expand_dims(face_roi, axis=0)
        
        return face_roi

    def draw_face_box(self, frame: np.ndarray, face_box: Tuple[int, int, int, int], 
                     is_mask: bool, confidence: float) -> None:
        """Draw bounding box and mask status on frame"""
        if frame is None or face_box is None:
            raise ValueError("Invalid input parameters")
            
        x, y, w, h = face_box
        color = (0, 255, 0) if is_mask else (0, 0, 255)
        
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        
        label = f'Mask: {confidence:.2f}%' if is_mask else f'No Mask: {confidence:.2f}%'
        cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.45, color, 2)