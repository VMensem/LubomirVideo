from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Список файлов в галерее
images = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Авторизация из env Render
ADMIN_USER = os.environ.get("Admin_login", "admin")
ADMIN_PASS = os.environ.get("Admin_password", "1234")

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route("/")
def index():
    return render_template("index.html", images=images[:12], name=os.environ.get("PHOTOGRAPHER_NAME", "Любомир Казюк"), title="Головна")

@app.route("/about")
def about():
    return render_template("about.html", name=os.environ.get("PHOTOGRAPHER_NAME", "Любомир Казюк"), title="Про мене")

@app.route("/contact")
def contact():
    return render_template("contact.html", name=os.environ.get("PHOTOGRAPHER_NAME", "Любомир Казюк"), title="Контакти")

@app.route("/gallery")
def gallery():
    return render_template("gallery.html", images=images, name=os.environ.get("PHOTOGRAPHER_NAME", "Любомир Казюк"), title="Галерея")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        file = request.files.get("file")

        if username != ADMIN_USER or password != ADMIN_PASS:
            error = "Невірний логін або пароль"
        elif file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            images.append({"url": f"/{file_path.replace(os.sep, '/')}", "name": filename})
            return redirect(url_for('gallery'))
        else:
            error = "Файл не підтримується або не обрано"

    return render_template("upload.html", error=error, name=os.environ.get("PHOTOGRAPHER_NAME", "Любомир Казюк"), title="Завантаження")

if __name__ == "__main__":
    app.run(debug=True)
