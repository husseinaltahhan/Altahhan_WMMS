# server.py
from flask import Flask, send_from_directory, abort
import os
from config import config

app = Flask(__name__)

@app.route('/<filename>')
def serve_file(filename):
    try:
        # Security check to prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            abort(403)
        
        # Check if file exists
        file_path = os.path.join("ota_files", filename)
        print(file_path)
        if not os.path.exists(file_path):
            abort(404)
            
        return send_from_directory("ota_files", filename)
    except Exception as e:
        app.logger.error(f"Error serving file {filename}: {e}")
        abort(500)

@app.errorhandler(404)
def not_found(error):
    return "File not found", 404

@app.errorhandler(403)
def forbidden(error):
    return "Access forbidden", 403

@app.errorhandler(500)
def internal_error(error):
    return "Internal server error", 500

if __name__ == '__main__':
    #flask_config = config.get_flask_config()
    #app.run(**flask_config)
    app.run(host="0.0.0.0", port=80, debug=False, threaded=True)
