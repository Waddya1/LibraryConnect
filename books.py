"""Add, edit, list, and mark-returned for the logged-in patron's books.

PRIVACY RULE: every query below includes "patron_id = ?" with the logged-in
patron's id, so a patron can never see or change someone else's records."""
from collections import Counter
from datetime import date

from flask import (Blueprint, abort, flash, g, redirect, render_template,
                   request, url_for)

from auth import login_required
from db import get_db
from due_dates import get_status
from validators import validate_book

bp = Blueprint("books", __name__, url_prefix="/books")


def get_own_book_or_404(book_id):
    book = get_db().execute(
        "SELECT id, title, library_name, due_date, returned "
        "FROM books WHERE id = ? AND patron_id = ?",
        (book_id, g.patron["id"]),
    ).fetchone()
    if book is None:
        abort(404)      # same response whether it doesn't exist or isn't yours
    return book


@bp.route("/")
@login_required
def list_books():
    db = get_db()
    active_rows = db.execute(
        "SELECT id, title, library_name, due_date FROM books "
        "WHERE patron_id = ? AND returned = 0 ORDER BY due_date, title",
        (g.patron["id"],),
    ).fetchall()

    # Add a status (green / yellow / red) to each active book.
    today = date.today()
    active = []
    for row in active_rows:
        book = dict(row)
        book["status"] = get_status(row["due_date"], today)
        active.append(book)
    counts = Counter(book["status"]["key"] for book in active)
    returned = db.execute(
        "SELECT id, title, library_name, due_date, returned_at FROM books "
        "WHERE patron_id = ? AND returned = 1 ORDER BY returned_at DESC",
        (g.patron["id"],),
    ).fetchall()
    return render_template("books/list.html", active=active,
                           returned=returned, counts=counts)


@bp.route("/add", methods=("GET", "POST"))
@login_required
def add():
    form = {}
    if request.method == "POST":
        errors, cleaned = validate_book(
            request.form.get("title", ""),
            request.form.get("library_name", ""),
            request.form.get("due_date", ""),
        )
        if not errors:
            db = get_db()
            db.execute(
                "INSERT INTO books (patron_id, title, library_name, due_date) "
                "VALUES (?, ?, ?, ?)",
                (g.patron["id"], cleaned["title"], cleaned["library_name"],
                 cleaned["due_date"]),
            )
            db.commit()
            flash("Book added.", "success")
            return redirect(url_for("books.list_books"))
        for error in errors:
            flash(error, "error")
        form = cleaned
    return render_template("books/form.html", form=form,
                           heading="Add a borrowed book", submit_label="Add book",
                           action_url=url_for("books.add"))


@bp.route("/<int:book_id>/edit", methods=("GET", "POST"))
@login_required
def edit(book_id):
    book = get_own_book_or_404(book_id)
    form = book
    if request.method == "POST":
        errors, cleaned = validate_book(
            request.form.get("title", ""),
            request.form.get("library_name", ""),
            request.form.get("due_date", ""),
        )
        if not errors:
            db = get_db()
            db.execute(
                "UPDATE books SET title = ?, library_name = ?, due_date = ? "
                "WHERE id = ? AND patron_id = ?",
                (cleaned["title"], cleaned["library_name"], cleaned["due_date"],
                 book_id, g.patron["id"]),
            )
            db.commit()
            flash("Book updated.", "success")
            return redirect(url_for("books.list_books"))
        for error in errors:
            flash(error, "error")
        form = cleaned
    return render_template("books/form.html", form=form,
                           heading="Edit book", submit_label="Save changes",
                           action_url=url_for("books.edit", book_id=book_id))


@bp.route("/<int:book_id>/return", methods=("POST",))
@login_required
def mark_returned(book_id):
    get_own_book_or_404(book_id)
    db = get_db()
    db.execute(
        "UPDATE books SET returned = 1, returned_at = datetime('now') "
        "WHERE id = ? AND patron_id = ?",
        (book_id, g.patron["id"]),
    )
    db.commit()
    flash("Book marked as returned.", "success")
    return redirect(url_for("books.list_books"))
