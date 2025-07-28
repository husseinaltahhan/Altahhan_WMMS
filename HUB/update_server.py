# server.py
from flask import Flask, send_from_directory

app = Flask(__name__)

@app.route('/<filename>')
def serve_file(filename):
    return send_from_directory("ota_files", filename)

app.run(host='0.0.0.0', port=80)
