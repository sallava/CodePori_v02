import cv2
import numpy as np
from config.config import Config
import logging

class OpenCVProcessor:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(Config.FACE_CASCADE_PATH)
        self.logger = logging.getLogger(__name__)
        
    def process_frame(self, frame_data):
        """Process thermal frame to detect faces and extract temperature"""
        try:
            frame = frame_data['frame']
            timestamp = frame_data['timestamp']
            
            # Convert thermal frame to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            if len(faces) == 0:
                raise ValueError('No faces detected')
                
            # Get forehead region of first detected face
            x, y, w, h = faces[0]
            forehead_height = int(h * Config.FOREHEAD_ROI_RATIO)
            forehead_roi = frame[y:y+forehead_height, x:x+w]
            
            # Extract temperature from forehead region
            temperature = np.max(forehead_roi)
            
            return {
                'temperature': temperature,
                'timestamp': timestamp
            }
            
        except Exception as e:
            self.logger.error(f'Error processing frame: {str(e)}')
            raise