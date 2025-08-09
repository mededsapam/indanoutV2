import os
from flask import Flask, request, render_template, jsonify
from datetime import datetime
from zoneinfo import ZoneInfo
import csv
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "captured_images"
LOG_FILE = "log.csv"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def now_wib():
    return datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    photo = request.files.get("photo")
    if not photo:
        return "No photo uploaded", 400

    filename = secure_filename(f"{now_wib().replace(' ', '_')}_{photo.filename}")
    photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    # Data lainnya
    latitude = request.form.get("latitude", "")
    longitude = request.form.get("longitude", "")
    user_agent = request.form.get("userAgent", request.headers.get("User-Agent", ""))
    hari = request.form.get("hari", "")
    jam = request.form.get("jam", "")
    material = request.form.get("material", "")
    keterangan = request.form.get("keterangan", "")
    ip_addr = request.remote_addr

    log_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not log_exists:
            writer.writerow([
                "timestamp_wib",
                "filename",
                "user_agent",
                "ip",
                "latitude",
                "longitude",
                "hari",
                "jam",
                "material",
                "keterangan"
            ])
        writer.writerow([
            now_wib(),
            filename,
            user_agent,
            ip_addr,
            latitude,
            longitude,
            hari,
            jam,
            material,
            keterangan
        ])

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
