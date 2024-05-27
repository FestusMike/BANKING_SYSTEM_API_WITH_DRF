from django.urls import path
from .views import (
    UserRegistrationAPIView,
    ResendOTPAPIView,
    OTPVerificationAPIView,
    PasswordSetUpAPIView,
    TransactionPinCreateAPIView,
    LoginAPIView,
    UserLogoutAPIView,
    PasswordChangeOTPAPIView,
    PasswordChangeAPIView,
    UserDetailAPIView,
    UserProfileUpdateAPIView,
    UsersListAPIView,
    AdminUserURDAPIView,
)

urlpatterns = [
    path("register", UserRegistrationAPIView.as_view(), name="user-registration"),
    path("otp-resend", ResendOTPAPIView.as_view(), name="otp-resend"),
    path("verify-otp", OTPVerificationAPIView.as_view(), name="otp-verification"),
    path("password-setup", PasswordSetUpAPIView.as_view(), name="create-password"),
    path("pin/create", TransactionPinCreateAPIView.as_view(), name="pin-create"),
    path("login", LoginAPIView.as_view(), name="login"),
    path("logout", UserLogoutAPIView.as_view(), name="logout"),
    path("otp/password-reset",PasswordChangeOTPAPIView.as_view(),name="password_change_otp",),
    path("password-reset", PasswordChangeAPIView.as_view(), name="password-reset"),
    path("profile", UserDetailAPIView.as_view(), name="profile-view"),
    path("profile/edit", UserProfileUpdateAPIView.as_view(), name="profile-view"),
    path("admin/users/<int:id>", AdminUserURDAPIView.as_view(), name="user-admin-urd"),
    path("admin/users", UsersListAPIView.as_view(), name="users-list"),
]
