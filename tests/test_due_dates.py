"""Tests for the due-date calculations. Run:  python -m unittest discover -s tests -t ."""
import unittest
from datetime import date

from due_dates import days_until_due, get_status, reminder_due_date
from validators import validate_book

TODAY = date(2026, 10, 20)


class DueDateTests(unittest.TestCase):
    def test_days_until_due(self):
        self.assertEqual(days_until_due("2026-10-25", TODAY), 5)
        self.assertEqual(days_until_due("2026-10-20", TODAY), 0)
        self.assertEqual(days_until_due("2026-10-18", TODAY), -2)

    def test_more_than_3_days_is_green(self):
        self.assertEqual(get_status("2026-10-24", TODAY)["color"], "green")   # 4 days
        self.assertEqual(get_status("2026-12-01", TODAY)["color"], "green")

    def test_within_3_days_is_yellow(self):
        for due in ("2026-10-23", "2026-10-22", "2026-10-21"):                # 3, 2, 1 days
            status = get_status(due, TODAY)
            self.assertEqual(status["color"], "yellow")
            self.assertEqual(status["key"], "due_soon")

    def test_due_today_is_flagged(self):
        status = get_status("2026-10-20", TODAY)
        self.assertEqual(status["key"], "due_today")
        self.assertEqual(status["color"], "yellow")
        self.assertEqual(status["label"], "DUE TODAY")

    def test_past_due_is_red(self):
        status = get_status("2026-10-19", TODAY)
        self.assertEqual(status["color"], "red")
        self.assertEqual(status["label"], "Overdue by 1 day")
        self.assertEqual(get_status("2026-10-10", TODAY)["label"], "Overdue by 10 days")

    def test_reminder_dates(self):
        self.assertEqual(reminder_due_date("before_3", TODAY), date(2026, 10, 23))
        self.assertEqual(reminder_due_date("due_today", TODAY), date(2026, 10, 20))
        self.assertEqual(reminder_due_date("overdue_1", TODAY), date(2026, 10, 19))

    def test_due_date_is_saved_in_standard_format(self):
        errors, cleaned = validate_book("Title", "Library", "2026-1-5")
        self.assertEqual(errors, [])
        self.assertEqual(cleaned["due_date"], "2026-01-05")


if __name__ == "__main__":
    unittest.main()
