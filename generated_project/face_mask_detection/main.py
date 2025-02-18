import logging
from pathlib import Path
import cv2
import tensorflow as tf

from config.configuration import Configuration
from core.detector import FaceDetector
from core.model import MaskDetectionModel
from core.video_processor import VideoProcessor
from core.database_manager import DatabaseManager
from models.detection_event import DetectionEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaceMaskDetectionSystem:
    def __init__(self):
        self.config = Configuration()
        
        self.face_detector = FaceDetector(
            model_path=str(Path(self.config.FACE_CASCADE_PATH))
        )
        
        self.mask_model = MaskDetectionModel(
            model_path=str(Path(self.config.MASK_MODEL_PATH))
        )
        
        self.video_processor = VideoProcessor()
        self.db_manager = DatabaseManager()

    def run(self):
        try:
            cap = cv2.VideoCapture(0)
            
            while True:
                success, frame = cap.read()
                if not success:
                    logger.error("Failed to grab frame")
                    break
                    
                processed_frame = self.video_processor.preprocess_frame(frame)
                faces = self.face_detector.detect_faces(processed_frame)
                
                for face in faces:
                    face_roi = self.video_processor.extract_face_roi(processed_frame, face)
                    prediction = self.mask_model.predict(face_roi)
                    
                    self.video_processor.draw_prediction(
                        frame, face, prediction
                    )
                    
                    event = DetectionEvent(
                        timestamp=tf.timestamp(),
                        mask_status=prediction["label"],
                        confidence=prediction["confidence"]
                    )
                    self.db_manager.log_detection(event)
                
                cv2.imshow("Face Mask Detection", frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except Exception as e:
            logger.error(f"Error in detection system: {str(e)}")
            
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.db_manager.close()

def main():
    try:
        system = FaceMaskDetectionSystem()
        system.run()
    except Exception as e:
        logger.error(f"Failed to initialize system: {str(e)}")

if __name__ == "__main__":
    main()