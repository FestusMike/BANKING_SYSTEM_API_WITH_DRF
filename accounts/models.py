from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from datetime import date
from utils.tools import BaseModel
from .utils import profile_image_path
from .managers import CustomUserManager

# Create your models here.

class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    full_name = models.CharField(max_length=255, null=False)
    email = models.EmailField(unique=True, blank=False, null=False)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(null=True)
    age = models.IntegerField(null=True, blank=True)
    address = models.CharField(max_length=50, blank=True, null=True)
    otp = models.CharField(null=True, unique=True, max_length=4)
    pin = models.CharField(null=True, max_length=255)
    profile_picture = models.ImageField(null=True, upload_to=profile_image_path)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    last_logout = models.DateTimeField(null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = CustomUserManager()

    class Meta:
        db_table = "Users"
        abstract = False

    def calculate_age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

    def save(self, *args, **kwargs):
        self.age = self.calculate_age()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        if self.full_name and not self.is_superuser: 
            return f"{self.id} - {self.full_name}"
        else:
            return f"{self.full_name} - Admin"