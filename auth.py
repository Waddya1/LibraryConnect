"""Registration, login, logout, and the login_required decorator."""
import functools
import sqlite3

from flask import (Blueprint, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db
from validators import normalize_email, validate_registration

bp = Blueprint("auth", __name__)

# Used so a login for an unknown email takes about as long as a real one.
DUMMY_HASH = generate_password_hash("not-a-real-password")


@bp.before_app_request
def load_logged_in_patron():
    """Runs before every request: sets g.patron (or None)."""
    patron_id = session.get("patron_id")
    if patron_id is None:
        g.patron = None
    else:
        g.patron = get_db().execute(
            "SELECT id, name, email FROM patrons WHERE id = ?", (patron_id,)
        ).fetchone()
        if g.patron is None:       # account no longer exists
            session.clear()


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.patron is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped_view


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = normalize_email(request.form.get("email", ""))
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        errors = validate_registration(name, email, password, confirm)
        if not errors:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO patrons (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, generate_password_hash(password)),
                )
                db.commit()
            except sqlite3.IntegrityError:
                errors.append("That email is already registered.")
            else:
                flash("Account created. Please log in.", "success")
                return redirect(url_for("auth.login"))
        for error in errors:
            flash(error, "error")
        return render_template("register.html", name=name, email=email)

    return render_template("register.html", name="", email="")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        email = normalize_email(request.form.get("email", ""))
        password = request.form.get("password", "")

        patron = get_db().execute(
            "SELECT id, password_hash FROM patrons WHERE email = ?", (email,)
        ).fetchone()

        hash_to_check = patron["password_hash"] if patron else DUMMY_HASH
        password_ok = check_password_hash(hash_to_check, password)

        if patron is not None and password_ok:
            session.clear()                 # new session on login
            session["patron_id"] = patron["id"]
            session.permanent = True        # uses PERMANENT_SESSION_LIFETIME
            return redirect(url_for("books.list_books"))

        flash("Invalid email or password.", "error")   # same message either way
        return render_template("login.html", email=email)

    return render_template("login.html", email="")


@bp.route("/logout", methods=("POST",))
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
