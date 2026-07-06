from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class AccountsAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="existing_user",
            email="existing@example.com",
            password="StrongPassword123!",
            first_name="Existing",
            last_name="User",
        )

    def test_user_can_register(self):
        payload = {
            "username": "john",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Smith",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
        }

        response = self.client.post("/api/accounts/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.all().count(), 2)
        self.assertEqual(response.data["username"], "john")
        self.assertEqual(response.data["first_name"], "John")
        self.assertEqual(response.data["last_name"], "Smith")
        self.assertNotIn("password", response.data)
        self.assertNotIn("password_confirm", response.data)

    def test_user_cannot_register_with_existing_email(self):
        payload = {
            "username": "john",
            "email": "existing@example.com",
            "first_name": "John",
            "last_name": "Smith",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
        }

        response = self.client.post("/api/accounts/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(User.objects.all().count(), 1)

    def test_user_cannot_register_with_password_mismatch(self):
        payload = {
            "username": "john",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Smith",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword1!",
        }

        response = self.client.post("/api/accounts/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.all().count(), 1)

    def test_unauthenticated_user_cannot_access_me_endpoint(self):
        response = self.client.get("/api/accounts/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_access_me_endpoint(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/accounts/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "existing_user")
        self.assertEqual(response.data["email"], "existing@example.com")
        self.assertEqual(response.data["first_name"], "Existing")
        self.assertEqual(response.data["last_name"], "User")

    def test_authenticated_user_can_update_own_profile(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "first_name": "Updated",
            "last_name": "Name",
        }
        response = self.client.patch("/api/accounts/me/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()

        self.assertEqual(response.data["first_name"], "Updated")
        self.assertEqual(response.data["last_name"], "Name")

    def test_authenticated_user_cannot_update_email_to_existing_email(self):
        another_user = User.objects.create_user(
            username="another_user",
            email="another@example.com",
            password="StrongPassword123!",
        )

        self.client.force_authenticate(user=another_user)

        payload = {
            "first_name": "Updated",
            "last_name": "Name",
            "email" : "existing@example.com",
        }

        response = self.client.patch("/api/accounts/me/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "existing@example.com")
