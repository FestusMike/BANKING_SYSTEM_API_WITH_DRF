from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.template.loader import render_to_string
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from .permissions import IsOwner
from .utils import GenerateOTP, send_email
from .serializers import (
    UserRegistrationSerializer,
    OTPVerificationSerializer,
    NewOTPRequestSerializer,
    TransactionPinSerializer,
    LoginSerializer,
    PasswordSerializer,
    PasswordChangeAuthenticatedSerializer,
    UserProfileUpdateSerializer,
    UserDetailSerializer
)
from banking.models import Account, Transaction, Ledger
import os


# Create your views here.

User = get_user_model()


class UserRegistrationAPIView(generics.GenericAPIView):
    """
    This View registers a new user based on their full name and email address.
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
    This View resends an account verification OTP, incase a user's OTP expires.
    """

    serializer_class = NewOTPRequestSerializer

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
    This View allows a user whose OTP has been verified to create a password.
    Once the password is created, their account becomes verified and they become
    a bona fide bank customer.
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
    This View blacklists the refresh token and access token, thereby logging out the user.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_serializer_class(self):
        from rest_framework.serializers import BaseSerializer
        if getattr(self, 'swagger_fake_view', False):
            return BaseSerializer
        return None
    
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

    def change_password(self, user, new_password):
        user.set_password(new_password)
        user.otp = None
        user.save()


class UserProfileUpdateAPIView(generics.RetrieveUpdateAPIView):
    """
    View for updating user profile information.
    """

    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = UserProfileUpdateSerializer
    authentication_classes = [JWTAuthentication]
    parser_classes = [FormParser, MultiPartParser, JSONParser]

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
        return Response(response_data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save()

class UserDetailAPIView(generics.GenericAPIView):
    """
    View that allows a user to view their profile.
    """
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_object(self):
        return self.request.user
    
    def get(self, request):
        instance  = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'status': status.HTTP_200_OK,
            'success' : True,
            'message': 'User details retrieved successfully',
            'data': serializer.data
        })

class UsersListAPIView(generics.ListAPIView):
    from rest_framework.pagination import PageNumberPagination
    queryset = User.objects.all().order_by("-date_created")
    permission_classes = [IsAdminUser]
    serializer_class = UserDetailSerializer
    pagination_class = PageNumberPagination

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)
        serializer = self.get_serializer(paginated_queryset, many=True)
        response_data = {
            'status' : status.HTTP_200_OK,
            'success' : True,
            'data' : serializer.data
            }
        return paginator.get_paginated_response(response_data)
        
class AdminUserURDAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [FormParser, MultiPartParser, JSONParser]
    lookup_field = 'id'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        response_data = {
            'status': status.HTTP_200_OK,
            'success' : True,
            'message': 'User retrieved successfully',
            'data': serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_data = {
            'status': status.HTTP_200_OK,
            'success' : True,
            'message': 'User updated successfully',
            'data': serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        response_data = {
            'status': status.HTTP_204_NO_CONTENT,
            'success' : True,
            'message': 'User deleted successfully',
        }
        return Response(response_data, status=status.HTTP_204_NO_CONTENT)
