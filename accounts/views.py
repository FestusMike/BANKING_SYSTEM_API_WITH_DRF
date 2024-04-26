from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import status, generics
from .utils import GenerateOTP
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import IsOwnerOrAdmin
from .serializers import (
    UserRegistrationSerializer,
    OTPVerificationSerializer,
    NewOTPRequestSerializer,
    TransactionPinSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordSerializer,
    PasswordChangeAuthenticatedSerializer,
    UserProfileUpdateSerializer
)
import re

# Create your views here.

User = get_user_model()


class UserRegistrationAPIView(generics.GenericAPIView):
    """
    This View registers a new user based on their e-mail, first_name, and last_name.
    When a user registers, their data is first saved in the database, and an OTP is sent
    to verify their entered e-mail address.
    """

    serializer_class = UserRegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        if User.objects.filter(email=email).exists():
            return Response(
                {
                    "status": status.HTTP_406_NOT_ACCEPTABLE,
                    "Success": False,
                    "message": "User with this email already exists",
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        otp = GenerateOTP(length=4)
        full_name = serializer.validated_data["full_name"]
        full_name_title = ' '.join(word.capitalize() for word in full_name.split())
        user = User.objects.create_user(
            email=email,
            full_name=full_name_title,
            otp=otp,
            is_active=False
        )
        serializer.validated_data["full_name"] = full_name_title
        response_data = {
            "status": status.HTTP_201_CREATED,
            "Success": True,
            "message": f"Enter the 4-digit OTP that has been sent to {email}. Please check your inbox or spam folder.",
            "data": serializer.validated_data 
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

class ResendOTPAPIView(generics.GenericAPIView):
    """
    This View resends an account verification OTP, incase a user's OTP expires.
    """

    serializer_class = NewOTPRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        otp = GenerateOTP(length=4)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            response_data = {
                "status": status.HTTP_404_NOT_FOUND,
                "Success": False,
                "message": "E-mail doesn't exist",
            }
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)
        user.otp = otp
        user.has_sent_another_welcome_otp = True
        user.save()

        response_data = {
                "status": status.HTTP_200_OK,
                "Success": True,
                "message": f"Enter the 4-digit OTP that has been sent to {email}. Please check your inbox or spam folder.",
            }
        return Response(response_data, status=status.HTTP_200_OK)

class OTPVerificationAPIView(generics.GenericAPIView):
    """
    This View confirms the OTP sent to the user's email address. If the user's OTP is valid
    and isn't more than 10 minutes of validity, it will be verified, and they will be allowed to proceed with password setup.
    """

    serializer_class = OTPVerificationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp = serializer.validated_data["otp"]
        try:
            user = User.objects.get(otp=otp)

            if user.date_updated + timedelta(minutes=10) < timezone.now():
                return Response(
                    {
                        "status": status.HTTP_406_NOT_ACCEPTABLE,
                        "Success": False,
                        "message": "OTP has expired. Kindly request another.",
                    },
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                )
            else:
                return Response(
                    {
                        "status": status.HTTP_200_OK,
                        "Success": True,
                        "message": "OTP verification successful.",
                    },
                    status=status.HTTP_200_OK,
                )

        except User.DoesNotExist:
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "Success": False,
                    "message": "Invalid OTP",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

class PasswordSetUpAPIView(generics.GenericAPIView):
    """
    This View allows a user whose OTP has been verified to create a password.
    Once the password is created, their account becomes verified and they become
    a sweeftly family member.
    """

    serializer_class = PasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp = serializer.validated_data["otp"]
        try:
            user = User.objects.get(otp=otp)
        except User.DoesNotExist:
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "Success": False,
                    "message": "Invalid OTP",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["password1"])
        user.otp = None
        user.is_active = True
        user.last_login = timezone.now()
        user.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response_data = {
            "status": status.HTTP_201_CREATED,
            "Success": True,
            "message": "Password set successfully.",
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

class TransactionPinCreateAPIView(generics.GenericAPIView):
    """
    This View allows a verified user to create a 4-digit transaction pin.
    """

    serializer_class = TransactionPinSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        pin = serializer.validated_data["pin"]

        if not re.match("^[0-9]{4}$", pin):
            return Response(
                {
                    "status": status.HTTP_406_NOT_ACCEPTABLE,
                    "Success": False,
                    "message": "PIN must be numeric and in four digits",
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        user.pin = make_password(pin)
        user.save()

        return Response(
                {
                    "status": status.HTTP_201_CREATED,
                    "Success": True,
                    "message": "Transaction PIN created successfully",
                },
                status=status.HTTP_201_CREATED,
        )

class LoginAPIView(generics.GenericAPIView):
    """
    This View allows a user to login based on their e-mail and password. If these login params
    are valid, they will be provided with an access and a refresh token, which will be included
    in the header in every API call that requires authentication.
    """

    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate(request, email=email, password=password)

        if user and user.is_active:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            user.last_login = timezone.now()
            user.save()
            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "Success": True,
                    "message": "Login succesful",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                },
                status=status.HTTP_200_OK,
            )

        elif user and not user.is_active:
            response_data = {
                "status": status.HTTP_401_UNAUTHORIZED,
                "Success": False,
                "message": "Inactive Account",
            }
            return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

        else:
            response_data = {
                "status": status.HTTP_401_UNAUTHORIZED,
                "Success": False,
                "message": "Invalid Credentials",
            }
            return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

class UserLogoutAPIView(generics.GenericAPIView):
    """
    This View blacklists the refresh token, thereby logging out the user.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer
    authentication_classes = [JWTAuthentication]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                raise Exception("Refresh token not provided")
            token = RefreshToken(refresh_token)
            token.blacklist()

            user = request.user
            user.last_logout = timezone.now()
            user.save()
            response_data = {
                "status": status.HTTP_205_RESET_CONTENT,
                "Success": True,
                "message": "Log out successful",
            }
            return Response(response_data, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            response_data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "Success": False,
                "message": "Logout not successful",
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

class PasswordChangeOTPAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = NewOTPRequestSerializer
    authentication_classes = [JWTAuthentication]

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            email = request.user.email
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {
                    "status": status.HTTP_404_NOT_FOUND,
                    "Success": False,
                    "message": "E-mail doesn't exist",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        otp = GenerateOTP(length=4)
        user.otp = otp
        user.save()

        return Response(
                {
                    "status": status.HTTP_200_OK,
                    "Success": True,
                    "message": f"A password reset OTP has been sent to: {email}. Please note that it expires after 10 minutes.",
                },
                status=status.HTTP_200_OK,
            )

class PasswordChangeAPIView(generics.GenericAPIView):
    """
    View for changing the password after OTP verification for users who forgot their password
    and logged in users who want to change their password.
    """

    serializer_class = OTPVerificationSerializer
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp = serializer.validated_data["otp"]
        try:
            user = User.objects.get(otp=otp)
            if request.user.is_authenticated:
                password_serializer = PasswordChangeAuthenticatedSerializer(
                    data=request.data, context={"user": user}
                )
            else:
                password_serializer = PasswordSerializer(data=request.data)

            password_serializer.is_valid(raise_exception=True)

            if "new_password1" in password_serializer.validated_data:
                new_password = password_serializer.validated_data["new_password1"]
            else:
                new_password = password_serializer.validated_data["password1"]

            self.change_password(user, new_password)
            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "Success": True,
                    "message": "Password changed successfully",
                },
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            return Response(
                {
                    "status": status.HTTP_404_NOT_FOUND,
                    "Success": False,
                    "message": "Invalid OTP",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    def change_password(self, user, new_password):
        user.set_password(new_password)
        user.otp = None
        user.save()

class UserProfileUpdateView(generics.RetrieveUpdateAPIView):
    """
    View for updating user profile information.
    """

    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    serializer_class = UserProfileUpdateSerializer
    authentication_classes = [JWTAuthentication]
    parser_classes = [FormParser, MultiPartParser]

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_data = {
            "status" : status.HTTP_200_OK,
            "message" : "Profile Updated Successfully",
            "data" : serializer.data
        }
        return Response(response_data)

    def perform_update(self, serializer):
        serializer.save()
