from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

media = []  # Список фото/видео (локальных и YouTube)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASSWORD", "Lubomirk2025")

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route("/")
def index():
    return render_template("index.html", media=media[:12], name=os.environ.get("PHOTOGRAPHER_NAME", "Любомир Казюк"), title="Головна")

@app.route("/about")
def about():
    return render_template("about.html", name=os.environ.get("PHOTOGRAPHER_NAME", "Любомир Казюк"), title="Про мене")

@app.route("/contact")
def contact():
    return render_template("contact.html", name=os.environ.get("PHOTOGRAPHER_NAME", "Любомир Казюк"), title="Контакти")

@app.route("/gallery")
def gallery():
    return render_template("gallery.html", media=media, name=os.environ.get("PHOTOGRAPHER_NAME", "Любомир Казюк"), title="Галерея")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        file = request.files.get("file")
        youtube = request.form.get("youtube")  # Новое поле для YouTube

        if username != ADMIN_USER or password != ADMIN_PASSWORD:
            error = "Невірний логін або пароль"
        elif file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            media.append({"type": "file", "url": f"/{file_path.replace(os.sep, '/')}", "name": filename})
            return redirect(url_for('gallery'))
        elif youtube:
            # Конвертируем ссылку в embed URL
            if "youtube.com/watch?v=" in youtube:
                video_id = youtube.split("watch?v=")[-1].split("&")[0]
                embed_url = f"https://www.youtube.com/embed/{video_id}"
                media.append({"type": "youtube", "url": embed_url})
                return redirect(url_for('gallery'))
            else:
                error = "Невірна YouTube ссылка"
        else:
            error = "Файл або YouTube ссылка не вибрано"

    return render_template("upload.html", error=error, name=os.environ.get("PHOTOGRAPHER_NAME", "Любомир Казюк"), title="Завантаження")

if __name__ == "__main__":
    app.run(debug=True)
