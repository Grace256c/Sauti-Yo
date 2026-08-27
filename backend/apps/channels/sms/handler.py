from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone

from apps.channels.africastalking_client import send_sms
from apps.channels.models import SmsContext
from apps.channels.sms import ai_classifier, keywords, templates
from apps.rights.services import get_situation_detail

FOLLOWUP_WINDOW_MINUTES = 10

MAX_SMS_LENGTH = templates.SMS_SEGMENT_BUDGET * 2

RATE_LIMIT_MAX_MESSAGES = 5
RATE_LIMIT_WINDOW_SECONDS = 60


def _is_rate_limited(phone_number):
    """
    Simple in-memory rate limit (Django's default local-memory cache -
    single-process only, resets on restart). Good enough to blunt basic
    webhook abuse at hackathon scale; a distributed limiter needs Redis,
    which this project deliberately doesn't run.
    """
    cache_key = f"sms_rate:{phone_number}"
    count = cache.get(cache_key, 0)
    if count >= RATE_LIMIT_MAX_MESSAGES:
        return True
    cache.set(cache_key, count + 1, timeout=RATE_LIMIT_WINDOW_SECONDS)
    return False


def _send(phone_number, message):
    if len(message) > MAX_SMS_LENGTH:
        message = message[: MAX_SMS_LENGTH - 3].rstrip() + "..."
    send_sms(phone_number, message)


def _compose_situation_reply(detail, mode):
    template_text = templates.build_situation_reply(detail, mode)
    if mode == "discreet":
        return template_text
    reworded = ai_classifier.reword_reply(template_text)
    if reworded and len(reworded) <= MAX_SMS_LENGTH:
        return reworded
    return template_text


def _clear_pending_safety_check(phone_number):
    SmsContext.objects.filter(
        phone_number=phone_number, pending_safety_check=True
    ).update(pending_safety_check=False)


def _resolve_pending_safety_check(phone_number, slug, discreet):
    """
    Marks a pending safety check-in as resolved AND refreshes updated_at
    (via update_or_create, not a bare queryset .update()), so the
    follow-up window restarts from when the check-in was actually
    answered rather than from when the question was originally sent -
    otherwise a slow-to-reply high-risk user could have their follow-up
    window silently eaten by however long they took to answer.
    """
    SmsContext.objects.update_or_create(
        phone_number=phone_number,
        defaults={
            "last_situation_slug": slug,
            "discreet": discreet,
            "pending_safety_check": False,
        },
    )


def _reply_to_situation(phone_number, slug, text):
    detail = get_situation_detail(slug)
    if detail is None:
        _send(phone_number, templates.build_unmatched_reply())
        return
    discreet = keywords.match_discreet(text)

    existing = _live_context(phone_number)
    is_new_topic = existing is None or existing.last_situation_slug != slug

    if is_new_topic and detail["risk_level"] == "high_risk":
        checkin_question = (
            templates.DISCREET_SAFETY_CHECKIN_QUESTION
            if discreet
            else templates.SAFETY_CHECKIN_QUESTION
        )
        _send(phone_number, checkin_question)
        SmsContext.objects.update_or_create(
            phone_number=phone_number,
            defaults={
                "last_situation_slug": slug,
                "discreet": discreet,
                "pending_safety_check": True,
            },
        )
        return

    mode = "discreet" if discreet else "normal"
    _send(phone_number, _compose_situation_reply(detail, mode))
    SmsContext.objects.update_or_create(
        phone_number=phone_number,
        defaults={
            "last_situation_slug": slug,
            "discreet": discreet,
            "pending_safety_check": False,
        },
    )


def handle_sms_request(phone_number, text):
    if _is_rate_limited(phone_number):
        return

    if keywords.match_danger(text):
        detail = _live_context_detail(phone_number)
        _send(phone_number, templates.build_safety_reply(detail))
        _clear_pending_safety_check(phone_number)
        return

    pending = _live_context(phone_number)
    if pending is not None and pending.pending_safety_check:
        if keywords.match_not_safe_answer(text):
            detail = get_situation_detail(pending.last_situation_slug)
            _send(phone_number, templates.build_safety_reply(detail))
            _resolve_pending_safety_check(
                phone_number, pending.last_situation_slug, pending.discreet
            )
            return

    if keywords.match_help(text):
        _send(phone_number, templates.build_support_reply(None))
        return

    slug = keywords.match_situation(text)
    if slug:
        _reply_to_situation(phone_number, slug, text)
        return

    followup = keywords.match_followup(text)
    if followup:
        context = _live_context(phone_number)
        if context is None:
            _send(phone_number, templates.build_followup_expired_reply())
            return
        detail = get_situation_detail(context.last_situation_slug)
        if detail is None:
            _send(phone_number, templates.build_followup_expired_reply())
            return
        mode = "discreet" if context.discreet else "normal"
        if followup == "support":
            _send(phone_number, templates.build_support_reply(detail, mode))
        else:
            _send(phone_number, templates.build_steps_reply(detail, mode))
        return

    slug = ai_classifier.classify_situation(text)
    if slug:
        _reply_to_situation(phone_number, slug, text)
        return

    pending = _live_context(phone_number)
    if pending is not None and pending.pending_safety_check:
        detail = get_situation_detail(pending.last_situation_slug)
        if detail is None:
            _clear_pending_safety_check(phone_number)
            _send(phone_number, templates.build_unmatched_reply())
            return
        mode = "discreet" if pending.discreet else "normal"
        _send(phone_number, _compose_situation_reply(detail, mode))
        _resolve_pending_safety_check(
            phone_number, pending.last_situation_slug, pending.discreet
        )
        return

    _send(phone_number, templates.build_unmatched_reply())


def _live_context(phone_number):
    cutoff = timezone.now() - timedelta(minutes=FOLLOWUP_WINDOW_MINUTES)
    context = SmsContext.objects.filter(phone_number=phone_number).first()
    if context is None:
        return None
    if context.updated_at < cutoff:
        context.delete()
        return None
    return context


def _live_context_detail(phone_number):
    context = _live_context(phone_number)
    if context is None:
        return None
    return get_situation_detail(context.last_situation_slug)
