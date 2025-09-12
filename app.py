from flask import Flask, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename

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

@app.context_processor
def inject_now():
    from datetime import datetime
    return {"now": datetime.utcnow()}

@app.route("/")
def index():
    images = sorted([f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(tuple(IMAGE_EXTENSIONS))])
    videos = sorted([f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(tuple(VIDEO_EXTENSIONS))])
    return render_template("index.html", images=images, videos=videos, name=os.environ.get("PHOTOGRAPHER_NAME","Любомир Казюк"))

@app.route("/gallery")
def gallery():
    files = os.listdir(UPLOAD_FOLDER)

    youtube_links = []
    youtube_file_path = os.path.join(UPLOAD_FOLDER, "youtube_links.txt")
    if os.path.exists(youtube_file_path):
        with open(youtube_file_path, "r", encoding="utf-8") as f:
            youtube_links = [line.strip() for line in f.readlines() if line.strip()]

    return render_template("gallery.html", files=files, youtube_links=youtube_links)

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
            youtube_link = request.form.get("youtube_link")

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                flash(f"Файл {filename} успішно завантажено!")
            elif youtube_link:
                with open(os.path.join(UPLOAD_FOLDER, "youtube_links.txt"), "a", encoding="utf-8") as f:
                    f.write(youtube_link + "\n")
                flash("YouTube відео додано!")
            else:
                flash("Невірний тип файлу або файл/посилання не вибрано")

            return redirect(url_for("upload"))
        else:
            flash("Невірний логін або пароль")

    return render_template("upload.html")

if __name__ == "__main__":
    app.run(debug=True)
