from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "middle_name",
            "last_name",
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
                    "first_name",
                    "middle_name",
                    "last_name",
                    "email",
                    "phone_number",
                    "date_of_birth",
                    "address",
                    "otp",
                    "profile_picture",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "last_logout")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "first_name",
                    "middle_name",
                    "last_name",
                    "email",
                    "address",
                    "otp",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
    list_display = (
        "first_name",
        "last_name",
        "email",
        "otp",
        "date_created",
        "date_updated",
    )
    search_fields = ("email",)
    ordering = ("-date_created",)


# Register CustomUserAdmin instead
admin.site.register(User, CustomUserAdmin)
