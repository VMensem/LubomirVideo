from flask import Flask, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
import re
import urllib.parse

app = Flask(__name__)
app.secret_key = "any-secret-key"

# Папка для завантажень
UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Дозволені розширення
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "tiff", "svg"}
VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "wmv", "flv", "webm"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_video_type(url: str):
    """Визначає тип відео для iframe або прямого відтворення"""
    url_lower = url.lower()
    if "youtube.com/watch" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    elif "instagram.com/p/" in url_lower:
        return "instagram"
    elif "facebook.com" in url_lower:
        return "facebook"
    elif any(cloud in url_lower for cloud in ["drive.google.com", "dropbox.com", "onedrive.live.com"]):
        return "cloud"
    else:
        return "direct"

@app.context_processor
def inject_now():
    from datetime import datetime
    return {"now": datetime.utcnow()}

@app.route("/")
def index():
    images = sorted([f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(tuple(IMAGE_EXTENSIONS))])
    videos = sorted([f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(tuple(VIDEO_EXTENSIONS))])
    return render_template(
        "index.html",
        images=images,
        videos=videos,
        name=os.environ.get("PHOTOGRAPHER_NAME", "Любомир Казюк")
    )

@app.route("/gallery")
def gallery():
    files = os.listdir(UPLOAD_FOLDER)
    video_links = []
    video_file_path = os.path.join(UPLOAD_FOLDER, "video_links.txt")
    if os.path.exists(video_file_path):
        with open(video_file_path, "r", encoding="utf-8") as f:
            for line in f.readlines():
                line = line.strip()
                if line:
                    video_links.append({
                        "url": line,
                        "type": detect_video_type(line)
                    })
    return render_template("gallery.html", files=files, video_links=video_links)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        login = request.form.get("login")
        password = request.form.get("password")

        if login == os.environ.get("ADMIN_USER") and password == os.environ.get("ADMIN_PASSWORD"):
            file = request.files.get("file")
            video_link = request.form.get("video_link")

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                flash(f"Файл {filename} успішно завантажено!")
            elif video_link:
                # Перетворюємо деякі хмарні посилання на прямі потоки (якщо потрібно)
                video_link = convert_cloud_link(video_link)
                with open(os.path.join(UPLOAD_FOLDER, "video_links.txt"), "a", encoding="utf-8") as f:
                    f.write(video_link + "\n")
                flash("Відео додано!")
            else:
                flash("Невірний тип файлу або файл/посилання не вибрано")
            return redirect(url_for("upload"))
        else:
            flash("Невірний логін або пароль")
    return render_template("upload.html")

def convert_cloud_link(url: str) -> str:
    """Перетворює Google Drive / Dropbox / OneDrive на пряме посилання для <video>"""
    if "drive.google.com" in url:
        # Google Drive share link -> direct download
        match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/uc?export=download&id={file_id}"
    elif "dropbox.com" in url:
        # Dropbox ?dl=0 -> dl=1
        url = re.sub(r'\?dl=0', '?dl=1', url)
        return url
    elif "onedrive.live.com" in url:
        # Onedrive: перетворення на пряме посилання трохи складніше, залишимо як є
        return url
    return url

if __name__ == "__main__":
    app.run(debug=True)
