from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "full_name",
            "email",
            "phone_number",
            "date_of_birth",
            "address",
            "profile_picture",
        )


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    model = User
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "full_name",
                    "email",
                    "phone_number",
                    #"date_of_birth",
                    "address",
                    "otp",
                    "profile_picture",
                    "is_active",
                    "is_staff",
                )
            },
        ),
      #  ("Important dates", {"fields": ("last_login", "last_logout")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "full_name",
                    "email",
                    "address",
                    "otp",
                    "password1",
                    "password2",
                    "is_active",
                ),
            },
        ),
    )
    list_display = (
        "full_name",
        "email",
        "age",
        "otp",
        "is_active",
    )
    search_fields = ("email",)
    ordering = ("-date_created",)


admin.site.register(User, CustomUserAdmin)
