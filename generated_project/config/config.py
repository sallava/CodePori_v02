import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class FlirCameraConfig:
    device_id: int = 0
    frame_rate: int = 30
    resolution: tuple = (640, 480)
    temperature_range: tuple = (30.0, 45.0)
    emissivity: float = 0.98
    distance: float = 1.0

@dataclass 
class OpenCVConfig:
    face_cascade_path: str = os.path.join(os.path.dirname(__file__), 
        '../static/haarcascade_frontalface_default.xml')
    min_face_size: tuple = (30, 30)
    scale_factor: float = 1.1
    min_neighbors: int = 5
    forehead_roi_ratio: float = 0.2

@dataclass
class TemperatureConfig:
    normal_max: float = 37.5
    fever_threshold: float = 38.0
    calibration_offset: float = -0.5
    measurement_window: int = 10
    alert_threshold: int = 3

@dataclass
class DatabaseConfig:
    host: str = 'localhost'
    port: int = 5432
    database: str = 'temperature_screening'
    user: str = 'postgres'
    password: str = 'postgres'
    pool_size: int = 5
    max_overflow: int = 10

@dataclass
class AppConfig:
    flask_host: str = '0.0.0.0'
    flask_port: int = 5000
    debug: bool = True
    log_level: str = 'INFO'
    log_file: str = 'app.log'

class Config:
    def __init__(self):
        self.camera = FlirCameraConfig()
        self.opencv = OpenCVConfig()
        self.temperature = TemperatureConfig()
        self.database = DatabaseConfig()
        self.app = AppConfig()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'camera': self.camera.__dict__,
            'opencv': self.opencv.__dict__,
            'temperature': self.temperature.__dict__, 
            'database': self.database.__dict__,
            'app': self.app.__dict__
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Config':
        config = cls()
        
        if 'camera' in config_dict:
            config.camera = FlirCameraConfig(**config_dict['camera'])
        if 'opencv' in config_dict:
            config.opencv = OpenCVConfig(**config_dict['opencv'])
        if 'temperature' in config_dict:
            config.temperature = TemperatureConfig(**config_dict['temperature'])
        if 'database' in config_dict:
            config.database = DatabaseConfig(**config_dict['database'])
        if 'app' in config_dict:
            config.app = AppConfig(**config_dict['app'])
            
        return config

config = Config()