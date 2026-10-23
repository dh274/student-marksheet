import os
import sqlite3
import tempfile
import unittest
from contextlib import closing

from werkzeug.security import generate_password_hash

os.environ.setdefault("SECRET_KEY", "test-only-import-secret")

from app import create_app


class PortalTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(
            self.temporary_directory.name, "portal-test.sqlite3"
        )
        self.app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SECRET_KEY": "test-only-secret",
                "DATABASE_PATH": self.database_path,
                "ADMIN_USERNAME": "portal-admin",
                "ADMIN_PASSWORD_HASH": generate_password_hash("test-admin-password"),
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def create_student(self, client, name, email):
        return client.post(
            "/register",
            data={
                "full_name": name,
                "email": email,
                "password": "student-test-password-123",
                "confirm_password": "student-test-password-123",
            },
            follow_redirects=True,
        )

    def test_public_pages_and_private_routes(self):
        for path in ("/", "/register", "/login", "/documents", "/letter"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
        self.assertEqual(self.client.get("/apply").status_code, 302)
        self.assertEqual(self.client.get("/dashboard").status_code, 302)
        self.assertEqual(self.client.get("/admin/applications").status_code, 302)
        self.assertEqual(self.client.get("/admin/login").status_code, 200)

    def test_application_is_saved_and_owned_by_student(self):
        self.create_student(self.client, "Student One", "one@example.com")
        response = self.client.post(
            "/apply",
            data={
                "student_name": "Student One",
                "registration_number": "AU/12345",
                "department": "Computer Science",
                "semester": "2",
                "examination_year": "2024",
                "college_name": "Example College",
                "reason": "The original marksheet was lost.",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AU/12345", response.data)
        self.assertIn(b"Not Started", response.data)

        with closing(sqlite3.connect(self.database_path)) as database:
            saved_application = database.execute(
                "SELECT user_id, registration_number, status FROM applications"
            ).fetchone()
            password_hash = database.execute(
                "SELECT password_hash FROM users WHERE email = ?",
                ("one@example.com",),
            ).fetchone()[0]
        self.assertEqual(saved_application[1:], ("AU/12345", "Not Started"))
        self.assertNotEqual(password_hash, "student-test-password-123")
        self.assertTrue(password_hash.startswith("scrypt:"))

        response = self.client.post(
            "/applications/1/status",
            data={"status": "Documents Prepared"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Documents Prepared", response.data)

        other_client = self.app.test_client()
        self.create_student(other_client, "Student Two", "two@example.com")
        other_dashboard = other_client.get("/dashboard")
        self.assertNotIn(b"AU/12345", other_dashboard.data)
        response = other_client.post(
            "/applications/1/status", data={"status": "Submitted"}
        )
        self.assertEqual(response.status_code, 404)

        with closing(sqlite3.connect(self.database_path)) as database:
            status = database.execute(
                "SELECT status FROM applications WHERE id = 1"
            ).fetchone()[0]
        self.assertEqual(status, "Documents Prepared")

    def test_admin_authentication_is_required_for_records(self):
        response = self.client.get("/admin/applications")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login", response.location)

        self.client.post(
            "/admin/login",
            data={"username": "portal-admin", "password": "test-admin-password"},
        )
        self.assertEqual(self.client.get("/admin/applications").status_code, 200)

    def test_csrf_rejects_post_without_token(self):
        csrf_app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "csrf-test-secret",
                "DATABASE_PATH": os.path.join(
                    self.temporary_directory.name, "csrf-test.sqlite3"
                ),
            }
        )
        response = csrf_app.test_client().post("/register", data={})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
