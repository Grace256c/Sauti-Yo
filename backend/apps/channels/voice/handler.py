from django.core.cache import cache

from apps.channels.models import VoiceSession
from apps.channels.sms import ai_classifier, keywords, templates
from apps.channels.voice import ivr, transcription
from apps.channels.voice.sessions import (
    end_session,
    get_or_create_session,
    update_session,
)
from apps.rights.models import RightsTopic, Situation
from apps.rights.services import get_situation_detail
from apps.support.models import SupportService

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


def _primary_support_phone_number(detail):
    if detail is not None:
        for topic in detail["rights_topics"]:
            for service in topic["support_services"]:
                if service.get("phone_number"):
                    return service["phone_number"]
        return None
    return _general_emergency_phone_number()


def _general_emergency_phone_number():
    service = (
        SupportService.objects.filter(is_emergency_service=True, is_active=True)
        .order_by("name")
        .values("phone_number")
        .first()
    )
    return service["phone_number"] if service else None


def _crisis_support_phone_number(detail):
    # Unlike _primary_support_phone_number (used by the post-reply menu's
    # "connect me" option, which must never misdirect a non-crisis caller
    # toward the general emergency/GBV line just because their situation
    # has no linked number - see apps.channels.sms.templates.build_support_reply
    # for the same no-fallback rule on that side), the crisis-connect path
    # is explicitly allowed to fall back: once we're already offering "press
    # 1 to connect" after a danger-word/safety-check-in crisis signal, any
    # reachable emergency number is better than none.
    return _primary_support_phone_number(detail) or _general_emergency_phone_number()


def _offer_crisis_connect(session, detail):
    safety_text = templates.build_safety_reply(detail)
    if _crisis_support_phone_number(detail) is None:
        # Nothing dialable exists for this situation, even after falling
        # back to the general emergency list - don't promise a connection
        # the call can't deliver. Fall back to the old speak-and-end
        # behavior instead of offering a "press 1" that would go nowhere.
        end_session(session)
        return ivr.build_final_message_xml(safety_text)
    update_session(
        session,
        state="awaiting_crisis_connect_digit",
        context={"slug": detail["slug"] if detail is not None else None},
    )
    return ivr.build_safety_reply_with_connect_xml(safety_text)


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
    if existing is not None:
        if existing.state in (
            "language_select",
            "main_menu",
            "emergency_list",
            "situation_list",
            "rights_list",
            "topic_detail",
            "action_steps",
            "support_contacts",
            "awaiting_safety_digit",
            "post_reply_menu",
            "awaiting_crisis_connect_digit",
        ):
            # A GetDigits timeout comes back from Africa's Talking with empty
            # dtmfDigits. Route it through digit handling with an empty digit
            # rather than falling through to a fresh greeting, which would
            # silently abandon a pending safety check-in, post-reply menu, or
            # crisis-connect offer, and waste the rate-limit budget on
            # repeated timeouts.
            return _handle_digits(session_id, phone_number, "")
        if existing.state == "awaiting_recording":
            # Africa's Talking can call back with recordingUrl="" (not
            # absent) when a <Record> captured silence or no audio - falsy
            # either way, so this and a genuinely missing recordingUrl both
            # land here. Treat it exactly like a failed/empty transcription
            # rather than re-greeting a session that's already past the
            # greeting and burning its rate-limit budget on a repeat.
            return _handle_unmatched(existing)

    return _handle_call_start(session_id, phone_number)


def _handle_call_start(session_id, phone_number):
    if _is_rate_limited(phone_number):
        return ivr.build_closing_xml()

    session, _ = get_or_create_session(session_id, phone_number)
    update_session(session, state="language_select", context={})
    return ivr.build_language_menu_xml()


def _handle_recording(session_id, phone_number, recording_url):
    session, _ = get_or_create_session(session_id, phone_number)

    transcript = transcription.transcribe_recording(recording_url)
    if not transcript:
        return _handle_unmatched(session)

    if keywords.match_danger(transcript):
        return _offer_crisis_connect(session, None)

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

    if session.state == "language_select":
        return _handle_language_digit(session, dtmf_digits)

    if session.state == "main_menu":
        return _handle_main_menu_digit(session, dtmf_digits)

    if session.state == "emergency_list":
        return _handle_emergency_digit(session, dtmf_digits)

    if session.state == "situation_list":
        return _handle_situation_digit(session, dtmf_digits)

    if session.state == "rights_list":
        return _handle_rights_digit(session, dtmf_digits)

    if session.state == "topic_detail":
        return _handle_topic_digit(session, dtmf_digits)

    if session.state == "action_steps":
        return _handle_action_steps_digit(session, dtmf_digits)

    if session.state == "support_contacts":
        return _handle_support_contacts_digit(session, dtmf_digits)

    if session.state == "awaiting_safety_digit":
        return _handle_safety_digit(session, dtmf_digits)

    if session.state == "post_reply_menu":
        return _handle_menu_digit(session, dtmf_digits)

    if session.state == "awaiting_crisis_connect_digit":
        return _handle_crisis_connect_digit(session, dtmf_digits)

    end_session(session)
    return ivr.build_closing_xml()


