import json
import os
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from tts_engine import DEFAULT_VOICE, TTSEngine, sanitize_user_id

app = Flask(__name__)
app.secret_key = os.environ.get("TTS_APP_SECRET", "change-me")

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"

VOICE_OPTIONS = [
    ("af_heart", "Heart (American Female)"),
    ("af_bella", "Bella (American Female)"),
    ("am_michael", "Michael (American Male)"),
    ("bf_emily", "Emily (British Female)"),
    ("bm_george", "George (British Male)"),
    ("cf_celine", "Celine (Canadian French)"),
]

THEME_OPTIONS = [
    ("light", "Light"),
    ("dark", "Dark"),
    ("black", "Black"),
]

engine = TTSEngine()


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_users() -> dict:
    ensure_data_dir()
    if not USERS_FILE.exists():
        default_user = {
            "users": {
                "demo@example.com": {
                    "password_hash": generate_password_hash("password"),
                    "display_name": "Demo User",
                }
            }
        }
        USERS_FILE.write_text(json.dumps(default_user, indent=2), encoding="utf-8")

    data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
    return data.get("users", {})


def save_users(users: dict) -> None:
    ensure_data_dir()
    payload = {"users": users}
    USERS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def get_history_file(user_id: str) -> Path:
    ensure_data_dir()
    safe_user = sanitize_user_id(user_id)
    return DATA_DIR / f"{safe_user}_history.json"


def load_history(user_id: str) -> list:
    history_file = get_history_file(user_id)
    if not history_file.exists():
        return []
    return json.loads(history_file.read_text(encoding="utf-8"))


def save_history(user_id: str, history: list) -> None:
    history_file = get_history_file(user_id)
    history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")


def append_history(user_id: str, entry: dict) -> None:
    history = load_history(user_id)
    history.insert(0, entry)
    save_history(user_id, history[:200])


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if "user_email" not in session:
            return redirect(url_for("login"))
        return view(**kwargs)

    return wrapped_view


@app.context_processor
def inject_voice_options():
    return {
        "voice_options": VOICE_OPTIONS,
        "default_voice": DEFAULT_VOICE,
        "theme_options": THEME_OPTIONS,
        "current_theme": session.get("theme", "light"),
    }


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_email" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        display_name = request.form.get("display_name", "").strip() or email

        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template("register.html")

        users = load_users()
        if email in users:
            flash("Account already exists. Please log in.", "error")
            return redirect(url_for("login"))

        users[email] = {
            "password_hash": generate_password_hash(password),
            "display_name": display_name,
        }
        save_users(users)
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_email" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        users = load_users()
        user = users.get(email)

        if user and check_password_hash(user["password_hash"], password):
            session["user_email"] = email
            session["display_name"] = user.get("display_name", email)
            flash("Logged in successfully.", "success")
            return redirect(url_for("index"))

        flash("Invalid credentials.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("login"))


@app.route("/theme", methods=["POST"])
def change_theme():
    selected = request.form.get("theme", "light").lower()
    valid = {value for value, _ in THEME_OPTIONS}
    if selected not in valid:
        selected = "light"
    session["theme"] = selected
    return redirect(request.referrer or url_for("index"))


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    selected_voice = session.get("last_voice", DEFAULT_VOICE)
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        voice = request.form.get("voice") or DEFAULT_VOICE
        selected_voice = voice

        if not text:
            flash("Please enter text to generate audio.", "error")
        else:
            user_email = session["user_email"]
            try:
                output_path = engine.synthesize(
                    text=text,
                    voice=voice,
                    user_id=user_email,
                )
            except Exception as exc:
                flash(f"Failed to generate audio: {exc}", "error")
            else:
                entry = {
                    "text": text,
                    "voice": voice,
                    "filename": output_path.name,
                    "created_at": datetime.utcnow().isoformat(timespec="seconds"),
                }
                append_history(user_email, entry)
                flash("Audio generated successfully.", "success")
                session["last_voice"] = voice
                return redirect(url_for("index"))

    history = load_history(session["user_email"])
    return render_template(
        "index.html",
        history=history,
        display_name=session.get("display_name"),
        selected_voice=selected_voice,
    )


@app.route("/media/<path:filename>")
@login_required
def media(filename: str):
    user_folder = sanitize_user_id(session["user_email"])
    audio_dir = engine.audio_root / user_folder
    requested_path = (audio_dir / filename).resolve()
    try:
        audio_dir_resolved = audio_dir.resolve()
    except FileNotFoundError:
        abort(404)

    if not str(requested_path).startswith(str(audio_dir_resolved)) or not requested_path.exists():
        abort(404)

    as_attachment = bool(request.args.get("download"))
    return send_from_directory(
        audio_dir,
        filename,
        as_attachment=as_attachment,
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
