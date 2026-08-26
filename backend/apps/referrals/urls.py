from django.urls import path

from .views import (
    ReferralCreateAPIView,
    ReferralDetailAPIView,
    ReferralListAPIView,
    ReferralStatusUpdateAPIView,
)


urlpatterns = [
    path(
        "",
        ReferralListAPIView.as_view(),
        name="referral-list",
    ),

    path(
        "create/",
        ReferralCreateAPIView.as_view(),
        name="referral-create",
    ),

    path(
        "<int:pk>/",
        ReferralDetailAPIView.as_view(),
        name="referral-detail",
    ),

    path(
        "<int:pk>/status/",
        ReferralStatusUpdateAPIView.as_view(),
        name="referral-status-update",
    ),
]