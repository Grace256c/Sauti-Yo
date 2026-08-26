from rest_framework import serializers

from apps.support.serializers import SupportServiceSerializer

from .models import (
    PartnerMember,
    PartnerOrganisation,
    PartnerServiceConfiguration,
    PartnerVerificationDocument,
    PartnerVerificationRequest,
)


class PartnerServiceConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerServiceConfiguration
        fields = [
            "id",
            "service_description",
            "rights_categories",
            "support_types",
            "languages",
            "support_channels",
            "districts_served",
            "nationwide",
            "free_services",
            "appointment_required",
            "accepting_referrals",
            "weekly_referral_limit",
            "availability_note",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class PartnerMemberSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(
        source="user.id",
        read_only=True,
    )

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    class Meta:
        model = PartnerMember
        fields = [
            "id",
            "user_id",
            "username",
            "email",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "user_id",
            "username",
            "email",
            "created_at",
            "updated_at",
        ]


class PartnerVerificationDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PartnerVerificationDocument
        fields = [
            "id",
            "document_type",
            "title",
            "file",
            "uploaded_by",
            "uploaded_by_name",
            "uploaded_at",
            "is_active",
        ]

        read_only_fields = [
            "id",
            "uploaded_by",
            "uploaded_by_name",
            "uploaded_at",
        ]

    def get_uploaded_by_name(self, obj):
        if not obj.uploaded_by:
            return None

        full_name = obj.uploaded_by.get_full_name().strip()

        return full_name or obj.uploaded_by.username


class PartnerVerificationRequestSerializer(serializers.ModelSerializer):
    documents = PartnerVerificationDocumentSerializer(
        many=True,
        read_only=True,
    )

    submitted_by_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PartnerVerificationRequest
        fields = [
            "id",
            "status",
            "declaration_accurate",
            "declaration_authorised",
            "declaration_consent",
            "submitted_by",
            "submitted_by_name",
            "submitted_at",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "review_notes",
            "documents",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "status",
            "submitted_by",
            "submitted_by_name",
            "submitted_at",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "review_notes",
            "documents",
            "created_at",
            "updated_at",
        ]

    def get_submitted_by_name(self, obj):
        if not obj.submitted_by:
            return None

        full_name = obj.submitted_by.get_full_name().strip()

        return full_name or obj.submitted_by.username

    def get_reviewed_by_name(self, obj):
        if not obj.reviewed_by:
            return None

        full_name = obj.reviewed_by.get_full_name().strip()

        return full_name or obj.reviewed_by.username


class PartnerOrganisationSerializer(serializers.ModelSerializer):
    support_service = SupportServiceSerializer(
        read_only=True,
    )

    service_configuration = PartnerServiceConfigurationSerializer(
        read_only=True,
    )

    members = PartnerMemberSerializer(
        many=True,
        read_only=True,
    )

    latest_verification = serializers.SerializerMethodField()

    class Meta:
        model = PartnerOrganisation
        fields = [
            "id",
            "support_service",
            "organisation_type",
            "registration_number",
            "year_established",
            "headquarters_district",
            "physical_address",
            "public_email",
            "public_phone",
            "is_active",
            "service_configuration",
            "members",
            "latest_verification",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "support_service",
            "is_active",
            "members",
            "latest_verification",
            "created_at",
            "updated_at",
        ]

    def get_latest_verification(self, obj):
        verification = obj.verification_requests.first()

        if verification is None:
            return None

        return PartnerVerificationRequestSerializer(
            verification,
            context=self.context,
        ).data


from .models import PartnerPreferences


class PartnerPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerPreferences

        fields = [
            "id",
            "email_notifications",
            "sms_notifications",
            "referral_notifications",
            "verification_notifications",
            "product_updates",
            "show_public_phone",
            "show_public_email",
            "allow_remote_referrals",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]



class PublicPartnerMatchSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    organisation_name = serializers.CharField()
    organisation_type = serializers.CharField()
    service_description = serializers.CharField()
    public_phone = serializers.CharField()
    public_email = serializers.EmailField()
    website = serializers.CharField()
    districts_served = serializers.ListField(
        child=serializers.CharField()
    )
    nationwide = serializers.BooleanField()
    languages = serializers.ListField(
        child=serializers.CharField()
    )
    support_channels = serializers.ListField(
        child=serializers.CharField()
    )
    rights_categories = serializers.ListField(
        child=serializers.CharField()
    )
    support_types = serializers.ListField(
        child=serializers.CharField()
    )
    free_services = serializers.BooleanField()
    appointment_required = serializers.BooleanField()
    availability_note = serializers.CharField()
    score = serializers.IntegerField()
    reasons = serializers.ListField(
        child=serializers.CharField()
    )
