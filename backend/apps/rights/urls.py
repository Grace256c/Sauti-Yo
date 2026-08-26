from django.urls import path

from .views import (
    IssueOutcomeDetailAPIView,
    RightsTopicDetailAPIView,
    RightsTopicListAPIView,
    SituationDetailAPIView,
    SituationListAPIView,
)

urlpatterns = [
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

    path(
    "outcomes/<slug:category_slug>/<slug:issue_slug>/",
    IssueOutcomeDetailAPIView.as_view(),
    name="issue-outcome-detail",
),
]