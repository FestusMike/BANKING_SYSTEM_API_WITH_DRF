from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from utils.tools import BaseModel
from .utils import profile_image_path
from .managers import CustomUserManager

# Create your models here.

class User(AbstractBaseUser, PermissionsMixin, BaseModel):
   
    full_name = models.CharField(max_length=255, null=False)
    email = models.EmailField(unique=True, blank=False, null=False)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(null=True)
    address = models.CharField(max_length=50, blank=True, null=True)
    otp = models.IntegerField(null=True, blank=True)
    pin = models.CharField(null=True, max_length=255)
    profile_picture = models.ImageField(null=True, upload_to=profile_image_path)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    has_sent_another_welcome_otp = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    last_logout = models.DateTimeField(null=True)

    USERNAME_FIELD = 'email'

    objects = CustomUserManager()

    class Meta:
        db_table = "Users"
        abstract = False

    def __str__(self) -> str:
        if self.id and self.full_name:
            return f"{self.id} - {self.full_name}"
        else:
            return "Superuser Account"