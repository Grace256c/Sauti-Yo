from django.urls import path

from .views import (
    CSRFTokenAPIView,
    PartnerLoginAPIView,
    PartnerLogoutAPIView,
    PartnerSessionAPIView,
)


urlpatterns = [
    path(
        "csrf/",
        CSRFTokenAPIView.as_view(),
        name="csrf-token",
    ),
    path(
        "login/",
        PartnerLoginAPIView.as_view(),
        name="partner-login",
    ),
    path(
        "logout/",
        PartnerLogoutAPIView.as_view(),
        name="partner-logout",
    ),
    path(
        "session/",
        PartnerSessionAPIView.as_view(),
        name="partner-session",
    ),
]
