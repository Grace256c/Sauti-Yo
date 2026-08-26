from rest_framework import serializers

from .models import (
    Referral,
    ReferralStatusHistory,
)


class ReferralStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ReferralStatusHistory
        fields = [
            "id",
            "from_status",
            "to_status",
            "changed_by",
            "changed_by_name",
            "note",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "changed_by",
            "changed_by_name",
            "created_at",
        ]

    def get_changed_by_name(self, obj):
        if not obj.changed_by:
            return None

        full_name = obj.changed_by.get_full_name().strip()

        return full_name or obj.changed_by.username


class ReferralSerializer(serializers.ModelSerializer):
    organisation_name = serializers.CharField(
        source="organisation.support_service.name",
        read_only=True,
    )

    rights_topic_title = serializers.CharField(
        source="rights_topic.title",
        read_only=True,
    )

    assigned_to_name = serializers.SerializerMethodField()

    status_history = ReferralStatusHistorySerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Referral
        fields = [
            "id",
            "reference",
            "organisation",
            "organisation_name",
            "rights_topic",
            "rights_topic_title",
            "summary",
            "district",
            "language",
            "preferred_support_channel",
            "status",
            "citizen_consent_to_share",
            "shared_at",
            "accepted_at",
            "completed_at",
            "assigned_to",
            "assigned_to_name",
            "status_history",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "reference",
            "organisation_name",
            "rights_topic_title",
            "assigned_to_name",
            "status_history",
            "created_at",
            "updated_at",
        ]

    def get_assigned_to_name(self, obj):
        if not obj.assigned_to:
            return None

        full_name = obj.assigned_to.get_full_name().strip()

        return full_name or obj.assigned_to.username

    def validate(self, attrs):
        consent = attrs.get(
            "citizen_consent_to_share",
            getattr(
                self.instance,
                "citizen_consent_to_share",
                False,
            ),
        )

        if not consent:
            sensitive_fields = [
                attrs.get("summary"),
                attrs.get("district"),
                attrs.get("language"),
                attrs.get(
                    "preferred_support_channel"
                ),
            ]

            if any(
                value not in (
                    None,
                    "",
                )
                for value in sensitive_fields
            ):
                raise serializers.ValidationError(
                    {
                        "citizen_consent_to_share":
                            (
                                "Citizen consent is required "
                                "before referral details are shared."
                            )
                    }
                )

        return attrs


class ReferralCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Referral
        fields = [
            "organisation",
            "rights_topic",
            "summary",
            "district",
            "language",
            "preferred_support_channel",
            "citizen_consent_to_share",
        ]

    def validate_citizen_consent_to_share(
        self,
        value,
    ):
        if not value:
            raise serializers.ValidationError(
                "Citizen consent is required before creating a referral."
            )

        return value