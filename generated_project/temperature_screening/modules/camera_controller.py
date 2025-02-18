import time
from typing import Optional, Tuple
import PySpin
import numpy as np
from config.config import CameraConfig

class CameraController:
    def __init__(self, config: CameraConfig):
        self.config = config
        self.system = None
        self.camera = None
        self.initialized = False
        
    def initialize(self) -> bool:
        """Initialize FLIR camera connection"""
        try:
            # Initialize PySpin system
            self.system = PySpin.System.GetInstance()
            cam_list = self.system.GetCameras()
            
            if cam_list.GetSize() == 0:
                raise RuntimeError("No cameras detected")
                
            # Get first camera
            self.camera = cam_list[0]
            
            # Initialize camera
            self.camera.Init()
            
            # Configure camera settings
            self.camera.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
            self.camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
            self.camera.ExposureTime.SetValue(self.config.exposure_time)
            self.camera.Gain.SetValue(self.config.gain)
            
            # Start acquisition
            self.camera.BeginAcquisition()
            
            self.initialized = True
            return True
            
        except PySpin.SpinnakerException as e:
            print(f"Error initializing camera: {e}")
            return False
            
    def get_frame(self) -> Optional[Tuple[np.ndarray, float]]:
        """Capture frame and temperature data from camera"""
        if not self.initialized:
            return None
            
        try:
            # Get next image
            image_result = self.camera.GetNextImage(self.config.timeout)
            
            if image_result.IsIncomplete():
                return None
                
            # Convert to numpy array
            frame = image_result.GetNDArray()
            
            # Get temperature data
            temp_data = self._get_temperature_data(image_result)
            
            # Release image
            image_result.Release()
            
            return frame, temp_data
            
        except PySpin.SpinnakerException as e:
            print(f"Error capturing frame: {e}")
            return None
            
    def _get_temperature_data(self, image) -> float:
        """Extract temperature data from image"""
        try:
            # Get temperature from center region
            height, width = image.GetHeight(), image.GetWidth()
            center_y = height // 2
            center_x = width // 2
            region_size = 10
            
            temp_sum = 0
            count = 0
            
            for y in range(center_y - region_size, center_y + region_size):
                for x in range(center_x - region_size, center_x + region_size):
                    if 0 <= y < height and 0 <= x < width:
                        temp_sum += image.GetPixel(x, y)
                        count += 1
                        
            return temp_sum / count if count > 0 else 0
            
        except PySpin.SpinnakerException as e:
            print(f"Error getting temperature data: {e}")
            return 0.0
            
    def release(self):
        """Release camera resources"""
        try:
            if self.camera:
                self.camera.EndAcquisition()
                self.camera.DeInit()
                del self.camera
            
            if self.system:
                self.system.ReleaseInstance()
                
        except PySpin.SpinnakerException as e:
            print(f"Error releasing camera: {e}")
            
    def __del__(self):
        self.release()