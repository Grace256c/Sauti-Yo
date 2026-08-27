from rest_framework import generics

from .models import RightsTopic, Situation
from .serializers import (
    RightsTopicSerializer,
    SituationSerializer,
)


class SituationListAPIView(generics.ListAPIView):
    serializer_class = SituationSerializer

    def get_queryset(self):
        return (
            Situation.objects.filter(is_active=True)
            .prefetch_related(
                "rights_links__rights_topic__action_steps",
                "rights_links__rights_topic__safety_responses",
                "rights_links__rights_topic__support_services",
                "rights_links__rights_topic__legal_provisions",
            )
            .order_by("title")
        )


class SituationDetailAPIView(
    generics.RetrieveAPIView
):
    serializer_class = SituationSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Situation.objects.filter(is_active=True)
            .prefetch_related(
                "rights_links__rights_topic__action_steps",
                "rights_links__rights_topic__safety_responses",
                "rights_links__rights_topic__support_services",
                "rights_links__rights_topic__legal_provisions",
            )
        )


class RightsTopicListAPIView(
    generics.ListAPIView
):
    serializer_class = RightsTopicSerializer

    def get_queryset(self):
        return (
            RightsTopic.objects.filter(is_active=True)
            .prefetch_related(
                "action_steps",
                "safety_responses",
                "support_services",
                "legal_provisions",
            )
            .order_by("title")
        )


class RightsTopicDetailAPIView(
    generics.RetrieveAPIView
):
    serializer_class = RightsTopicSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (
            RightsTopic.objects.filter(is_active=True)
            .prefetch_related(
                "action_steps",
                "safety_responses",
                "support_services",
                "legal_provisions",
            )
        )