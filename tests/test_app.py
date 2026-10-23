"""Run from the project folder:  python -m unittest discover -s tests -t ."""
import os
import tempfile
import unittest

from app import create_app
from db import get_db, init_db


class LibraryConnectTests(unittest.TestCase):
    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".sqlite")
        self.app = create_app({"TESTING": True, "DATABASE": self.path,
                               "SECRET_KEY": "test-key"})
        with self.app.app_context():
            init_db()

    def tearDown(self):
        os.close(self.fd)
        os.unlink(self.path)

    # ---- helpers ----
    def post(self, client, url, data=None):
        client.get("/register")                      # makes a CSRF token
        with client.session_transaction() as sess:
            token = sess["csrf_token"]
        payload = dict(data or {})
        payload["csrf_token"] = token
        return client.post(url, data=payload)

    def register_and_login(self, client, email, password="password123"):
        self.post(client, "/register", {"name": "Test Patron", "email": email,
                                        "password": password,
                                        "confirm_password": password})
        return self.post(client, "/login", {"email": email, "password": password})

    def add_book(self, client, title="Test Book"):
        return self.post(client, "/books/add", {"title": title,
                                                "library_name": "Test Library",
                                                "due_date": "2026-11-01"})

    # ---- tests ----
    def test_password_is_hashed(self):
        client = self.app.test_client()
        self.register_and_login(client, "a@example.com", "password123")
        with self.app.app_context():
            row = get_db().execute("SELECT password_hash FROM patrons").fetchone()
        self.assertNotEqual(row["password_hash"], "password123")

    def test_post_without_csrf_token_is_rejected(self):
        client = self.app.test_client()
        self.assertEqual(client.post("/login", data={}).status_code, 400)

    def test_books_page_requires_login(self):
        client = self.app.test_client()
        response = client.get("/books/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_wrong_password_is_rejected(self):
        client = self.app.test_client()
        self.register_and_login(client, "a@example.com")
        client.get("/books/")
        other = self.app.test_client()
        self.post(other, "/login", {"email": "a@example.com", "password": "wrongpass1"})
        self.assertEqual(other.get("/books/").status_code, 302)

    def test_invalid_due_date_is_rejected(self):
        client = self.app.test_client()
        self.register_and_login(client, "a@example.com")
        self.post(client, "/books/add", {"title": "X", "library_name": "Y",
                                         "due_date": "not-a-date"})
        with self.app.app_context():
            count = get_db().execute("SELECT COUNT(*) AS n FROM books").fetchone()["n"]
        self.assertEqual(count, 0)

    def test_patrons_cannot_access_each_others_books(self):
        alice = self.app.test_client()
        bob = self.app.test_client()
        self.register_and_login(alice, "alice@example.com")
        self.register_and_login(bob, "bob@example.com")
        self.add_book(alice, "Alice Secret Book")

        self.assertNotIn(b"Alice Secret Book", bob.get("/books/").data)
        self.assertEqual(bob.get("/books/1/edit").status_code, 404)
        self.assertEqual(self.post(bob, "/books/1/edit",
                                   {"title": "Hacked", "library_name": "X",
                                    "due_date": "2026-12-01"}).status_code, 404)
        self.assertEqual(self.post(bob, "/books/1/return").status_code, 404)
        self.assertIn(b"Alice Secret Book", alice.get("/books/").data)

    def test_mark_returned_moves_book(self):
        client = self.app.test_client()
        self.register_and_login(client, "a@example.com")
        self.add_book(client)
        self.post(client, "/books/1/return")
        with self.app.app_context():
            row = get_db().execute("SELECT returned FROM books WHERE id = 1").fetchone()
        self.assertEqual(row["returned"], 1)


if __name__ == "__main__":
    unittest.main()
