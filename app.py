from flask import Flask, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "any-secret-key"

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "mov"}
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
    files = sorted(os.listdir(UPLOAD_FOLDER))
    return render_template("gallery.html", files=files)

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
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                flash(f"Файл {filename} успішно завантажено!")
                return redirect(url_for("upload"))
            else:
                flash("Невірний тип файлу або файл не вибрано")
        else:
            flash("Невірний логін або пароль")
    return render_template("upload.html")