def _handle_language_digit(session, digit):
    languages = {
        "1": "en",
        "2": "lg",
        "3": "sw",
        "4": "nyn",
    }

    if digit == "0":
        end_session(session)
        return ivr.build_closing_xml()

    language = languages.get(digit)
    if language is None:
        return ivr.build_language_menu_xml()

    update_session(
        session,
        state="main_menu",
        context={"language": language},
    )
    return ivr.build_main_menu_xml()


def _handle_main_menu_digit(session, digit):
    if digit == "0":
        end_session(session)
        return ivr.build_closing_xml()

    if digit == "1":
        language = session.context.get("language", "en")
        update_session(
            session,
            state="situation_list",
            context={"language": language, "page": 0},
        )
        return _build_situation_menu(session)

    if digit == "2":
        language = session.context.get("language", "en")
        update_session(
            session,
            state="emergency_list",
            context={"language": language},
        )
        return _build_emergency_menu()

    return ivr.build_main_menu_xml()


def _emergency_services():
    return list(
        SupportService.objects.filter(
            is_emergency_service=True,
            is_active=True,
        ).order_by("name")
    )


def _build_emergency_menu():
    return ivr.build_emergency_contacts_xml(_emergency_services())


def _handle_emergency_digit(session, digit):
    language = session.context.get("language", "en")

    if digit == "0":
        end_session(session)
        return ivr.build_closing_xml()

    if digit == "9":
        update_session(
            session,
            state="main_menu",
            context={"language": language},
        )
        return ivr.build_main_menu_xml()

    return _build_emergency_menu()


VOICE_SITUATIONS_PER_PAGE = 7


def _situation_page(session):
    situations = list(
        Situation.objects.filter(is_active=True).order_by("title")
    )

    start = session.context.get("page", 0)
    shown = situations[start:start + VOICE_SITUATIONS_PER_PAGE]
    has_more = start + VOICE_SITUATIONS_PER_PAGE < len(situations)

    return shown, has_more


def _build_situation_menu(session):
    shown, has_more = _situation_page(session)
    return ivr.build_situation_menu_xml(shown, has_more=has_more)


def _handle_situation_digit(session, digit):
    language = session.context.get("language", "en")
    page = session.context.get("page", 0)
    shown, has_more = _situation_page(session)

    if digit == "0":
        end_session(session)
        return ivr.build_closing_xml()

    if digit == "9":
        update_session(
            session,
            state="main_menu",
            context={"language": language},
        )
        return ivr.build_main_menu_xml()

    if digit == "8" and has_more:
        update_session(
            session,
            state="situation_list",
            context={
                "language": language,
                "page": page + VOICE_SITUATIONS_PER_PAGE,
            },
        )
        return _build_situation_menu(session)

    if digit.isdigit():
        choice = int(digit)
        if 1 <= choice <= len(shown):
            situation = shown[choice - 1]

            topics = list(
                RightsTopic.objects.filter(
                    situation_links__situation=situation,
                    is_active=True,
                )
                .order_by("title")
                .distinct()[:9]
            )

            # Match the USSD behaviour: when only one related right exists,
            # enter it directly instead of forcing another menu.
            if len(topics) == 1:
                topic = topics[0]
                update_session(
                    session,
                    state="topic_detail",
                    context={
                        "language": language,
                        "page": page,
                        "situation_slug": situation.slug,
                        "topic_slug": topic.slug,
                    },
                )
                return ivr.build_topic_detail_xml(topic)

            update_session(
                session,
                state="rights_list",
                context={
                    "language": language,
                    "page": page,
                    "situation_slug": situation.slug,
                },
            )
            return ivr.build_rights_menu_xml(topics)

    return _build_situation_menu(session)


def _topics_for_voice_situation(situation_slug):
    return list(
        RightsTopic.objects.filter(
            situation_links__situation__slug=situation_slug,
            situation_links__situation__is_active=True,
            is_active=True,
        )
        .order_by("title")
        .distinct()[:9]
    )


