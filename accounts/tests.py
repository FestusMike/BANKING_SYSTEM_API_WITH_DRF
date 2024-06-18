from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework import status

User = get_user_model()

class TestUserRegistrationAPIView(TestCase):
    def setUp(self):
        self.client = Client()

    def test_user_registration_success(self):
        data = {
            "full_name": "John Doe",
            "email": "johndoe@example.com"
        }
        response = self.client.post('/api/v1/auth/user-registration', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, data['email'])
        self.assertEqual(User.objects.get().full_name, 'John Doe')

    def test_user_registration_failure_email_exists(self):
        User.objects.create_user(email="johndoe@example.com", full_name="John Doe")
        data = {
            "full_name": "Jane Doe",
            "email": "johndoe@example.com"
        }
        response = self.client.post('/api/v1/auth/user-registration', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_user_registration_failure_invalid_data(self):
        data = {
            "full_name": "",
            "email": ""
        }
        response = self.client.post('/api/v1/auth/user-registration', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

class TestOTPVerificationAPIView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email="test@example.com", otp="1234")

    def test_otp_verification_success(self):
        data = {"otp": "1234"}
        response = self.client.post("/api/v1/auth/otp-verification", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.asserEqual(len(response.data["otp"]), 4)
        self.assertEqual(response.data["status"], status.HTTP_200_OK)
        self.assertEqual(response.data["Success"], True)
        self.assertEqual(response.data["message"], "OTP verification successful.")

    def test_otp_verification_failure_invalid_otp(self):
        data = {"otp": "6543"}
        response = self.client.post("/api/v1/auth/otp-verification", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["status"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["Success"], False)
        self.assertEqual(response.data["message"], "Invalid OTP")

    def test_otp_verification_failure_expired_otp(self):
        self.user.date_updated = timezone.now() - timedelta(minutes=15)
        self.user.save()
        data = {"otp": "1234"}
        response = self.client.post("/api/v1/auth/otp-verification", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["Success"], False)
        self.assertEqual(response.data["message"], "OTP has expired. Kindly request another.")

    def test_otp_verification_failure_missing_otp(self):
        data = {}
        response = self.client.post("/api/v1/auth/otp-verification", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["Success"], False)
        self.assertEqual(response.data["message"], "OTP is required")

class TestPasswordSetUpAPIView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email="test@example.com", otp="1234")

    def test_password_setup_success(self):
        data = {"otp": "1234", "password1": "password123", "password2": "password123"}
        response = self.client.post("/api/v1/auth/password-setup", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["Success"], True)
        self.assertEqual(response.data["message"], "Password set successfully and account creation complete. A token of 20,000.00 naira has been credited to your account as a welcome bonus.")

    def test_password_setup_failure_invalid_otp(self):
        data = {"otp": "6543", "password1": "password123", "password2": "password123"}
        response = self.client.post("/api/v1/auth/password-setup", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["status"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["Success"], False)
        self.assertEqual(response.data["message"], "Invalid OTP")

    def test_password_setup_failure_expired_otp(self):
        self.user.date_updated = timezone.now() - timedelta(minutes=15)
        self.user.save()
        data = {"otp": "1234", "password1": "password123", "password2": "password123"}
        response = self.client.post("/api/v1/auth/password-setup", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["Success"], False)
        self.assertEqual(response.data["message"], "OTP has expired. Kindly request another.")

    def test_password_setup_failure_password_mismatch(self):
        data = {"otp": "1234", "password1": "password123", "password2": "password456"}
        response = self.client.post("/api/v1/auth/password-setup", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

