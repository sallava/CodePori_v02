import os
import json
import io
import zipfile
import logging
from flask import Flask, render_template, request, Response, send_file
from main import generate_project_stream

app = Flask(__name__)
app.debug = True  # Set to False in production

# Configure logging (optional but recommended)
logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more detailed logs
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("mas.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """
    Renders the HTML interface for project generation.
    """
    return render_template('multi_agent_interface.html')

@app.route('/generate_stream')
def generate_stream():
    """
    SSE endpoint for real-time streaming of agent responses.
    Expects GET params: ?description=...&lang=...
    """
    description = request.args.get('description', '').strip()
    coding_language = request.args.get('lang', 'Python').strip()

    if not description:
        return Response(json.dumps({"error": "No project description provided."}), mimetype='application/json'), 400

    def event_stream():
        # Each chunk is JSON text from main.generate_project_stream
        for chunk in generate_project_stream(description, coding_language):
            # SSE format requires "data: ...\n\n"
            yield f"data: {chunk}\n\n"

    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/download_project/<project_name>')
def download_project(project_name):
    """
    Endpoint to download a specific generated project as a ZIP archive.
    Access via: http://127.0.0.1:5000/download_project/<project_name>
    
    Parameters:
        project_name (str): Name of the project folder to download.
    
    Security:
        - Validates the project_name to prevent directory traversal attacks.
        - Ensures the project exists within the 'generated_projects' directory.
    """
    # Define the base directory where all projects are stored
    base_dir = 'generated_project'
    
    # Sanitize the project_name to prevent directory traversal
    # Allow only alphanumeric characters, underscores, and hyphens
    if not project_name.isidentifier() and not all(c.isalnum() or c in ('-', '_') for c in project_name):
        logger.warning(f"Invalid project name attempted for download: {project_name}")
        return Response(json.dumps({"error": "Invalid project name."}), mimetype='application/json'), 400

    # Construct the absolute path to the project directory
    project_dir = os.path.join(base_dir, project_name)
    
    # Check if the project directory exists and is indeed a directory
    if not os.path.exists(project_dir) or not os.path.isdir(project_dir):
        logger.error(f"Download attempted but project '{project_name}' does not exist.")
        return Response(json.dumps({"error": f"Project '{project_name}' not found."}), mimetype='application/json'), 404

    try:
        # Create a BytesIO buffer to hold the ZIP archive in memory
        memory_file = io.BytesIO()

        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Walk through the project directory and add files to the ZIP archive
            for root, dirs, files in os.walk(project_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # To maintain the folder structure in the ZIP
                    arcname = os.path.relpath(file_path, start=project_dir)
                    zf.write(file_path, arcname)

        memory_file.seek(0)  # Reset buffer pointer to the beginning

        # Send the ZIP file as a downloadable response
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'{project_name}.zip'  # For Flask >= 2.0
            # For older Flask versions, use 'attachment_filename' instead of 'download_name'
            # attachment_filename=f'{project_name}.zip',
        )
    except Exception as e:
        logger.error(f"Error while zipping the project '{project_name}': {e}")
        return Response(json.dumps({"error": "Failed to create ZIP archive."}), mimetype='application/json'), 500

if __name__ == "__main__":
    # Ensure templates directory exists
    if not os.path.exists('templates'):
        os.makedirs('templates')
    # Ensure generated_projects directory exists
    if not os.path.exists('generated_project'):
        os.makedirs('generated_project')
    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)