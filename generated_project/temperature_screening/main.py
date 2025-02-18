from flask import Flask, render_template, jsonify
from modules.camera_controller import CameraController 
from modules.opencv_processor import OpenCVProcessor
from modules.temperature_analyzer import TemperatureAnalyzer
from modules.data_manager import DataManager
from config.config import Config
import logging

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
try:
    camera = CameraController()
    processor = OpenCVProcessor()
    analyzer = TemperatureAnalyzer()
    data_mgr = DataManager()
except Exception as e:
    logger.error(f"Failed to initialize components: {str(e)}")
    raise

@app.route('/')
def dashboard():
    """Render main dashboard"""
    return render_template('dashboard.html')

@app.route('/history')
def history():
    """Render temperature history page"""
    return render_template('history.html')

@app.route('/api/current-reading')
def get_current_reading():
    """Get current temperature reading"""
    try:
        # Capture frame from thermal camera
        frame = camera.capture_frame()
        
        # Process frame to detect faces and extract temperature
        processed_data = processor.process_frame(frame)
        
        # Analyze temperature reading
        analysis = analyzer.analyze_temperature(processed_data['temperature'])
        
        # Store reading in database
        data_mgr.store_reading(processed_data['temperature'], 
                             processed_data['timestamp'],
                             analysis['status'])
        
        return jsonify({
            'temperature': processed_data['temperature'],
            'timestamp': processed_data['timestamp'],
            'status': analysis['status']
        })
        
    except Exception as e:
        logger.error(f"Error getting temperature reading: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/readings/history')
def get_reading_history():
    """Get historical temperature readings"""
    try:
        history = data_mgr.get_readings()
        return jsonify(history)
    except Exception as e:
        logger.error(f"Error retrieving reading history: {str(e)}")
        return jsonify({'error': str(e)}), 500

def cleanup():
    """Cleanup resources before shutdown"""
    try:
        camera.disconnect()
        data_mgr.close_connection()
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

if __name__ == '__main__':
    try:
        # Initialize camera connection
        camera.connect()
        
        # Start Flask development server
        app.run(host=Config.FLASK_HOST,
               port=Config.FLASK_PORT,
               debug=Config.DEBUG_MODE)
               
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        raise
        
    finally:
        cleanup()