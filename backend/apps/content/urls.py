from django.urls import path

from .views import (
    ChannelContentDetailAPIView,
    ChannelContentListAPIView,
)

urlpatterns = [
    path(
        "",
        ChannelContentListAPIView.as_view(),
        name="channel-content-list",
    ),
    path(
        "<int:pk>/",
        ChannelContentDetailAPIView.as_view(),
        name="channel-content-detail",
    ),
]