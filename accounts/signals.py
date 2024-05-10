from .models import User
from banking.models import Account
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework import status
from .utils import send_email
import os

@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    """
    This function sends an OTP email to a newly created user.
    If sending the email fails, it deletes the user and adds an error message to the response data.
    """
    if created and not (instance.is_staff or instance.is_superuser):
        Account.objects.create(
            user=instance, current_balance=25000.00, account_type="SAVINGS"
        )
        subject = "Welcome! Verify your email address."
        message = f"""
    Hi, {instance.full_name} 

    Thank you for registering with Longman!

    To verify your email address and activate your account, please enter the following OTP:

    {instance.otp}

    This OTP will expire in 10 minutes.

    Sincerely,

    Longman Technologies.
    """
        sender_name = "Longman Technologies"
        sender_email = os.getenv("EMAIL_SENDER")
        reply_to_email = os.getenv("REPLY_TO_EMAIL")
        to = [{"email": instance.email, "name": instance.full_name}]

        sent_email = send_email(
            to=to,
            subject=subject,
            sender={"name": sender_name, "email": sender_email},
            reply_to={"email": reply_to_email},
            html_content=message,
        )
        if not sent_email == "Success":
            instance.delete()
            response_data = {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Success": False,
                "message": "An error occurred while sending the OTP email. Please try registering again.",
            }
            return response_data


@receiver(post_save, sender=User)
def send_new_otp(sender, instance, created, **kwargs):
    """
    This function resends a new otp if the former one expires.
    """
    if not created and (
        instance.otp
        and instance.has_sent_another_welcome_otp
        and not instance.is_active
    ):
        subject = "Verify your email address."
        message = f"""
    Hi, {instance.full_name}

    To verify your email address and activate your account, please enter the following OTP:

    {instance.otp}

    This OTP will expire in 10 minutes.

    Sincerely,

    Longman Technologies
    """
        sender_name = "Longman Technologies"
        sender_email = os.getenv("EMAIL_SENDER")
        reply_to_email = os.getenv("REPLY_TO_EMAIL")
        to = [{"email": instance.email, "name": instance.full_name}]
        sent_email = send_email(
            to=to,
            subject=subject,
            sender={"name": sender_name, "email": sender_email},
            reply_to={"email": reply_to_email},
            html_content=message,
        )
        return sent_email == "Success"


@receiver(post_save, sender=User)
def send_password_reset_otp(sender, instance, created, **kwargs):
    """
    This signal sends an OTP email to a user when a user requests to change their password.
    """
    if not created and (instance.otp and instance.is_active):
        subject = "Password Reset OTP"
        message = f"""
    Hi, {instance.full_name}

    A password reset OTP has been requested for your account.

    To proceed with the procedure, please enter the following OTP:

    {instance.otp}

    This OTP will expire in 10 minutes.

    Sincerely,

    Longman Technologies
    """
        sender_name = "Longman Technologies"
        sender_email = os.getenv("EMAIL_SENDER")
        reply_to_email = os.getenv("REPLY_TO_EMAIL")
        to = [{"email": instance.email, "name": instance.full_name}]
        sent_email = send_email(
            to=to,
            subject=subject,
            sender={"name": sender_name, "email": sender_email},
            reply_to={"email": reply_to_email},
            html_content=message,
        )
        return sent_email == "Success"
