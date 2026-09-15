from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


class RegistrationTests(APITestCase):
    def test_register_creator_ok(self):
        resp = self.client.post(
            reverse("register"),
            {"username": "alice", "email": "alice@example.com", "password": "StrongPass123", "role": "creator"},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="alice").exists())
        self.assertEqual(User.objects.get(username="alice").role, "creator")

    def test_register_reviewer_ok(self):
        resp = self.client.post(
            reverse("register"),
            {"username": "bob", "email": "bob@example.com", "password": "StrongPass123", "role": "reviewer"},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_register_duplicate_username_rejected(self):
        User.objects.create_user(username="alice", email="a@example.com", password="StrongPass123", role="creator")
        resp = self.client.post(
            reverse("register"),
            {"username": "alice", "email": "other@example.com", "password": "StrongPass123", "role": "creator"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_admin_role_rejected(self):
        resp = self.client.post(
            reverse("register"),
            {"username": "eve", "email": "eve@example.com", "password": "StrongPass123", "role": "admin"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields_rejected(self):
        resp = self.client.post(reverse("register"), {"username": "carl"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_hashed_not_plaintext(self):
        self.client.post(
            reverse("register"),
            {"username": "dana", "email": "dana@example.com", "password": "StrongPass123", "role": "creator"},
        )
        user = User.objects.get(username="dana")
        self.assertNotEqual(user.password, "StrongPass123")


class LoginLogoutTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="StrongPass123", role="creator"
        )

    def test_login_ok(self):
        resp = self.client.post(reverse("login"), {"username": "alice", "password": "StrongPass123"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_login_bad_credentials(self):
        resp = self.client.post(reverse("login"), {"username": "alice", "password": "wrong"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_blacklists_refresh_token(self):
        login = self.client.post(reverse("login"), {"username": "alice", "password": "StrongPass123"})
        access, refresh = login.data["access"], login.data["refresh"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        resp = self.client.post(reverse("logout"), {"refresh": refresh})
        self.assertEqual(resp.status_code, status.HTTP_205_RESET_CONTENT)

        refresh_resp = self.client.post(reverse("token_refresh"), {"refresh": refresh})
        self.assertEqual(refresh_resp.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="StrongPass123", role="creator"
        )

    def test_profile_requires_auth(self):
        resp = self.client.get(reverse("profile"))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_invalid_token_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer garbage-token")
        resp = self.client.get(reverse("profile"))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_returns_own_data(self):
        login = self.client.post(reverse("login"), {"username": "alice", "password": "StrongPass123"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        resp = self.client.get(reverse("profile"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["username"], "alice")
