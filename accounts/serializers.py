from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from filetype import guess
import re

User = get_user_model()


class UserRegistrationSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()

    def validate_full_name(self, value):
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise ValidationError(
            "Only alphabetical characters and spaces are allowed for the full name."
        )
        return value

class OTPVerificationSerializer(serializers.Serializer):
    otp = serializers.IntegerField()

class NewOTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class TransactionPinSerializer(serializers.Serializer):
    pin = serializers.CharField()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class LogoutSerializer(serializers.Serializer):
    pass

class PasswordSerializer(serializers.Serializer):
    otp = serializers.IntegerField()
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate(self, data):
        password1 = data.get("password1")
        password2 = data.get("password2")

        if password1 != password2:
            raise serializers.ValidationError("Passwords don't match")
        return data

class PasswordChangeAuthenticatedSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password1 = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context.get("user")
        if not user.check_password(value):
            raise serializers.ValidationError("Incorrect old password")
        return value

    def validate_new_password(self, value):
        if not value:
            raise serializers.ValidationError("New password cannot be empty")
        return value

    def password_equality(self, data):
        new_password1 = data.get("new_password1")
        new_password2 = data.get("new_password2")

        if new_password1 != new_password2:
            raise serializers.ValidationError("Passwords don't match")
        return data

    def validate(self, data):
        self.password_equality(data)
        return data


class UserProfileUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            "date_of_birth",
            "phone_number",
            "date_of_birth",
            "address",
            "profile_picture",
        )

    def validate_phone_number(self, value): 
        if not value.startswith("+234") or(value.startswith("+234") and len(value) > 15):
            raise serializers.ValidationError(
                "Phone number must start with country code +234 and must be 15 characters max."
            )
        return value

    def validate_profile_picture(self, value):
        if not value:
            return value  

        if value.size > 2 * 1024 * 1024:  
            raise serializers.ValidationError("Profile picture must be less than 2MB")

        file_type = guess(value)
        if not file_type:
            raise serializers.ValidationError("Uploaded file type cannot be determined")
        allowed_types = ['image/jpeg', 'image/png']
        if file_type.mime not in allowed_types:
            raise serializers.ValidationError("Profile picture must be a JPEG or PNG image")
        return value


    