from .models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from rest_framework import status
from .utils import send_email, GenerateOTP
from banking.models import Transaction
import os

@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    """
    This function sends an OTP email to a newly created user.
    If sending the email fails, it deletes the user and adds an error message to the response data.
    """
    if created and not (instance.is_staff or instance.is_superuser):

        otp = GenerateOTP(length=4)
        instance.otp = otp
        instance.save()  

        subject = "Welcome! Verify your email address."
        context = {'full_name': instance.full_name, 'otp' : otp}

        message = render_to_string('welcome_email.html', context)

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

@receiver(post_save, sender=Transaction)
def send_welcome_bonus_alert(sender, instance, created, **kwargs):
    """
    This signal sends a credit alert to a newly created user upon succesful verification and password setup.
    """
    if created and instance.from_account == None:

        subject = "Welcome Bonus Alert!"
        context = {
            'recipient_name': instance.to_account.user.full_name, 
            'description' : instance.description,
            'current_balance' : instance.to_account.current_balance,
            'account_number' : instance.to_account.account_number,
            'date' : instance.timestamp.strftime("%Y-%m-%d")
            }

        message = render_to_string('bonus_alert_email.html', context)

        sender_name = "Longman Technologies"
        sender_email = os.getenv("EMAIL_SENDER")
        reply_to_email = os.getenv("REPLY_TO_EMAIL")
        to = [{"email": instance.to_account.user.email, "name": instance.to_account.user.full_name}]

        sent_email = send_email(
            to=to,
            subject=subject,
            sender={"name": sender_name, "email": sender_email},
            reply_to={"email": reply_to_email},
            html_content=message,
        )
        if not sent_email == "Success":
            response_data = {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Success": False,
                "message": "An error occurred while sending bonus alert email. However, your account has been duly updated. Don't fret.",
            }
            return response_data