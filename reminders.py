"""Reminder logic: find reminders to send today, build the email text,
send them (or preview them), and record what was sent.

This file never talks to an email server itself. The code that actually
sends mail is passed in as 'send_function', which keeps this file easy to test."""
from due_dates import REMINDER_RULES, reminder_due_date

INTRO_LINES = {
    "before_3": "This item is due in 3 days.",
    "due_today": "This item is due today.",
    "overdue_1": "This item was due yesterday and is now overdue.",
}
SUBJECT_ENDINGS = {
    "before_3": "is due in 3 days",
    "due_today": "is due today",
    "overdue_1": "is now overdue",
}


def find_reminders_due(db, today):
    """Books that need a reminder today. Skips returned books and any
    reminder that was already sent for the book's current due date."""
    found = []
    for reminder_type in REMINDER_RULES:
        target_due_date = reminder_due_date(reminder_type, today).isoformat()
        rows = db.execute(
            "SELECT b.id AS book_id, b.title, b.library_name, b.due_date, "
            "       p.name AS patron_name, p.email "
            "FROM books b JOIN patrons p ON p.id = b.patron_id "
            "WHERE b.returned = 0 AND b.due_date = ? "
            "AND NOT EXISTS ("
            "    SELECT 1 FROM reminders_sent r "
            "    WHERE r.book_id = b.id AND r.reminder_type = ? "
            "    AND r.due_date = b.due_date) "
            "ORDER BY p.email, b.title",
            (target_due_date, reminder_type),
        ).fetchall()
        for row in rows:
            reminder = dict(row)
            reminder["reminder_type"] = reminder_type
            found.append(reminder)
    return found


def build_email(reminder):
    """Returns (subject, body) as plain text."""
    # Collapse any line breaks so a title can never break the email header.
    short_title = " ".join(reminder["title"].split())[:80]
    kind = reminder["reminder_type"]

    subject = f'LibraryConnect reminder: "{short_title}" {SUBJECT_ENDINGS[kind]}'
    body = "\n".join([
        f"Hello {reminder['patron_name']},",
        "",
        INTRO_LINES[kind],
        "",
        f"  Title:    {reminder['title']}",
        f"  Library:  {reminder['library_name']}",
        f"  Due date: {reminder['due_date']}",
        "",
        "Please return or renew this item.",
        "",
        "-- LibraryConnect (automated reminder)",
    ])
    return subject, body


def mark_sent(db, book_id, reminder_type, due_date):
    db.execute(
        "INSERT OR IGNORE INTO reminders_sent (book_id, reminder_type, due_date) "
        "VALUES (?, ?, ?)",
        (book_id, reminder_type, due_date),
    )
    db.commit()


def process_reminders(db, today, send_function=None, dry_run=False, log=print):
    """Send (or preview) every reminder due today. Returns a summary dict.

    dry_run=True  -> prints previews; sends nothing; records nothing.
    send_function -> a function(to_address, subject, body) that sends one email.
    """
    summary = {"found": 0, "sent": 0, "previewed": 0, "failed": 0}
    reminders = find_reminders_due(db, today)
    summary["found"] = len(reminders)

    for reminder in reminders:
        subject, body = build_email(reminder)

        if not dry_run and reminder["email"].lower().endswith("@example.com"):
            log(f"SKIPPED demo address: {reminder['email']}")
            continue

        if dry_run:
            log(f"--- DRY RUN (not sent, not recorded) [{reminder['reminder_type']}] ---")
            log(f"To: {reminder['email']}")
            log(f"Subject: {subject}")
            log(body)
            log("")
            summary["previewed"] += 1
            continue

        try:
            send_function(reminder["email"], subject, body)
        except Exception as error:   # one failed email must not stop the others
            log(f"FAILED to send to {reminder['email']} "
                f"({reminder['reminder_type']}): {error}")
            summary["failed"] += 1
            continue

        mark_sent(db, reminder["book_id"], reminder["reminder_type"], reminder["due_date"])
        log(f"Sent {reminder['reminder_type']} reminder to {reminder['email']}: "
            f"{reminder['title']}")
        summary["sent"] += 1

    return summary
