from rest_framework import serializers

from .models import SupportService


class SupportServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportService
        fields = [
            "id",
            "name",
            "service_type",
            "description",
            "phone_number",
            "alternate_phone_number",
            "email",
            "website",
            "availability",
            "coverage",
            "verification_status",
            "last_verified",
            "next_verification_due",
            "is_emergency_service",
            "is_active",
        ]