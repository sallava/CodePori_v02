from typing import Optional, Tuple
import PySpin
from config.config import config

class CameraController:
    def __init__(self):
        self.system = PySpin.System.GetInstance()
        self.camera = None
        self.initialized = False

    def initialize(self) -> bool:
        try:
            cam_list = self.system.GetCameras()
            if cam_list.GetSize() == 0:
                raise RuntimeError('No FLIR cameras detected')
                
            self.camera = cam_list[config.camera.device_id]
            self.camera.Init()
            
            # Configure camera settings
            self.camera.AcquisitionFrameRateEnable.SetValue(True)
            self.camera.AcquisitionFrameRate.SetValue(config.camera.frame_rate)
            
            self.camera.BeginAcquisition()
            self.initialized = True
            return True
            
        except PySpin.SpinnakerException as e:
            print(f'Camera initialization error: {str(e)}')
            return False

    def get_frame(self) -> Optional[Tuple[PySpin.Image, float]]:
        if not self.initialized:
            return None
            
        try:
            image = self.camera.GetNextImage()
            if image.IsIncomplete():
                return None
                
            temp_data = self._extract_temperature_data(image)
            return image, temp_data
            
        except PySpin.SpinnakerException as e:
            print(f'Frame capture error: {str(e)}')
            return None

    def _extract_temperature_data(self, image: PySpin.Image) -> float:
        # Implementation depends on specific FLIR camera model and SDK
        # This is a placeholder that would need to be customized
        return 0.0

    def release(self):
        if self.camera:
            try:
                self.camera.EndAcquisition()
                self.camera.DeInit()
                del self.camera
            except PySpin.SpinnakerException as e:
                print(f'Camera release error: {str(e)}')
                
        self.system.ReleaseInstance()
        self.initialized = False

    def __del__(self):
        self.release()