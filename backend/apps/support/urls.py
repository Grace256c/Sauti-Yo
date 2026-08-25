from django.urls import path

from .views import (
    SupportServiceDetailAPIView,
    SupportServiceListAPIView,
)

urlpatterns = [
    path(
        "",
        SupportServiceListAPIView.as_view(),
        name="support-service-list",
    ),
    path(
        "<int:pk>/",
        SupportServiceDetailAPIView.as_view(),
        name="support-service-detail",
    ),
]