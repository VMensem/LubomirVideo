from flask import Flask, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "any-secret-key"

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'svg', 'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm' }
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.context_processor
def inject_now():
    from datetime import datetime
    return {"now": datetime.utcnow()}

@app.route("/")
def index():
    images = sorted([f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(("png","jpg","jpeg","gif"))])
    videos = sorted([f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(("mp4","mov"))])
    return render_template("index.html", images=images, videos=videos, name=os.environ.get("PHOTOGRAPHER_NAME","Любомир Казюк"))

@app.route("/gallery")
def gallery():
    files = os.listdir(os.path.join("static", "uploads"))
    
    # Читаем youtube ссылки на сервере
    youtube_links = []
    youtube_file_path = os.path.join("static", "uploads", "youtube_links.txt")
    if os.path.exists(youtube_file_path):
        with open(youtube_file_path, "r") as f:
            youtube_links = [line.strip() for line in f.readlines() if line.strip()]

    return render_template("gallery.html", files=files, youtube_links=youtube_links)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

# Добавляем поле youtube_link
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
                # сохраняем ссылку в отдельный файл для галереи
                with open(os.path.join(UPLOAD_FOLDER, "youtube_links.txt"), "a") as f:
                    f.write(youtube_link + "\n")
                flash("YouTube відео додано!")
            else:
                flash("Невірний тип файлу або файл/посилання не вибрано")
            return redirect(url_for("upload"))
        else:
            flash("Невірний логін або пароль")
    return render_template("upload.html")
