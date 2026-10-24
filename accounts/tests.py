
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegistrationTests(APITestCase):
    def setUp(self):
        self.url = "/api/auth/register/"

    def test_register_attendee_successfully(self):
        response = self.client.post(
            self.url,
            {
                "username": "new_attendee",
                "email": "new_attendee@example.com",
                "password": "StrongTestPass!927",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], User.Role.ATTENDEE)
        self.assertTrue(
            User.objects.filter(username="new_attendee").exists()
        )

    def test_register_duplicate_username_fails(self):
        User.objects.create_user(
            username="existing_user",
            email="existing@example.com",
            password="StrongTestPass!927",
        )

        response = self.client.post(
            self.url,
            {
                "username": "existing_user",
                "email": "another@example.com",
                "password": "AnotherStrongPass!927",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    def setUp(self):
        self.url = "/api/auth/login/"
        self.username = "login_test_user"
        self.password = "StrongTestPass!927"

        User.objects.create_user(
            username=self.username,
            email="login_test@example.com",
            password=self.password,
        )

    def test_login_returns_jwt_tokens(self):
        response = self.client.post(
            self.url,
            {
                "username": self.username,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_with_wrong_password_fails(self):
        response = self.client.post(
            self.url,
            {
                "username": self.username,
                "password": "WrongPassword!927",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
