"""Authentication routes — login, register, logout."""
from functools import wraps
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, session, g,
)
from .models import db, User

auth = Blueprint("auth", __name__, url_prefix="/auth")


# ---------------------------------------------------------------------------
# Middleware — load current user on every request
# ---------------------------------------------------------------------------

def load_user():
    """Call this from before_request to populate g.user."""
    user_id = session.get("user_id")
    if user_id:
        g.user = db.session.get(User, user_id)
    else:
        g.user = None


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------

def login_required(f):
    """Redirect to login if not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.user is None:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Redirect to login if not an admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.user is None:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        if not g.user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@auth.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter(
            db.or_(User.username == username, User.email == username)
        ).first()

        if user and user.check_password(password) and user.is_active:
            session["user_id"] = user.id
            flash(f"Welcome back, {user.full_name or user.username}!", "success")
            next_url = request.args.get("next") or request.form.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            if user.is_admin:
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("main.index"))

        flash("Invalid username or password.", "danger")

    return render_template("auth/login.html")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        errors = []
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if not email:
            errors.append("Email is required.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(username=username).first():
            errors.append("Username already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("auth/register.html")

        user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            address=address,
            role="customer",
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        flash("Account created! Welcome to Winaris Glass.", "success")
        return redirect(url_for("main.index"))

    return render_template("auth/register.html")


@auth.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    session.pop("cart", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@auth.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        g.user.full_name = request.form.get("full_name", "").strip()
        g.user.email = request.form.get("email", "").strip()
        g.user.phone = request.form.get("phone", "").strip()
        g.user.address = request.form.get("address", "").strip()

        new_pw = request.form.get("new_password", "")
        if new_pw:
            if len(new_pw) < 6:
                flash("Password must be at least 6 characters.", "danger")
                return redirect(url_for("auth.profile"))
            g.user.set_password(new_pw)

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html")
