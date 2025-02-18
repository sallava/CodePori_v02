from config.config import Config
import logging

class TemperatureAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def analyze_temperature(self, temperature):
        """Analyze temperature reading and determine status"""
        try:
            if temperature < Config.NORMAL_TEMP_MIN:
                status = 'LOW'
            elif temperature > Config.NORMAL_TEMP_MAX:
                status = 'HIGH'
            else:
                status = 'NORMAL'
                
            return {
                'status': status,
                'is_normal': status == 'NORMAL'
            }
            
        except Exception as e:
            self.logger.error(f'Error analyzing temperature: {str(e)}')
            raise