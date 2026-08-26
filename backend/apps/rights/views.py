from django.shortcuts import get_object_or_404

from rest_framework import generics

from .models import IssueOutcome, RightsTopic, Situation
from .serializers import (
    IssueOutcomeSerializer,
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
            )
        )


class IssueOutcomeDetailAPIView(
    generics.RetrieveAPIView
):
    serializer_class = IssueOutcomeSerializer

    def get_queryset(self):
        return (
            IssueOutcome.objects.filter(is_active=True)
            .select_related("situation")
            .prefetch_related(
                "rights_topics__action_steps",
                "rights_topics__safety_responses",
                "rights_topics__support_services",
            )
        )

    def get_object(self):
        queryset = self.get_queryset()

        return get_object_or_404(
            queryset,
            category_slug=self.kwargs["category_slug"],
            issue_slug=self.kwargs["issue_slug"],
        )