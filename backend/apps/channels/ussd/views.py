import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .handler import handle_ussd_request

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def ussd_callback(request):
    session_id = request.POST.get("sessionId", "")
    phone_number = request.POST.get("phoneNumber", "")
    text = request.POST.get("text", "")

    try:
        response_text = handle_ussd_request(session_id, phone_number, text)
    except Exception:
        logger.exception("Unhandled error processing USSD request")
        response_text = "END Sorry, something went wrong. Please try again."

    return HttpResponse(response_text, content_type="text/plain")
