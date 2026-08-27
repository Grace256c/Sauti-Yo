from django.urls import path

from .sms.views import sms_callback
from .ussd.views import ussd_callback
from .voice.views import voice_callback

urlpatterns = [
    path("ussd/", ussd_callback, name="ussd-callback"),
    path("sms/", sms_callback, name="sms-callback"),
    path("voice/", voice_callback, name="voice-callback"),
]
