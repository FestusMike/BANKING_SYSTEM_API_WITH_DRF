from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.admin.models import LogEntry, DELETION
from django.utils.html import escape
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User


class LogEntryAdmin(admin.ModelAdmin):
    date_hierarchy = 'action_time'

    list_filter = ['user', 'content_type', 'action_flag']
    search_fields = ['object_repr', 'change_message']
    list_display = ['action_time', 'user', 'content_type', 'object_link', 'action_flag']

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    def object_link(self, obj):
        if obj.action_flag == DELETION:
            link = escape(obj.object_repr)
        else:
            ct = obj.content_type
            link = '<a href="%s">%s</a>' % (
            reverse('admin:%s_%s_change' % (ct.app_label, ct.model), args=[obj.object_id]),
            escape(obj.object_repr),
        )
        return mark_safe(link)
    object_link.admin_order_field = 'object_repr'
    object_link.short_description = 'object'

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
        "phone_number",
        "otp",
        "is_active",
    )
    search_fields = ("email",)
    ordering = ("-date_created",)



admin.site.register(User, CustomUserAdmin)
admin.site.register(LogEntry, LogEntryAdmin)
