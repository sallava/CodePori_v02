import tensorflow as tf
import numpy as np
import logging

logger = logging.getLogger(__name__)

class MaskDetectionModel:
    def __init__(self, model_path):
        try:
            self.model = tf.keras.models.load_model(model_path)
            self.input_shape = (224, 224)
        except Exception as e:
            logger.error(f"Failed to load mask detection model: {str(e)}")
            raise
    
    def preprocess_image(self, image):
        image = tf.image.resize(image, self.input_shape)
        image = tf.cast(image, tf.float32) / 255.0
        return np.expand_dims(image, axis=0)
    
    def predict(self, face_roi):
        try:
            processed_image = self.preprocess_image(face_roi)
            prediction = self.model.predict(processed_image)
            confidence = float(prediction[0][0])
            label = "Mask" if confidence > 0.5 else "No Mask"
            
            return {
                "label": label,
                "confidence": confidence
            }
        except Exception as e:
            logger.error(f"Error during mask prediction: {str(e)}")
            return {"label": "Error", "confidence": 0.0}