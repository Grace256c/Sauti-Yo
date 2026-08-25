from django.contrib import admin

from .models import ChannelContent


@admin.register(ChannelContent)
class ChannelContentAdmin(admin.ModelAdmin):
    list_display = (
        "content_key",
        "language",
        "channel",
        "is_verified",
        "reviewed_by",
        "last_reviewed",
        "is_active",
    )

    list_filter = (
        "language",
        "channel",
        "is_verified",
        "is_active",
    )

    search_fields = (
        "content_key",
        "text",
        "reviewed_by",
    )

    ordering = (
        "content_key",
        "language",
        "channel",
    )