import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.channels.voice import ivr

from .handler import handle_voice_request

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def voice_callback(request):
    session_id = request.POST.get("sessionId", "")
    phone_number = request.POST.get("phoneNumber", "")
    is_active = request.POST.get("isActive", "1")
    dtmf_digits = request.POST.get("dtmfDigits", "")
    recording_url = request.POST.get("recordingUrl", "")

    try:
        response_xml = handle_voice_request(
            session_id, phone_number, is_active, dtmf_digits, recording_url
        )
    except Exception:
        logger.exception("Unhandled error processing Voice request")
        response_xml = ivr.build_final_message_xml(
            "Sorry, something went wrong. Please try again."
        )

    return HttpResponse(response_xml, content_type="text/xml")
