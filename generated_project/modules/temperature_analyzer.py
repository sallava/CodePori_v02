from typing import List, Optional
from collections import deque
from datetime import datetime
from config.config import config

class TemperatureAnalyzer:
    def __init__(self):
        self.readings = deque(maxlen=config.temperature.measurement_window)
        self.alert_count = 0
        self.last_alert_time = None

    def analyze_temperature(self, temperature: float) -> dict:
        # Apply calibration offset
        calibrated_temp = temperature + config.temperature.calibration_offset
        
        self.readings.append(calibrated_temp)
        
        result = {
            'temperature': calibrated_temp,
            'status': self._get_temperature_status(calibrated_temp),
            'alert_required': self._check_alert_required(calibrated_temp),
            'average': self._get_average_temperature(),
            'timestamp': datetime.now()
        }
        
        return result

    def _get_temperature_status(self, temperature: float) -> str:
        if temperature >= config.temperature.fever_threshold:
            return 'FEVER'
        elif temperature >= config.temperature.normal_max:
            return 'ELEVATED'
        else:
            return 'NORMAL'

    def _check_alert_required(self, temperature: float) -> bool:
        if temperature >= config.temperature.fever_threshold:
            self.alert_count += 1
            
            if self.alert_count >= config.temperature.alert_threshold:
                current_time = datetime.now()
                
                # Reset alert if it's been more than 5 minutes
                if (self.last_alert_time is None or 
                    (current_time - self.last_alert_time).total_seconds() > 300):
                    self.last_alert_time = current_time
                    self.alert_count = 0
                    return True
        else:
            self.alert_count = max(0, self.alert_count - 1)
            
        return False

    def _get_average_temperature(self) -> Optional[float]:
        if not self.readings:
            return None
            
        return sum(self.readings) / len(self.readings)

    def reset(self):
        self.readings.clear()
        self.alert_count = 0
        self.last_alert_time = None