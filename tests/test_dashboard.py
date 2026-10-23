"""Checks that the dashboard shows status labels. Uses dates relative to today."""
import os
import tempfile
import unittest
from datetime import date, timedelta

from app import create_app
from db import init_db


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".sqlite")
        self.app = create_app({"TESTING": True, "DATABASE": self.path,
                               "SECRET_KEY": "test-key"})
        with self.app.app_context():
            init_db()
        self.client = self.app.test_client()

    def tearDown(self):
        os.close(self.fd)
        os.unlink(self.path)

    def post(self, url, data):
        self.client.get("/register")
        with self.client.session_transaction() as sess:
            data = dict(data, csrf_token=sess["csrf_token"])
        return self.client.post(url, data=data)

    def add_book(self, title, days_from_today):
        due = (date.today() + timedelta(days=days_from_today)).isoformat()
        self.post("/books/add", {"title": title, "library_name": "Test Library",
                                 "due_date": due})

    def test_dashboard_shows_status_for_each_book(self):
        self.post("/register", {"name": "T", "email": "t@example.com",
                                "password": "password123",
                                "confirm_password": "password123"})
        self.post("/login", {"email": "t@example.com", "password": "password123"})
        self.add_book("Far Away Book", 10)
        self.add_book("Soon Book", 2)
        self.add_book("Today Book", 0)
        self.add_book("Late Book", -2)

        page = self.client.get("/books/").data
        self.assertIn(b"10 days left", page)
        self.assertIn(b"Due in 2 days", page)
        self.assertIn(b"DUE TODAY", page)
        self.assertIn(b"Overdue by 2 days", page)


if __name__ == "__main__":
    unittest.main()
