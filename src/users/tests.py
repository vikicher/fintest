import pytest
from django.urls import reverse
from rest_framework import status

from users.models import User


pytestmark = pytest.mark.django_db


class TestRegisterView:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.url = reverse("auth-register")

    def test_register_creates_user_and_returns_tokens(self, api_client):
        response = api_client.post(self.url, {
            "email": "user@example.com",
            "password": "strong-password-123",
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["email"] == "user@example.com"
        assert User.objects.filter(email="user@example.com").exists()

    def test_register_duplicate_email_fails(self, api_client, user):
        response = api_client.post(self.url, {
            "email": user.email,
            "password": "another-password-123",
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_register_short_password_fails(self, api_client):
        response = api_client.post(self.url, {
            "email": "user@example.com",
            "password": "short",
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_register_email_is_case_insensitively_unique(self, api_client, user):
        response = api_client.post(self.url, {
            "email": user.email.upper(),
            "password": "another-password-123",
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestLoginView:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.url = reverse("auth-login")
        self.password = "strong-password-123"

    def test_login_with_valid_credentials_returns_tokens(self, api_client, user):
        response = api_client.post(self.url, {
            "email": user.email,
            "password": self.password,
        })

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_with_invalid_password_fails(self, api_client, user):
        response = api_client.post(self.url, {
            "email": user.email,
            "password": "wrong-password",
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_with_unknown_email_fails(self, api_client):
        response = api_client.post(self.url, {
            "email": "unknown@example.com",
            "password": self.password,
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMeView:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.url = reverse("auth-me")

    def test_me_requires_authentication(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_returns_current_user(self, auth_client, user):
        response = auth_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email