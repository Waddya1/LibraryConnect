"""Input validation. Each function returns a list of error messages
(an empty list means the input is valid)."""
import re
from datetime import date, datetime

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(email):
    return email.strip().lower()


def validate_registration(name, email, password, confirm_password):
    errors = []
    if not name or len(name) > 100:
        errors.append("Name is required (100 characters maximum).")
    if len(email) > 254 or not EMAIL_PATTERN.match(email):
        errors.append("Please enter a valid email address.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    elif len(password) > 128:
        errors.append("Password must be 128 characters or fewer.")
    if password != confirm_password:
        errors.append("Passwords do not match.")
    return errors


def validate_book(title, library_name, due_date_text):
    """Returns (errors, cleaned_values)."""
    errors = []
    title = title.strip()
    library_name = library_name.strip()
    due_date_text = due_date_text.strip()

    if not title or len(title) > 200:
        errors.append("Title is required (200 characters maximum).")
    if not library_name or len(library_name) > 100:
        errors.append("Library name is required (100 characters maximum).")

    cleaned_due_date = due_date_text
    try:
        due = datetime.strptime(due_date_text, "%Y-%m-%d").date()
        if not (date(2000, 1, 1) <= due <= date(2100, 12, 31)):
            errors.append("Due date must be between 2000 and 2100.")
        else:
            cleaned_due_date = due.isoformat()   # always saved as YYYY-MM-DD
    except ValueError:
        errors.append("Due date must be a valid date (YYYY-MM-DD).")

    cleaned = {"title": title, "library_name": library_name, "due_date": cleaned_due_date}
    return errors, cleaned
