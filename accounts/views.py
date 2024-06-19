from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.template.loader import render_to_string
from drf_spectacular.utils import extend_schema
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import MethodNotAllowed
from .utils import GenerateOTP, send_email
from .serializers import (
    UserRegistrationSerializer,
    OTPVerificationSerializer,
    NewOTPRequestSerializer,
    TransactionPinSerializer,
    LoginSerializer,
    PasswordSerializer,
    DeliberatePasswordChangeSerializer,
    UserProfileUpdateSerializer,
    UserDetailSerializer,
)
from banking.models import Account, Transaction, Ledger
import os


# Create your views here.

User = get_user_model()

class UserRegistrationAPIView(generics.GenericAPIView):
    """
    This view registers a new user based on their full name and email address.\n
    When a user registers, their data is first saved in the database, and an OTP is sent\n
    to verify their entered e-mail address.
    """

    serializer_class = UserRegistrationSerializer
    @extend_schema(
    description= """
    This endpoint registers a new user based on their full name and email address.\n
    When a user registers, their data is first saved in the database, and an OTP is sent\n
    to verify their entered e-mail address.
    """,
    request=UserRegistrationSerializer,
    responses={
        201: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
                "data": {
                    "type": "object",
                    "properties" : {
                        "full_name" :{"type" : "string"},
                        "email" :{"type" : "string"} 
                    }                    
                    },
            },
        },
        400: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
        500: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
    },
    methods=["POST"],
    )      
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        if User.objects.filter(email=email).exists():
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "Success": False,
                    "message": "User with this email already exists",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        full_name = serializer.validated_data["full_name"]
        full_name_title = ' '.join(word.capitalize() for word in full_name.split())
        User.objects.create_user(
            email=email,
            full_name=full_name_title,
            is_active=False
        )
        serializer.validated_data["full_name"] = full_name_title
        response_data = {
            "status": status.HTTP_201_CREATED,
            "Success": True,
            "message": "Enter the 4-digit OTP that has been sent to your email address. Please check your inbox or spam folder.",
            "data": serializer.validated_data 
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

class ResendOTPAPIView(generics.GenericAPIView):
    """
    This view resends an account verification OTP, incase a user's OTP expires.\n
    The user is expected to enter their registered email so they can get a new 4-digit OTP.
    """

    serializer_class = NewOTPRequestSerializer
    
    @extend_schema(
    description="""
    This endpoint resends an account verification OTP, incase a user's OTP expires.\n
    The user is expected to enter their registered email so they can get a new 4-digit OTP.
    """,
    request=NewOTPRequestSerializer,
    responses={
        200: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
        400: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
        404: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
        500: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        }
    },
    methods=["POST"],
    ) 
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            response_data = {
                "status": status.HTTP_404_NOT_FOUND,
                "Success": False,
                "message": "E-mail doesn't exist",
            }
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)
        if user and user.is_active:
            response_data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "Success": False,
                "message": "You are not allowed to perform this operation, as your account has been verified",
            }
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)

        otp = GenerateOTP(length=4)

        user.otp = otp
        user.save()
        
        subject = "Verify your email address."
        context = {'full_name': user.full_name, 'otp': otp}
        
        message = render_to_string('otp_resend.html', context)
        
        sender_name = "Longman Technologies"
        sender_email = os.getenv("EMAIL_SENDER")
        reply_to_email = os.getenv("REPLY_TO_EMAIL")
        to = [{"email": user.email, "name": user.full_name}]
        sent_email = send_email(
            to=to,
            subject=subject,
            sender={"name": sender_name, "email": sender_email},
            reply_to={"email": reply_to_email},
            html_content=message,
        )
        
        if sent_email == "Success":
            response_data = {
                "status": status.HTTP_200_OK,
                "Success": True,
                "message": f"Enter the 4-digit OTP that has been sent to your email address. Please check your inbox or spam folder.",
            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Success": False,
                "message": "An error occurred while sending the OTP email. Please try again later.",
            }
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OTPVerificationAPIView(generics.GenericAPIView):
    """
    This view confirms the OTP sent to the user's email address. If the user's OTP is valid\n
    and isn't more than 10 minutes of validity, it will be verified, and they will be allowed to proceed with password setup.\n
    """

    serializer_class = OTPVerificationSerializer

    @extend_schema(
    description= """
    This endpoint confirms the OTP sent to a user's email address. If a user's OTP is valid\n
    and isn't more than 10 minutes of validity, it will be verified, and they will be allowed to proceed with password setup.
    """,
    request=OTPVerificationSerializer,
    responses={
        200: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
        400: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
        404: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
        500: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        }
    },
    methods=["POST"],
    ) 
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp = serializer.validated_data["otp"]
        try:
            user = User.objects.get(otp=otp)
        except User.DoesNotExist:
            return Response(
                {
                    "status": status.HTTP_404_NOT_FOUND,
                    "Success": False,
                    "message": "Invalid OTP",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        if user.date_updated + timedelta(minutes=10) < timezone.now():
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "Success": False,
                    "message": "OTP has expired. Kindly request another.",
                },
                    status=status.HTTP_400_BAD_REQUEST,
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

class PasswordSetUpAPIView(generics.GenericAPIView):
    """
    This view allows a user whose OTP has been verified to create a password.\n
    Once the password is created, their account becomes verified and they become\n
    a bona fide bank customer. They also get a welcome token of 20,000 naira.\n 
    Generous! Isn't it?
    """
    serializer_class = PasswordSerializer
    
    @extend_schema(
    description =  """
    This endpoint allows a user whose OTP has been verified to create a password.\n
    Once the password is created, their account becomes verified and they become\n
    a bona fide bank customer. They also get a welcome token of 20,000 naira.\n 
    Generous! Isn't it?
    """,
    request=PasswordSerializer,
    responses={
        201: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
                "account_number": {"type": "string"},
                "access_token": {"type": "string"},
                "refresh_token": {"type": "string"},
            },
        },
        400: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
        404: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
    },
    methods=["POST"],
    ) 
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp = serializer.validated_data["otp"]
        try:
            user = User.objects.get(otp=otp)
        except User.DoesNotExist:
            return Response(
                {
                    "status": status.HTTP_404_NOT_FOUND,
                    "Success": False,
                    "message": "Invalid OTP",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        if user.date_updated + timedelta(minutes=10) < timezone.now():
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "Success": False,
                    "message": "OTP has expired. Kindly request another.",
                },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        user.set_password(serializer.validated_data["password1"])
        user.otp = None
        user.is_active = True
        user.last_login = timezone.now()
        user.save()

        account = Account.objects.create(
            user=user, current_balance=20000.00, account_type="SAVINGS"
        )

        transaction = Transaction.objects.create(
            transaction_type="CREDIT",
            transaction_mode="AUTO CREDIT",
            from_account=None,  
            to_account=account,
            amount=20000.00,
            description="Welcome! Enjoy your welcome bonus!",
        )

        Ledger.objects.create(
            account=account,
            transaction = transaction,
            balance_after_transaction = account.current_balance 
        )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh.access_token)

        response_data = {
            "status": status.HTTP_201_CREATED,
            "Success": True,
            "message": "Password set successfully and account creation complete. A token of 20,000.00 naira has been credited to your account as a welcome bonus.",
            "account_number": account.account_number,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class TransactionPinCreateAPIView(generics.GenericAPIView):
    """
    This view allows a verified user to create a 4-digit transaction pin.
    """

    serializer_class = TransactionPinSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @extend_schema(
    description= """This endpoint allows a verified user to create a 4-digit transaction pin.""",
    request=TransactionPinSerializer,
    responses={
        201: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
        400: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        }
    },
    methods=["POST"],
    ) 
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        pin = serializer.validated_data["pin"]

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
    This view allows a user to login based on their e-mail and password. If these login params\n
    are valid, they will be provided with an access and a refresh token, which will be included\n
    in the header in every API call that requires authentication.
    """

    serializer_class = LoginSerializer

    @extend_schema(
    description= """
    This endpoint allows a user to login based on their e-mail and password. If these login params\n
    are valid, they will be provided with an access and a refresh token, which will be included\n
    in the header in every API call that requires authentication.
    """,
    request=LoginSerializer,
    responses={
        200: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
                "access_token": {"type": "string"},
                "refresh_token": {"type": "string"},
            },
        },
        401: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
    },
    methods=["POST"],
    )
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
                    "message": "Login successful",
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
    This View blacklists the refresh token, consequently preventing a user from generating a new\n
    access token until they are re-authenticated.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_serializer_class(self):
        return None
    
    @extend_schema(
    description=  """
    This endpoint blacklists the refresh token, consequently preventing a user from generating a new\n
    access token until they are re-authenticated.
    """,
    responses={
        200: {"description": "Log out successful"},
        400: {"description": "Log out not successful"}
    },
    request=None,
    methods=["POST"]
    )     
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
                "status": status.HTTP_200_OK,
                "Success": True,
                "message": "Log out successful",
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            response_data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "Success": False,
                "message": f"Logout not successful because {e}",
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeOTPAPIView(generics.GenericAPIView):
    """
    This view allows a user to generate a password reset OTP. If the user is authenticated,\n
    the OTP is sent directly to the user's registered e-mail. Otherwise, they will be required\n
    to provide to provide their registered e-mail, so they can receive the OTP.
    """
    permission_classes = [AllowAny]
    serializer_class = NewOTPRequestSerializer
    authentication_classes = [JWTAuthentication]
    @extend_schema(
    description= """
    This view allows a user to generate a password reset OTP. If the user is authenticated,\n
    the OTP is sent directly to the user's registered e-mail. Otherwise, they will be required\n
    to provide to provide their registered e-mail, so they can receive the OTP.
    """,
    request=NewOTPRequestSerializer,
    responses={
        200: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
        500: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
        404: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
    },
    methods=["POST"],
    )
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

        subject = "Password Reset OTP"
        context = {'full_name': user.full_name, 'otp': otp}
        
        message = render_to_string('password_reset.html', context) 
        
        sender_name = "Longman Technologies"
        sender_email = os.getenv("EMAIL_SENDER")
        reply_to_email = os.getenv("REPLY_TO_EMAIL")
        to = [{"email": user.email, "name": user.full_name}]
        sent_email = send_email(
            to=to,
            subject=subject,
            sender={"name": sender_name, "email": sender_email},
            reply_to={"email": reply_to_email},
            html_content=message,
        )
        
        if sent_email == "Success":
            response_data = {
                "status": status.HTTP_200_OK,
                "Success": True,
                "message": "A password reset OTP has been sent to your registered email address. Please note that it expires after 10 minutes.",
            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Success": False,
                "message": "An error occurred while sending the OTP email. Please try again later.",
            }
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ForgottenPasswordResetAPIView(generics.GenericAPIView):
    """
    This view is for users who have forgotten their passwords. They will be prompted to input their\n
    otp, new password, and new password confirmation. Immediately these inputs are verified as valid,\n
    they will be allowed to login with their new password.
    """
    serializer_class = PasswordSerializer
    permission_classes = [AllowAny]

    @extend_schema(
    description= """
    This endpoint is for users who have forgotten their passwords. They will be prompted to input their\n
    otp, new password, and new password confirmation. Immediately these inputs are verified as valid,\n
    they will be allowed to login with their new password.
    """,
    request=PasswordSerializer,
    responses={
        200: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
        400: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
        404: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
    },
    methods=["POST"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp = serializer.validated_data["otp"]
        try:
            user = User.objects.get(otp=otp)
        except User.DoesNotExist:
            return Response(
                {
                    "status": status.HTTP_404_NOT_FOUND,
                    "Success": False,
                    "message": "Invalid OTP",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        if user.date_updated + timedelta(minutes=10) < timezone.now():
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "Success": False,
                    "message": "OTP has expired. Kindly request another.",
                },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        self.reset_forgotten_password(request, user)

        return Response(
                {
                    "status": status.HTTP_200_OK,
                    "Success": True,
                    "message": "Password changed successfully",
                },
                status=status.HTTP_200_OK,
            )

    def reset_forgotten_password(self, request, user):
        serializer = PasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data["password1"]
        self.change_password(user, new_password)

    def change_password(self, user, new_password):
        user.set_password(new_password)
        user.otp = None
        user.save()

class DeliberatePasswordResetAPIView(generics.GenericAPIView):
    """
    Unlike the ForgottenPasswordResetAPIView, this view allows only authenticated users to change their password.\n
    A more nuanced explanation is that a user didn't forget their password, but they feel like changing it for reasons\n
    best personal to them. Hence, they will be required to provide their old password before they can proceed.
    """
    serializer_class = DeliberatePasswordChangeSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @extend_schema(
    description =  """
    This endpoint allows only authenticated users to change their password.\n
    A more nuanced explanation is that a user didn't forget their password, but they feel like changing it for reasons\n
    best personal to them. Hence, they will be required to provide their old password before they can proceed.
    """,
    request=DeliberatePasswordChangeSerializer,
    responses={
        200: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
        400: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
        404: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
    },
    methods=["POST"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp = serializer.validated_data["otp"]
        user = request.user

        if otp != user.otp:
            return Response(
                    {
                "status": status.HTTP_400_BAD_REQUEST,
                "Success": False,
                "message": "Invalid OTP"
            },
                status=status.HTTP_400_BAD_REQUEST
                )

        if user.date_updated + timedelta(minutes=10) < timezone.now():
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "Success": False,
                    "message": "OTP has expired. Kindly request another.",
                },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"status": status.HTTP_400_BAD_REQUEST,
                 "Success": False,
                 "message": "Incorrect old password"},
                status=status.HTTP_400_BAD_REQUEST)
        
        new_password = serializer.validated_data["new_password1"]
        user.set_password(new_password)
        user.save()

        return Response(
            {
                "status": status.HTTP_200_OK,
                "Success": True,
                "message": "Password changed successfully",
            },
            status=status.HTTP_200_OK,
        )

class UserProfileUpdateAPIView(generics.RetrieveUpdateAPIView):
    """
    This view allows a user to update their information.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileUpdateSerializer
    authentication_classes = [JWTAuthentication]
    parser_classes = [FormParser, MultiPartParser, JSONParser]

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    @extend_schema(
        description =  """This endpoint allows a user to update their information.""",
        responses={
        200: UserProfileUpdateSerializer,
        400: {"description": "Bad request"},
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    },
        methods=["PUT", "PATCH"]
    )
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
        return Response(response_data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save()

    def get(self, request, *args, **kwargs):
        raise MethodNotAllowed("GET")

class UserDetailAPIView(generics.GenericAPIView):
    """
    This view allows a user to only view their profile.
    """
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    @extend_schema(
    description = """This endpoint allows a user to only view their profile.""",
    responses={
        200: UserDetailSerializer,
        400: {"description" : "Bad Request"},
        500: {"description": "Internal server error"},
    },
    methods=["GET"],
    )    
    def get(self, request):
        instance  = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'status': status.HTTP_200_OK,
            'success' : True,
            'message': 'User details retrieved successfully',
            'data': serializer.data
        })


