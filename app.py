import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from functools import wraps
from pathlib import Path

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB per upload

    # Flask-Mail config (optional — для відправки контактної форми)
    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "")
    app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", "587") or 587)
    app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "true").lower() in ("1","true","yes")
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER", "")
    mail = Mail(app)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    class ContactForm(FlaskForm):
        name = StringField("Ім'я", validators=[DataRequired()])
        email = StringField("Email", validators=[DataRequired(), Email()])
        message = TextAreaField("Повідомлення", validators=[DataRequired()])
        submit = SubmitField("Відправити")

    def allowed_file(filename):
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

    def check_auth(user, pwd):
        return (user == os.environ.get("ADMIN_USER", "admin")
                and pwd == os.environ.get("ADMIN_PASSWORD", "password"))

    def authenticate():
        return abort(401)

    def requires_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password):
                return authenticate()
            return f(*args, **kwargs)
        return decorated

    @app.errorhandler(401)
    def unauthorized(e):
        return ("Unauthorized", 401, {"WWW-Authenticate": 'Basic realm="Login Required"'})

    @app.route("/")
    def index():
        # show latest 12 images
        files = sorted(Path(app.config["UPLOAD_FOLDER"]).glob("*"), reverse=True)
        images = [f.name for f in files if allowed_file(f.name)]
        return render_template("index.html", images=images[:12], name=os.environ.get("PHOTOGRAPHER_NAME", "Любомир Казюк"))

    @app.route("/gallery")
    def gallery():
        files = sorted(Path(app.config["UPLOAD_FOLDER"]).glob("*"), reverse=True)
        images = [f.name for f in files if allowed_file(f.name)]
        return render_template("gallery.html", images=images, name=os.environ.get("PHOTOGRAPHER_NAME", "Любомир Казюк"))

    @app.route("/about")
    def about():
        return render_template("about.html", name=os.environ.get("PHOTOGRAPHER_NAME", "Любомир Казюк"))

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        form = ContactForm()
        if form.validate_on_submit():
            # send email if mail configured
            recipient = os.environ.get("CONTACT_RECIPIENT_EMAIL", os.environ.get("MAIL_DEFAULT_SENDER"))
            subject = f"Повідомлення з сайту від {form.name.data}"
            body = f"Ім'я: {form.name.data}\nEmail: {form.email.data}\n\n{form.message.data}"
            if app.config["MAIL_USERNAME"]:
                try:
                    msg = Message(subject, recipients=[recipient], body=body)
                    mail.send(msg)
                    flash("Повідомлення надіслано. Дякую!", "success")
                except Exception as ex:
                    app.logger.exception("Mail sending failed")
                    flash("Не вдалося відправити повідомлення — спробуйте пізніше.", "danger")
            else:
                # If no mail configured, just log (useful during dev)
                app.logger.info("Contact form message:\n" + body)
                flash("Повідомлення отримано (локально).", "success")
            return redirect(url_for("contact"))
        return render_template("contact.html", form=form)

    @app.route("/admin/upload", methods=["GET", "POST"])
    @requires_auth
    def upload():
        if request.method == "POST":
            if "photo" not in request.files:
                flash("Файл не знайдено в запиті.", "danger")
                return redirect(request.url)
            f = request.files["photo"]
            if f.filename == "":
                flash("Будь ласка, оберіть файл.", "danger")
                return redirect(request.url)
            if f and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                save_path = Path(app.config["UPLOAD_FOLDER"]) / filename
                # if same name exists, append number
                i = 1
                base = save_path.stem
                ext = save_path.suffix
                while save_path.exists():
                    save_path = Path(app.config["UPLOAD_FOLDER"]) / f"{base}-{i}{ext}"
                    i += 1
                f.save(save_path)
                flash("Файл завантажено.", "success")
                return redirect(url_for("gallery"))
            else:
                flash("Недопустимий тип файлу.", "danger")
                return redirect(request.url)
        return render_template("upload.html")

    @app.route("/uploads/<filename>")
    def uploaded_file(filename):
        # direct serving from static/uploads (but route provided)
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=(os.environ.get("FLASK_DEBUG", "0") == "1"))
