import os
from pathlib import Path

class Configuration:
    def __init__(self):
        self.PROJECT_ROOT = Path(__file__).parent.parent
        
        # Model paths
        self.HAAR_CASCADE_PATH = str(self.PROJECT_ROOT / 'weights' / 'haarcascade_frontalface.xml')
        self.MASK_MODEL_PATH = str(self.PROJECT_ROOT / 'weights' / 'face_mask_model.h5')
        
        # Database configuration
        self.DB_HOST = os.getenv('DB_HOST', 'localhost')
        self.DB_PORT = int(os.getenv('DB_PORT', 5432))
        self.DB_NAME = os.getenv('DB_NAME', 'face_mask_detection')
        self.DB_USER = os.getenv('DB_USER', 'postgres')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD', '')
        
        # Video processing parameters
        self.FRAME_WIDTH = 640
        self.FRAME_HEIGHT = 480
        self.FPS = 30
        
        # Model parameters
        self.CONFIDENCE_THRESHOLD = 0.5
        
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"