from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import RightsTopic, Situation
from .serializers import (
    ConcernAnalysisRequestSerializer,
    RightsTopicSerializer,
    SituationSerializer,
)
from .services import analyse_concern


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


class ConcernAnalysisAPIView(APIView):
    """
    Public free-text concern analysis endpoint.

    The endpoint only returns legal information already stored in the
    Rights-to-Action knowledge base. It does not generate legal facts.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ConcernAnalysisRequestSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        result = analyse_concern(
            serializer.validated_data["concern"],
        )

        if result is None:
            return Response(
                {
                    "matched": False,
                    "detail": (
                        "We could not confidently match this "
                        "concern to the currently supported "
                        "rights situations."
                    ),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "matched": True,
                **result,
            },
            status=status.HTTP_200_OK,
        )
