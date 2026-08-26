from datetime import timedelta

from django.utils import timezone

from apps.channels.africastalking_client import send_sms
from apps.channels.models import SmsContext
from apps.channels.sms import keywords, templates
from apps.rights.services import get_situation_detail

FOLLOWUP_WINDOW_MINUTES = 10


def handle_sms_request(phone_number, text):
    if keywords.match_danger(text):
        detail = _live_context_detail(phone_number)
        send_sms(phone_number, templates.build_safety_reply(detail))
        return

    if keywords.match_help(text):
        send_sms(phone_number, templates.build_support_reply(None))
        return

    slug = keywords.match_situation(text)
    if slug:
        detail = get_situation_detail(slug)
        mode = "discreet" if keywords.match_discreet(text) else "normal"
        send_sms(phone_number, templates.build_situation_reply(detail, mode))
        SmsContext.objects.update_or_create(
            phone_number=phone_number,
            defaults={"last_situation_slug": slug},
        )
        return

    followup = keywords.match_followup(text)
    if followup:
        detail = _live_context_detail(phone_number)
        if detail is None:
            send_sms(phone_number, templates.build_followup_expired_reply())
            return
        if followup == "support":
            send_sms(phone_number, templates.build_support_reply(detail))
        else:
            send_sms(phone_number, templates.build_steps_reply(detail))
        return

    send_sms(phone_number, templates.build_unmatched_reply())


def _live_context_detail(phone_number):
    cutoff = timezone.now() - timedelta(minutes=FOLLOWUP_WINDOW_MINUTES)
    context = SmsContext.objects.filter(
        phone_number=phone_number, updated_at__gte=cutoff
    ).first()
    if context is None:
        return None
    return get_situation_detail(context.last_situation_slug)
