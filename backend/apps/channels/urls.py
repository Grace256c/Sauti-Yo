from django.urls import path

from .sms.views import sms_callback
from .ussd.views import ussd_callback

urlpatterns = [
    path("ussd/", ussd_callback, name="ussd-callback"),
    path("sms/", sms_callback, name="sms-callback"),
]
