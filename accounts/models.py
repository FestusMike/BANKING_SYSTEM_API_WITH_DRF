from django.db import models
from django.contrib.auth.models import AbstractUser
from utils.tools import primary_key
from .utils import profile_image_path
from .managers import CustomUserManager

# Create your models here.


class User(AbstractUser):
    account_number = models.BigIntegerField(
        unique=True, primary_key=True, editable=False, default=primary_key(10)
    )
    first_name = models.CharField(max_length=50, blank=False, null=False)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=False, null=False)
    email = models.EmailField(unique=True, blank=False, null=False)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(null=True)
    address = models.CharField(max_length=50, blank=True, null=True)
    otp = models.IntegerField(null=True, blank=True)
    profile_picture = models.ImageField(null=True, upload_to=profile_image_path)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True)
    last_logout = models.DateTimeField(null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()
