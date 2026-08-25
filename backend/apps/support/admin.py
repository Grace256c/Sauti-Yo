from django.contrib import admin

from .models import SupportService


@admin.register(SupportService)
class SupportServiceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "service_type",
        "phone_number",
        "verification_status",
        "is_emergency_service",
        "is_active",
    )

    list_filter = (
        "verification_status",
        "is_emergency_service",
        "is_active",
    )

    search_fields = (
        "name",
        "service_type",
        "coverage",
        "phone_number",
    )