def _handle_rights_digit(session, digit):
    language = session.context.get("language", "en")
    situation_slug = session.context.get("situation_slug")
    page = session.context.get("page", 0)
    topics = _topics_for_voice_situation(situation_slug)

    if digit == "0":
        end_session(session)
        return ivr.build_closing_xml()

    if digit == "9":
        update_session(
            session,
            state="situation_list",
            context={"language": language, "page": page},
        )
        return _build_situation_menu(session)

    if digit.isdigit():
        choice = int(digit)
        if 1 <= choice <= len(topics):
            topic = topics[choice - 1]
            update_session(
                session,
                state="topic_detail",
                context={
                    "language": language,
                    "page": page,
                    "situation_slug": situation_slug,
                    "topic_slug": topic.slug,
                },
            )
            return ivr.build_topic_detail_xml(topic)

    return ivr.build_rights_menu_xml(topics)


def _handle_topic_digit(session, digit):
    language = session.context.get("language", "en")
    situation_slug = session.context.get("situation_slug")
    topic_slug = session.context.get("topic_slug")
    page = session.context.get("page", 0)

    topic = RightsTopic.objects.filter(
        slug=topic_slug,
        is_active=True,
    ).first()

    if topic is None:
        update_session(
            session,
            state="situation_list",
            context={"language": language, "page": page},
        )
        return _build_situation_menu(session)

    if digit == "0":
        end_session(session)
        return ivr.build_closing_xml()

    if digit == "9":
        topics = _topics_for_voice_situation(situation_slug)

        if len(topics) <= 1:
            update_session(
                session,
                state="situation_list",
                context={"language": language, "page": page},
            )
            return _build_situation_menu(session)

        update_session(
            session,
            state="rights_list",
            context={
                "language": language,
                "page": page,
                "situation_slug": situation_slug,
            },
        )
        return ivr.build_rights_menu_xml(topics)

    if digit == "1":
        update_session(
            session,
            state="action_steps",
            context={
                "language": language,
                "page": page,
                "situation_slug": situation_slug,
                "topic_slug": topic_slug,
            },
        )
        return ivr.build_action_steps_xml(topic)

    if digit == "2":
        update_session(
            session,
            state="support_contacts",
            context={
                "language": language,
                "page": page,
                "situation_slug": situation_slug,
                "topic_slug": topic_slug,
            },
        )
        return ivr.build_support_contacts_xml(topic)

    return ivr.build_topic_detail_xml(topic)


def _topic_from_voice_session(session):
    return RightsTopic.objects.filter(
        slug=session.context.get("topic_slug"),
        is_active=True,
    ).first()


def _return_to_voice_topic(session):
    topic = _topic_from_voice_session(session)

    if topic is None:
        language = session.context.get("language", "en")
        page = session.context.get("page", 0)
        update_session(
            session,
            state="situation_list",
            context={"language": language, "page": page},
        )
        return _build_situation_menu(session)

    update_session(
        session,
        state="topic_detail",
        context=dict(session.context),
    )
    return ivr.build_topic_detail_xml(topic)


def _handle_action_steps_digit(session, digit):
    if digit == "0":
        end_session(session)
        return ivr.build_closing_xml()

    if digit == "9":
        return _return_to_voice_topic(session)

    topic = _topic_from_voice_session(session)
    if topic is None:
        return _return_to_voice_topic(session)

    return ivr.build_action_steps_xml(topic)


def _handle_support_contacts_digit(session, digit):
    if digit == "0":
        end_session(session)
        return ivr.build_closing_xml()

    if digit == "9":
        return _return_to_voice_topic(session)

    topic = _topic_from_voice_session(session)
    if topic is None:
        return _return_to_voice_topic(session)

    return ivr.build_support_contacts_xml(topic)


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
        return _offer_crisis_connect(session, detail)

    # Anything other than an explicit "1" (safe) or "2" (not safe) - a
    # garbled DTMF tone, an off-menu digit, or a GetDigits timeout - must
    # never be treated as "safe" on a high-risk check-in. Give one bounded
    # re-prompt, then fail closed to the safety reply rather than silently
    # continuing to the ordinary situation reply.
    attempts = session.context.get("safety_check_attempts", 0)
    if attempts >= MAX_SAFETY_CHECK_ATTEMPTS - 1:
        return _offer_crisis_connect(session, detail)

    update_session(
        session,
        context={**session.context, "safety_check_attempts": attempts + 1},
    )
    return ivr.build_safety_checkin_xml(discreet)


def _handle_crisis_connect_digit(session, digit):
    slug = session.context.get("slug")
    detail = get_situation_detail(slug) if slug else None

    if digit == "1":
        phone = _crisis_support_phone_number(detail)
        end_session(session)
        return ivr.build_dial_xml(phone) if phone else ivr.build_closing_xml()

    end_session(session)
    return ivr.build_closing_xml()


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

    if digit == "3":
        phone = _primary_support_phone_number(detail)
        if phone:
            end_session(session)
            return ivr.build_dial_xml(phone)
        return ivr.build_reply_xml(templates.build_support_reply(detail, mode))

    end_session(session)
    return ivr.build_closing_xml()
