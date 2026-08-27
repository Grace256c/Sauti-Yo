from django.urls import path

from .views import (
    ConcernAnalysisAPIView,
    RightsTopicDetailAPIView,
    RightsTopicListAPIView,
    SituationDetailAPIView,
    SituationListAPIView,
)

urlpatterns = [
    path(
        "analyse/",
        ConcernAnalysisAPIView.as_view(),
        name="concern-analysis",
    ),
    path(
        "situations/",
        SituationListAPIView.as_view(),
        name="situation-list",
    ),
    path(
        "situations/<slug:slug>/",
        SituationDetailAPIView.as_view(),
        name="situation-detail",
    ),
    path(
        "topics/",
        RightsTopicListAPIView.as_view(),
        name="rights-topic-list",
    ),
    path(
        "topics/<slug:slug>/",
        RightsTopicDetailAPIView.as_view(),
        name="rights-topic-detail",
    ),
]