from rest_framework import serializers

from .models import ChannelContent


class ChannelContentSerializer(serializers.ModelSerializer):
    language_display = serializers.CharField(
        source="get_language_display",
        read_only=True,
    )

    channel_display = serializers.CharField(
        source="get_channel_display",
        read_only=True,
    )

    class Meta:
        model = ChannelContent
        fields = [
            "id",
            "content_key",
            "language",
            "language_display",
            "channel",
            "channel_display",
            "text",
            "is_verified",
            "reviewed_by",
            "last_reviewed",
            "is_active",
        ]