import unittest

from app import create_app, db
from app.models.organization import Organization
from app.models.user import User


class TestAuthSession(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        org = Organization(id=1, name="Test Org", code="TST")
        db.session.add(org)
        self.user = User(
            organisation_id=1,
            username="admin1",
            email="admin@test.com",
            role="admin",
        )
        self.user.set_password("Password1!")
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_me_without_session_returns_200(self):
        resp = self.client.get("/api/auth/me")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertFalse(data["authenticated"])
        self.assertIsNone(data["user"])

    def test_refresh_without_session_returns_200(self):
        resp = self.client.post("/api/auth/refresh")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertFalse(data["refreshed"])
        self.assertFalse(data["authenticated"])

    def test_login_returns_tokens_and_me_works_with_header(self):
        login = self.client.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "Password1!"},
        )
        self.assertEqual(login.status_code, 200)
        payload = login.get_json()
        self.assertIn("access_token", payload)
        self.assertIn("refresh_token", payload)

        me = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {payload['access_token']}"},
        )
        self.assertEqual(me.status_code, 200)
        me_data = me.get_json()
        self.assertTrue(me_data["authenticated"])
        self.assertEqual(me_data["email"], "admin@test.com")

    def test_refresh_with_header_returns_new_access_token(self):
        login = self.client.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "Password1!"},
        )
        refresh_token = login.get_json()["refresh_token"]

        refreshed = self.client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        self.assertEqual(refreshed.status_code, 200)
        refresh_data = refreshed.get_json()
        self.assertTrue(refresh_data["refreshed"])
        self.assertIn("access_token", refresh_data)
