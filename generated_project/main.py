from flask import Flask, render_template, jsonify
from modules.camera_controller import CameraController
from modules.opencv_processor import OpenCVProcessor
from modules.temperature_analyzer import TemperatureAnalyzer
from modules.data_manager import DataManager
from config.config import config
from datetime import datetime, timedelta
import cv2
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    filename=config.app.log_file,
    level=getattr(logging, config.app.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize components
camera = CameraController()
opencv = OpenCVProcessor()
analyzer = TemperatureAnalyzer()
data_manager = DataManager()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/api/current-reading')
def get_current_reading():
    frame, temp_data = camera.get_frame()
    if frame is None:
        return jsonify({'error': 'Failed to capture frame'}), 500

    # Convert frame to OpenCV format
    cv_frame = frame.GetNDArray()
    processed_frame, face_roi = opencv.process_frame(cv_frame)

    if face_roi is None:
        return jsonify({'error': 'No face detected'}), 404

    temperature = opencv.extract_temperature(temp_data, face_roi)
    analysis = analyzer.analyze_temperature(temperature)

    # Save to database if alert is required
    if analysis['alert_required']:
        data_manager.save_temperature_reading(
            temperature=analysis['temperature'],
            status=analysis['status'],
            alert_triggered=True
        )

    return jsonify(analysis)

@app.route('/api/statistics')
def get_statistics():
    period = timedelta(hours=24)
    stats = data_manager.get_statistics(period)
    return jsonify(stats)

@app.route('/api/alerts')
def get_alerts():
    start_date = datetime.now() - timedelta(hours=24)
    alerts = data_manager.get_alerts(start_date)
    return jsonify([alert.to_dict() for alert in alerts])

def initialize_system():
    if not camera.initialize():
        logging.error('Failed to initialize camera')
        return False
    logging.info('System initialized successfully')
    return True

def cleanup_system():
    camera.release()
    logging.info('System cleanup completed')

if __name__ == '__main__':
    try:
        if initialize_system():
            app.run(
                host=config.app.flask_host,
                port=config.app.flask_port,
                debug=config.app.debug
            )
    finally:
        cleanup_system()