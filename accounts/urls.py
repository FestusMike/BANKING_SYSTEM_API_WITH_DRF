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
    ForgottenPasswordResetAPIView,
    DeliberatePasswordResetAPIView,
    UserDetailAPIView,
    UserProfileUpdateAPIView,
    UsersListAPIView,
    AdminUserRUDAPIView,
)

urlpatterns = [
    path("user-registration", UserRegistrationAPIView.as_view(), name="user-registration"),
    path("otp-resend", ResendOTPAPIView.as_view(), name="otp-resend"),
    path("otp-verification", OTPVerificationAPIView.as_view(), name="otp-verification"),
    path("password-setup", PasswordSetUpAPIView.as_view(), name="create-password"),
    path("pin-setup", TransactionPinCreateAPIView.as_view(), name="pin-create"),
    path("user-login", LoginAPIView.as_view(), name="login"),
    path("user-logout", UserLogoutAPIView.as_view(), name="logout"),
    path("password-reset-otp",PasswordChangeOTPAPIView.as_view(),name="password-change-otp",),
    path("forgotten-password-reset", ForgottenPasswordResetAPIView.as_view(), name="forgotten-password-reset"),
    path("deliberate-password-reset", DeliberatePasswordResetAPIView.as_view(), name="deliberate-password-reset"),
    path("user-profile", UserDetailAPIView.as_view(), name="profile-view"),
    path("user-profile-edit", UserProfileUpdateAPIView.as_view(), name="profile-edit-view"),
    path("admin/users/<int:id>", AdminUserRUDAPIView.as_view(), name="user-admin-rud"),
    path("admin/users", UsersListAPIView.as_view(), name="users-list"),
]
