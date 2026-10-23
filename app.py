import hmac
import os
import sqlite3
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.security import check_password_hash, generate_password_hash
from flask_wtf.csrf import CSRFProtect

from forms import (
    AdminLoginForm,
    ApplicationForm,
    LoginForm,
    RegistrationForm,
    StatusForm,
)


login_manager = LoginManager()
csrf = CSRFProtect()


class User(UserMixin):
    def __init__(self, user_id, email, full_name):
        self.id = str(user_id)
        self.email = email
        self.full_name = full_name


def get_db():
    if "db" not in g:
        database_path = current_app.config["DATABASE_PATH"]
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(database_path, timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA busy_timeout = 10000")
    return g.db


def close_db(_error=None):
    database = g.pop("db", None)
    if database is not None:
        database.close()


def init_db():
    schema_path = Path(__file__).with_name("schema.sql")
    get_db().executescript(schema_path.read_text(encoding="utf-8"))


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    return wrapped_view


def create_app(test_config=None):
    overrides = test_config or {}
    secret_key = overrides.get("SECRET_KEY") or os.environ.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError(
            "SECRET_KEY must be set in the environment before starting the application."
        )

    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=secret_key,
        DATABASE_PATH=os.environ.get(
            "DATABASE_PATH", str(Path(app.instance_path) / "applications.sqlite3")
        ),
        ADMIN_USERNAME=os.environ.get("ADMIN_USERNAME"),
        ADMIN_PASSWORD_HASH=os.environ.get("ADMIN_PASSWORD_HASH"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("APP_ENV") == "production",
        MAX_CONTENT_LENGTH=1024 * 1024,
    )
    app.config.update(overrides)

    login_manager.init_app(app)
    login_manager.login_view = "login"
    csrf.init_app(app)
    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        form = RegistrationForm()
        if form.validate_on_submit():
            email = form.email.data.strip().lower()
            try:
                database = get_db()
                cursor = database.execute(
                    "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
                    (
                        form.full_name.data.strip(),
                        email,
                        generate_password_hash(form.password.data),
                    ),
                )
                database.commit()
            except sqlite3.IntegrityError:
                form.email.errors.append(
                    "We could not create an account with those details. Check the email or sign in."
                )
            else:
                session.clear()
                login_user(User(cursor.lastrowid, email, form.full_name.data.strip()))
                flash("Your account has been created.", "success")
                return redirect(url_for("dashboard"))
        return render_template("register.html", form=form)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        form = LoginForm()
        if form.validate_on_submit():
            email = form.email.data.strip().lower()
            user_row = get_db().execute(
                "SELECT id, email, full_name, password_hash FROM users WHERE email = ?",
                (email,),
            ).fetchone()
            if user_row and check_password_hash(
                user_row["password_hash"], form.password.data
            ):
                session.clear()
                login_user(User(user_row["id"], user_row["email"], user_row["full_name"]))
                return redirect(url_for("dashboard"))
            flash("Email or password is incorrect.", "error")
        return render_template("login.html", form=form)

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        session.clear()
        flash("You have been signed out.", "success")
        return redirect(url_for("home"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        applications = get_db().execute(
            "SELECT * FROM applications WHERE user_id = ? ORDER BY created_at DESC, id DESC",
            (current_user.id,),
        ).fetchall()
        return render_template(
            "dashboard.html",
            applications=applications,
            statuses=StatusForm.STATUSES,
            status_form=StatusForm(),
        )

    @app.route("/apply", methods=["GET", "POST"])
    @login_required
    def apply():
        form = ApplicationForm()
        if form.validate_on_submit():
            database = get_db()
            database.execute(
                """
                INSERT INTO applications (
                    user_id, student_name, registration_number, department,
                    semester, examination_year, college_name, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    current_user.id,
                    form.student_name.data.strip(),
                    form.registration_number.data.strip(),
                    form.department.data.strip(),
                    form.semester.data,
                    form.examination_year.data,
                    form.college_name.data.strip(),
                    form.reason.data.strip(),
                ),
            )
            database.commit()
            flash("Your application record has been saved to your tracker.", "success")
            return redirect(url_for("dashboard"))
        return render_template("apply.html", form=form)

    @app.route("/applications/<int:application_id>/status", methods=["POST"])
    @login_required
    def update_status(application_id):
        form = StatusForm()
        if not form.validate_on_submit():
            flash("Choose a valid application status.", "error")
            return redirect(url_for("dashboard"))

        database = get_db()
        cursor = database.execute(
            "UPDATE applications SET status = ? WHERE id = ? AND user_id = ?",
            (form.status.data, application_id, current_user.id),
        )
        database.commit()
        if cursor.rowcount != 1:
            abort(404)
        flash("Your tracker status has been updated.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/documents")
    def documents():
        return render_template("documents.html")

    @app.route("/letter")
    def letter():
        return render_template("letter.html")

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if not app.config["ADMIN_USERNAME"] or not app.config["ADMIN_PASSWORD_HASH"]:
            abort(503, description="Admin login has not been configured.")

        form = AdminLoginForm()
        if form.validate_on_submit():
            username_matches = hmac.compare_digest(
                form.username.data.strip().encode("utf-8"),
                app.config["ADMIN_USERNAME"].encode("utf-8"),
            )
            password_matches = check_password_hash(
                app.config["ADMIN_PASSWORD_HASH"], form.password.data
            )
            if username_matches and password_matches:
                logout_user()
                session.clear()
                session["is_admin"] = True
                flash("Admin sign-in successful.", "success")
                return redirect(url_for("admin_dashboard"))
            flash("Admin username or password is incorrect.", "error")
        return render_template("admin_login.html", form=form)

    @app.route("/admin/logout", methods=["POST"])
    @admin_required
    def admin_logout():
        session.clear()
        flash("Admin signed out.", "success")
        return redirect(url_for("home"))

    @app.route("/admin/applications")
    @admin_required
    def admin_dashboard():
        applications = get_db().execute(
            """
            SELECT applications.*, users.email AS account_email
            FROM applications JOIN users ON users.id = applications.user_id
            ORDER BY applications.created_at DESC, applications.id DESC
            """
        ).fetchall()
        return render_template("admin_dashboard.html", applications=applications)

    @app.errorhandler(413)
    def request_too_large(_error):
        return "Request is too large.", 413

    return app


@login_manager.user_loader
def load_user(user_id):
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return None
    row = get_db().execute(
        "SELECT id, email, full_name FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if row is None:
        return None
    return User(row["id"], row["email"], row["full_name"])


app = create_app()


if __name__ == "__main__":
    debug = (
        os.environ.get("APP_ENV") != "production"
        and os.environ.get("FLASK_DEBUG") == "1"
    )
    app.run(debug=debug)
