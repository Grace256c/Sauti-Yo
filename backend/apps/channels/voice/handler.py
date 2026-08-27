from django.core.cache import cache

from apps.channels.models import VoiceSession
from apps.channels.sms import ai_classifier, keywords, templates
from apps.channels.voice import ivr, transcription
from apps.channels.voice.sessions import (
    end_session,
    get_or_create_session,
    update_session,
)
from apps.rights.services import get_situation_detail

RATE_LIMIT_MAX_CALLS = 5
RATE_LIMIT_WINDOW_SECONDS = 60

MAX_RECORDING_ATTEMPTS = 2
MAX_SAFETY_CHECK_ATTEMPTS = 2


def _is_rate_limited(phone_number):
    """
    Simple in-memory rate limit (Django's default local-memory cache -
    single-process only, resets on restart), same pattern and reasoning
    as apps.channels.sms.handler._is_rate_limited: good enough to blunt
    basic webhook abuse at hackathon scale without needing Redis.
    """
    cache_key = f"voice_rate:{phone_number}"
    count = cache.get(cache_key, 0)
    if count >= RATE_LIMIT_MAX_CALLS:
        return True
    cache.set(cache_key, count + 1, timeout=RATE_LIMIT_WINDOW_SECONDS)
    return False


def _compose_reply(detail, mode):
    template_text = templates.build_situation_reply(detail, mode)
    if mode == "discreet":
        return template_text
    reworded = ai_classifier.reword_reply(template_text)
    return reworded or template_text


def handle_voice_request(session_id, phone_number, is_active, dtmf_digits, recording_url):
    if is_active == "0":
        VoiceSession.objects.filter(session_id=session_id, is_active=True).update(
            is_active=False, state="ended"
        )
        return ""

    if recording_url:
        return _handle_recording(session_id, phone_number, recording_url)

    if dtmf_digits:
        return _handle_digits(session_id, phone_number, dtmf_digits)

    existing = VoiceSession.objects.filter(
        session_id=session_id, is_active=True
    ).first()
    if existing is not None and existing.state in (
        "awaiting_safety_digit",
        "post_reply_menu",
    ):
        # A GetDigits timeout comes back from Africa's Talking with empty
        # dtmfDigits. Route it through digit handling with an empty digit
        # rather than falling through to a fresh greeting, which would
        # silently abandon a pending safety check-in (or post-reply menu)
        # and waste the rate-limit budget on repeated timeouts.
        return _handle_digits(session_id, phone_number, "")

    return _handle_call_start(session_id, phone_number)


def _handle_call_start(session_id, phone_number):
    if _is_rate_limited(phone_number):
        return ivr.build_closing_xml()

    get_or_create_session(session_id, phone_number)
    return ivr.build_greeting_xml()


def _handle_recording(session_id, phone_number, recording_url):
    session, _ = get_or_create_session(session_id, phone_number)

    transcript = transcription.transcribe_recording(recording_url)
    if not transcript:
        return _handle_unmatched(session)

    if keywords.match_danger(transcript):
        end_session(session)
        return ivr.build_final_message_xml(templates.build_safety_reply())

    discreet = keywords.match_discreet(transcript)
    slug = keywords.match_situation(transcript) or ai_classifier.classify_situation(
        transcript
    )
    if not slug:
        return _handle_unmatched(session)

    detail = get_situation_detail(slug)
    if detail is None:
        return _handle_unmatched(session)

    if detail["risk_level"] == "high_risk":
        update_session(
            session,
            state="awaiting_safety_digit",
            context={"slug": slug, "discreet": discreet},
        )
        return ivr.build_safety_checkin_xml(discreet)

    return _speak_situation_reply(session, slug, detail, discreet)


def _speak_situation_reply(session, slug, detail, discreet):
    mode = "discreet" if discreet else "normal"
    spoken_text = _compose_reply(detail, mode)
    update_session(
        session, state="post_reply_menu", context={"slug": slug, "discreet": discreet}
    )
    return ivr.build_reply_xml(spoken_text)


def _handle_unmatched(session):
    attempts = session.context.get("attempts", 0)
    if attempts >= MAX_RECORDING_ATTEMPTS - 1:
        end_session(session)
        return ivr.build_unmatched_xml(retry=False)
    update_session(session, context={"attempts": attempts + 1})
    return ivr.build_unmatched_xml(retry=True)


def _handle_digits(session_id, phone_number, dtmf_digits):
    session, _ = get_or_create_session(session_id, phone_number)

    if session.state == "awaiting_safety_digit":
        return _handle_safety_digit(session, dtmf_digits)

    if session.state == "post_reply_menu":
        return _handle_menu_digit(session, dtmf_digits)

    end_session(session)
    return ivr.build_closing_xml()


def _handle_safety_digit(session, digit):
    slug = session.context.get("slug")
    discreet = session.context.get("discreet", False)
    detail = get_situation_detail(slug)

    if digit == "1":
        if detail is None:
            end_session(session)
            return ivr.build_unmatched_xml(retry=False)
        return _speak_situation_reply(session, slug, detail, discreet)

    if digit == "2":
        end_session(session)
        return ivr.build_final_message_xml(templates.build_safety_reply(detail))

    # Anything other than an explicit "1" (safe) or "2" (not safe) - a
    # garbled DTMF tone, an off-menu digit, or a GetDigits timeout - must
    # never be treated as "safe" on a high-risk check-in. Give one bounded
    # re-prompt, then fail closed to the safety reply rather than silently
    # continuing to the ordinary situation reply.
    attempts = session.context.get("safety_check_attempts", 0)
    if attempts >= MAX_SAFETY_CHECK_ATTEMPTS - 1:
        end_session(session)
        return ivr.build_final_message_xml(templates.build_safety_reply(detail))

    update_session(
        session,
        context={**session.context, "safety_check_attempts": attempts + 1},
    )
    return ivr.build_safety_checkin_xml(discreet)


def _handle_menu_digit(session, digit):
    slug = session.context.get("slug")
    discreet = session.context.get("discreet", False)
    detail = get_situation_detail(slug)

    if detail is None:
        end_session(session)
        return ivr.build_unmatched_xml(retry=False)

    mode = "discreet" if discreet else "normal"

    if digit == "1":
        return ivr.build_reply_xml(templates.build_support_reply(detail, mode))

    if digit == "2":
        return ivr.build_reply_xml(_compose_reply(detail, mode))

    end_session(session)
    return ivr.build_closing_xml()
