from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from django.core import mail
from django.test import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator

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

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_BASE_URL="http://frontend.test",
    )
    def test_password_reset_request_sends_email_for_existing_user(self):
        response = self.client.post(
            "/api/accounts/password-reset/",
            {
                "email": "existing@example.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Password reset request", mail.outbox[0].subject)
        self.assertIn("http://frontend.test/password-reset-confirm", mail.outbox[0].body)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_BASE_URL="http://frontend.test",
    )
    def test_password_reset_request_with_unknown_email_returns_ok(self):
        response = self.client.post(
            "/api/accounts/password-reset/",
            {
                "email": "unknown@example.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)
        self.assertIn("detail", response.data)

    def test_password_reset_confirm_changes_password(self):
        uid = urlsafe_base64_encode(
            force_bytes(self.user.pk)
        )

        token = default_token_generator.make_token(
            self.user
        )

        response = self.client.post(
            "/api/accounts/password-reset-confirm/",
            {
                "uid": uid,
                "token": token,
                "new_password": "NewStrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertTrue(
            self.user.check_password("NewStrongPassword123!")
        )

    def test_password_reset_confirm_with_invalid_token_fails(self):
        uid = urlsafe_base64_encode(
            force_bytes(self.user.pk)
        )

        response = self.client.post(
            "/api/accounts/password-reset-confirm/",
            {
                "uid": uid,
                "token": "invalid-token",
                "new_password": "NewStrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.user.refresh_from_db()
        self.assertTrue(
            self.user.check_password("StrongPassword123!")
        )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_BASE_URL="http://frontend.test",
    )
    def test_user_registration_sends_verification_email(self):
        response = self.client.post(
            "/api/accounts/register/",
            {
                "username": "john",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Smith",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(
            username="john"
        )

        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Verify your email address", mail.outbox[0].subject)
        self.assertIn("http://frontend.test/verify-email", mail.outbox[0].body)

    def test_user_can_verify_email(self):
        inactive_user = User.objects.create_user(
            username="inactiveuser",
            email="inactiveuser@example.com",
            password="StrongPassword123!",
            is_active=False,
        )

        uid = urlsafe_base64_encode(
            force_bytes(str(inactive_user.pk))
        )

        token = default_token_generator.make_token(
            inactive_user
        )

        response = self.client.post(
            "/api/accounts/verify-email/",
            {
                "uid": uid,
                "token": token,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        inactive_user.refresh_from_db()
        self.assertTrue(inactive_user.is_active)

    def test_email_verification_with_invalid_token_fails(self):
        inactive_user = User.objects.create_user(
            username="inactiveuser",
            email="inactiveuser@example.com",
            password="StrongPassword123!",
            is_active=False,
        )

        uid = urlsafe_base64_encode(
            force_bytes(str(inactive_user.pk))
        )

        response = self.client.post(
            "/api/accounts/verify-email/",
            {
                "uid": uid,
                "token": "invalid-token",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        inactive_user.refresh_from_db()
        self.assertFalse(inactive_user.is_active)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_BASE_URL="http://frontend.test",
    )
    def test_resend_email_verification_sends_email_for_inactive_user(self):
        inactive_user = User.objects.create_user(
            username="inactive_user",
            email="inactive_user@example.com",
            password="StrongPassword123!",
            first_name="inactive",
            last_name="User",
            is_active=False,
        )

        response = self.client.post(
            "/api/accounts/resend-verification/",
            {
                "email": inactive_user.email,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Verify your email address", mail.outbox[0].subject)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_BASE_URL="http://frontend.test",
    )
    def test_resend_email_verification_for_active_user_does_not_send_email(self):
        response = self.client.post(
            "/api/accounts/resend-verification/",
            {
                "email": self.user.email,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

