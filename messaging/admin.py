from django.contrib import admin
from .models import CustomerMessage, Picture


class PictureInline(admin.TabularInline):
    model = CustomerMessage.pictures.through
    extra = 1
    readonly_fields = []


class CustomerMessageAdmin(admin.ModelAdmin):
    list_display = ("reference_id", "user", "message", "date_created", "date_updated")
    search_fields = ("reference_id", "user__email", "message")
    list_filter = ("date_created", "date_updated")
    readonly_fields = ("reference_id", "date_created", "date_updated")
    inlines = [PictureInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user")


class PictureAdmin(admin.ModelAdmin):
    list_display = ("id", "image", "caption", "date_created")
    search_fields = ("caption",)
    list_filter = ("date_created",)
    readonly_fields = ("date_created",)

admin.site.register(CustomerMessage, CustomerMessageAdmin)
admin.site.register(Picture, PictureAdmin)
