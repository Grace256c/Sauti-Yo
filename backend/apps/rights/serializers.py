from rest_framework import serializers

from apps.support.serializers import (
    SupportServiceSerializer,
)

from .models import (
    ActionStep,
    LegalProvision,
    RightsTopic,
    SafetyResponse,
    Situation,
    SituationRightsTopic,
)


def get_requested_language(serializer):
    """
    Read ?lang=xx from the current API request.

    Supported examples:
    ?lang=en
    ?lang=lg
    ?lang=sw
    ?lang=nyn

    English is used as the default.
    """
    request = serializer.context.get("request")

    if not request:
        return "en"

    language = request.query_params.get("lang", "en")

    supported_languages = {
        "en",
        "lg",
        "sw",
        "nyn",
    }

    if language not in supported_languages:
        return "en"

    return language


class ActionStepSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = ActionStep
        fields = [
            "id",
            "order",
            "title",
            "description",
            "is_safety_critical",
            "is_active",
        ]

    def get_title(self, obj):
        language = get_requested_language(self)

        if language == "en":
            return obj.title

        translation = obj.translations.filter(
            language=language
        ).first()

        if translation:
            return translation.title

        return obj.title

    def get_description(self, obj):
        language = get_requested_language(self)

        if language == "en":
            return obj.description

        translation = obj.translations.filter(
            language=language
        ).first()

        if translation:
            return translation.description

        return obj.description


class SafetyResponseSerializer(
    serializers.ModelSerializer
):
    message = serializers.SerializerMethodField()

    class Meta:
        model = SafetyResponse
        fields = [
            "id",
            "trigger_key",
            "message",
            "is_active",
        ]

    def get_message(self, obj):
        language = get_requested_language(self)

        if language == "en":
            return obj.message

        translation = obj.translations.filter(
            language=language
        ).first()

        if translation:
            return translation.message

        return obj.message


class LegalProvisionSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = LegalProvision
        fields = [
            "id",
            "source_type",
            "law_title",
            "provision_reference",
            "provision_heading",
            "provision_text",
            "plain_language_explanation",
            "source_url",
            "jurisdiction",
            "reviewed_by",
            "last_reviewed",
            "next_review_due",
            "verification_status",
            "order",
            "is_active",
        ]


class RightsTopicSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()

    action_steps = ActionStepSerializer(
        many=True,
        read_only=True,
    )

    safety_responses = SafetyResponseSerializer(
        many=True,
        read_only=True,
    )

    support_services = SupportServiceSerializer(
        many=True,
        read_only=True,
    )


    legal_provisions = LegalProvisionSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = RightsTopic
        fields = [
            "id",
            "slug",
            "title",
            "risk_level",
            "summary",
            "source_name",
            "source_url",
            "reviewed_by",
            "last_reviewed",
            "next_review_due",
            "verification_status",
            "support_services",
            "legal_provisions",
            "action_steps",
            "safety_responses",
            "is_active",
        ]

    def get_title(self, obj):
        language = get_requested_language(self)

        if language == "en":
            return obj.title

        translation = obj.translations.filter(
            language=language
        ).first()

        if translation:
            return translation.title

        return obj.title

    def get_summary(self, obj):
        language = get_requested_language(self)

        if language == "en":
            return obj.summary

        translation = obj.translations.filter(
            language=language
        ).first()

        if translation:
            return translation.summary

        return obj.summary


class SituationRightsTopicSerializer(
    serializers.ModelSerializer
):
    rights_topic = RightsTopicSerializer(
        read_only=True
    )

    class Meta:
        model = SituationRightsTopic
        fields = [
            "id",
            "rights_topic",
        ]


class SituationSerializer(serializers.ModelSerializer):
    rights_links = SituationRightsTopicSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Situation
        fields = [
            "id",
            "slug",
            "title",
            "description",
            "risk_level",
            "rights_links",
            "is_active",
        ]


class ConcernAnalysisRequestSerializer(
    serializers.Serializer
):
    concern = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
        max_length=2000,
    )
