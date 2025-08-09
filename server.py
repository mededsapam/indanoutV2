import os
from flask import Flask, request, render_template, jsonify, send_from_directory
from datetime import datetime
from zoneinfo import ZoneInfo
import csv
from werkzeug.utils import secure_filename

# Config
UPLOAD_FOLDER = "captured_images"
LOG_CSV = "log.csv"
ALLOWED_EXT = {"png", "jpg", "jpeg"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder="captured_images")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB limit

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def now_wib_iso():
    # Asia/Jakarta is UTC+7
    tz = ZoneInfo("Asia/Jakarta")
    return datetime.now(tz).isoformat(timespec='seconds')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    # Require explicit photo field
    if "photo" not in request.files:
        return "No photo provided", 400

    photo = request.files["photo"]
    if photo.filename == "":
        return "Empty filename", 400
    if not allowed_file(photo.filename):
        return "File type not allowed", 400

    # Save the file with safe filename + timestamp
    ts = now_wib_iso().replace(":", "-")
    filename = secure_filename(f"{ts}_{photo.filename}")
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    photo.save(filepath)

    # Collect metadata
    user_agent_header = request.headers.get("User-Agent", request.form.get("clientUA", "unknown"))
    lat = request.form.get("latitude", "")
    lon = request.form.get("longitude", "")
    hari = request.form.get("hari", "")
    jam = request.form.get("jam", "")
    material = request.form.get("material", "")
    keterangan = request.form.get("keterangan", "")

    client_ip = request.remote_addr or ""

    # Log to CSV: timestamp_WIB, filename, user_agent, ip, latitude, longitude, hari, jam, material, keterangan
    header = ["timestamp_wib", "filename", "user_agent", "ip", "latitude", "longitude", "hari", "jam", "material", "keterangan"]
    write_header = not os.path.exists(LOG_CSV)
    row = [now_wib_iso(), filename, user_agent_header, client_ip, lat, lon, hari, jam, material, keterangan]

    try:
        with open(LOG_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(header)
            writer.writerow(row)
    except Exception as e:
        # if logging fails, still return 500
        return f"Failed to write log: {e}", 500

    return jsonify({"status": "ok", "filename": filename})

# Optional: serve captured images (only for dev; consider access controls in production)
@app.route("/captured_images/<path:filename>")
def serve_image(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    # For Replit use port from env; otherwise default 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
  
