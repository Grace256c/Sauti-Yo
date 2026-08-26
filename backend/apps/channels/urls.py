from django.urls import path

from .ussd.views import ussd_callback

urlpatterns = [
    path("ussd/", ussd_callback, name="ussd-callback"),
]
