from rest_framework import serializers

from apps.support.serializers import (
    SupportServiceSerializer,
)

from .models import (
    ActionStep,
    IssueOutcome,
    RightsTopic,
    SafetyResponse,
    Situation,
    SituationRightsTopic,
)


class ActionStepSerializer(serializers.ModelSerializer):
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


class SafetyResponseSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = SafetyResponse
        fields = [
            "id",
            "trigger_key",
            "message",
            "is_active",
        ]


class RightsTopicSerializer(serializers.ModelSerializer):
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

    class Meta:
        model = RightsTopic
        fields = [
            "id",
            "slug",
            "title",
            "summary",
            "source_name",
            "source_url",
            "reviewed_by",
            "last_reviewed",
            "next_review_due",
            "verification_status",
            "support_services",
            "action_steps",
            "safety_responses",
            "is_active",
        ]


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

class IssueOutcomeSituationSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Situation
        fields = [
            "id",
            "slug",
            "title",
            "description",
            "risk_level",
        ]        

class IssueOutcomeSerializer(serializers.ModelSerializer):
    rights_topics = RightsTopicSerializer(
        many=True,
        read_only=True,
    )

    situation = IssueOutcomeSituationSerializer(
    read_only=True,
)

    class Meta:
        model = IssueOutcome
        fields = [
            "id",
            "category_slug",
            "issue_slug",
            "heading",
            "introduction",
            "evidence_items",
            "situation",
            "rights_topics",
            "is_active",
        ]        