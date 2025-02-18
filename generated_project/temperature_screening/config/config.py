from dataclasses import dataclass

@dataclass
class CameraConfig:
    exposure_time: float = 20000.0
    gain: float = 1.0
    timeout: int = 1000

@dataclass
class DatabaseConfig:
    host: str = 'localhost'
    port: int = 5432
    database: str = 'temperature_screening'
    user: str = 'postgres'
    password: str = 'postgres'

@dataclass
class TemperatureConfig:
    normal_max: float = 37.5
    fever_threshold: float = 38.0
    calibration_offset: float = -0.5

config = {
    'camera': CameraConfig(),
    'database': DatabaseConfig(),
    'temperature': TemperatureConfig()
}