"""Tests for reminder selection, duplicate prevention, and returned-book exclusion."""
import os
import tempfile
import unittest
from datetime import date

import reminders
from app import create_app
from db import get_db, init_db

TODAY = date(2026, 10, 20)


def quiet(*args):
    """A do-nothing log function so test output stays clean."""


class FakeSender:
    """Pretends to send email and remembers what it was asked to send."""
    def __init__(self, fail=False):
        self.sent = []
        self.fail = fail

    def __call__(self, to_address, subject, body):
        if self.fail:
            raise OSError("pretend the mail server is down")
        self.sent.append((to_address, subject, body))


class ReminderTests(unittest.TestCase):
    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".sqlite")
        self.app = create_app({"TESTING": True, "DATABASE": self.path,
                               "SECRET_KEY": "test-key"})
        self.ctx = self.app.app_context()
        self.ctx.push()
        init_db()
        self.db = get_db()
        self.db.execute("INSERT INTO patrons (name, email, password_hash) "
                        "VALUES ('Test Patron', 'test@example.com', 'x')")
        self.db.commit()

    def tearDown(self):
        self.ctx.pop()
        os.close(self.fd)
        os.unlink(self.path)

    def add_book(self, title, due_date, returned=0):
        cursor = self.db.execute(
            "INSERT INTO books (patron_id, title, library_name, due_date, returned) "
            "VALUES (1, ?, 'Test Library', ?, ?)", (title, due_date, returned))
        self.db.commit()
        return cursor.lastrowid

    def sent_count(self):
        return self.db.execute("SELECT COUNT(*) AS n FROM reminders_sent").fetchone()["n"]

    def run_reminders(self, sender, today=TODAY, dry_run=False):
        return reminders.process_reminders(self.db, today, sender, dry_run, log=quiet)

    # ---- which books get reminders ----
    def test_each_reminder_type_is_found_on_the_right_day(self):
        self.add_book("Three Days", "2026-10-23")
        self.add_book("Today", "2026-10-20")
        self.add_book("Yesterday", "2026-10-19")
        self.add_book("Four Days (no reminder)", "2026-10-24")
        self.add_book("Two Days Late (no reminder)", "2026-10-18")

        found = reminders.find_reminders_due(self.db, TODAY)
        types = {item["title"]: item["reminder_type"] for item in found}
        self.assertEqual(types, {"Three Days": "before_3",
                                 "Today": "due_today",
                                 "Yesterday": "overdue_1"})

    def test_returned_books_are_excluded(self):
        self.add_book("Returned Today", "2026-10-20", returned=1)
        self.add_book("Returned Early", "2026-10-23", returned=1)
        self.add_book("Returned Late", "2026-10-19", returned=1)
        sender = FakeSender()
        summary = self.run_reminders(sender)
        self.assertEqual(summary["found"], 0)
        self.assertEqual(sender.sent, [])

    # ---- duplicate prevention ----
    def test_same_reminder_is_never_sent_twice(self):
        self.add_book("Due Today", "2026-10-20")
        sender = FakeSender()
        first = self.run_reminders(sender)
        second = self.run_reminders(sender)
        self.assertEqual(first["sent"], 1)
        self.assertEqual(second["sent"], 0)
        self.assertEqual(len(sender.sent), 1)
        self.assertEqual(self.sent_count(), 1)

    def test_changed_due_date_allows_new_reminders(self):
        book_id = self.add_book("Renewed Book", "2026-10-20")
        sender = FakeSender()
        self.run_reminders(sender, today=date(2026, 10, 20))
        self.assertEqual(len(sender.sent), 1)

        # Patron renews: new due date.
        self.db.execute("UPDATE books SET due_date = '2026-11-10' WHERE id = ?", (book_id,))
        self.db.commit()

        self.run_reminders(sender, today=date(2026, 11, 7))    # 3 days before new date
        self.run_reminders(sender, today=date(2026, 11, 10))   # due date
        self.assertEqual(len(sender.sent), 3)
        self.assertEqual(self.sent_count(), 3)

    # ---- testing mode and failures ----
    def test_dry_run_sends_and_records_nothing(self):
        self.add_book("Due Today", "2026-10-20")
        sender = FakeSender()
        summary = self.run_reminders(sender, dry_run=True)
        self.assertEqual(summary["previewed"], 1)
        self.assertEqual(sender.sent, [])
        self.assertEqual(self.sent_count(), 0)
        # A real run afterwards still sends it.
        self.assertEqual(self.run_reminders(sender)["sent"], 1)

    def test_failed_send_is_not_recorded_so_it_can_retry(self):
        self.add_book("Due Today", "2026-10-20")
        summary = self.run_reminders(FakeSender(fail=True))
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(self.sent_count(), 0)
        self.assertEqual(self.run_reminders(FakeSender())["sent"], 1)

    # ---- email text ----
    def test_email_contains_required_information(self):
        self.add_book("Dune", "2026-10-20")
        sender = FakeSender()
        self.run_reminders(sender)
        to_address, subject, body = sender.sent[0]
        self.assertEqual(to_address, "test@example.com")
        self.assertIn("Dune", subject)
        for expected in ("Dune", "Test Library", "2026-10-20", "return or renew"):
            self.assertIn(expected, body)

    def test_line_breaks_in_title_cannot_break_the_subject(self):
        self.add_book("Bad\nTitle", "2026-10-20")
        sender = FakeSender()
        self.run_reminders(sender)
        self.assertNotIn("\n", sender.sent[0][1])


if __name__ == "__main__":
    unittest.main()
