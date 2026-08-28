import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .handler import handle_sms_request

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def sms_callback(request):
    phone_number = request.POST.get("from", "")
    text = request.POST.get("text", "")
    short_code = request.POST.get("to", "")
    link_id = request.POST.get("linkId", "")

    try:
        handle_sms_request(
            phone_number,
            text,
            short_code=short_code,
            link_id=link_id,
        )
    except Exception:
        logger.exception("Unhandled error processing SMS request")

    return HttpResponse(status=200)
