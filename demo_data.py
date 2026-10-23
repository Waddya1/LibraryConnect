"""Creates FAKE demo data so you can demonstrate reminders.

  python demo_data.py                       demo account demo@example.com
  python demo_data.py --email you@gmail.com demo account that uses YOUR address,
                                            so real test emails reach you

Safe to run again: it resets only the demo account's books.
Never put real patron information in this app.
"""
import argparse
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

from app import app
from db import get_db
from validators import EMAIL_PATTERN, normalize_email

DEMO_NAME = "Demo Patron"
DEMO_PASSWORD = "DemoPass123!"     # fake password for a throwaway local demo account

# (title, days from today, already returned?)
DEMO_BOOKS = [
    ("Demo: Due in 5 days (green, no reminder)", 5, 0),
    ("Demo: Due in 3 days (3-day reminder)", 3, 0),
    ("Demo: Due today (due-date reminder)", 0, 0),
    ("Demo: Due yesterday (1-day-late reminder)", -1, 0),
    ("Demo: 4 days overdue (red, no reminder)", -4, 0),
    ("Demo: Returned (never gets a reminder)", 0, 1),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", default="demo@example.com")
    args = parser.parse_args()

    email = normalize_email(args.email)
    if not EMAIL_PATTERN.match(email):
        parser.error("please give a valid email address")

    with app.app_context():
        db = get_db()
        patron = db.execute("SELECT id, name FROM patrons WHERE email = ?", (email,)).fetchone()

        if patron is None:
            cursor = db.execute(
                "INSERT INTO patrons (name, email, password_hash) VALUES (?, ?, ?)",
                (DEMO_NAME, email, generate_password_hash(DEMO_PASSWORD)))
            patron_id = cursor.lastrowid
        elif patron["name"] == DEMO_NAME:
            patron_id = patron["id"]
        else:
            print(f"{email} is already a regular account, not a demo account.")
            print("Use a different email so your real test data is not touched.")
            return

        db.execute("DELETE FROM books WHERE patron_id = ?", (patron_id,))
        today = date.today()
        for title, offset, returned in DEMO_BOOKS:
            due = (today + timedelta(days=offset)).isoformat()
            db.execute(
                "INSERT INTO books (patron_id, title, library_name, due_date, returned) "
                "VALUES (?, ?, 'Demo Public Library', ?, ?)",
                (patron_id, title, due, returned))
        db.commit()

    print("Demo data ready.")
    print(f"  Log in at http://127.0.0.1:5000 with {email} / {DEMO_PASSWORD}")
    print("  Preview reminders:  python send_reminders.py --dry-run")
    print("  Send for real:      python send_reminders.py")


if __name__ == "__main__":
    main()
