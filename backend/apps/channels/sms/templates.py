from apps.rights.services import get_channel_text, get_safety_message
from apps.support.models import SupportService

SMS_SEGMENT_BUDGET = 160

UNMATCHED_REPLY = (
    "You can text HOME, WORK, LAND or CHILD for help, or HELP for support."
)
FOLLOWUP_EXPIRED_REPLY = (
    "Please first text HOME, WORK, LAND or CHILD to tell us what's going "
    "on, then text STEPS or SUPPORT."
)
GENERAL_SAFETY_REPLY = (
    "If you are in immediate danger, call the Police on 999 or 112 now. "
    "Free support: Sauti 116."
)
NO_SUPPORT_SERVICES_REPLY = (
    "No support contacts are available right now. In an emergency, call "
    "the Police on 999 or 112."
)
NO_ACTION_STEPS_REPLY = (
    "No specific steps are available for this yet. Text SUPPORT for help "
    "contacts."
)


def _situation_intro(detail):
    text = get_channel_text(detail["slug"], "sms", "en")
    if text:
        return text
    return detail["description"] or detail["title"]


def _first_action_step(detail):
    for topic in detail["rights_topics"]:
        if topic["action_steps"]:
            return topic["action_steps"][0]["description"]
    return None


def _first_support_service(detail):
    for topic in detail["rights_topics"]:
        for service in topic["support_services"]:
            if service.get("phone_number"):
                return service
    return None


def build_situation_reply(detail, mode="normal"):
    intro = _situation_intro(detail)
    step = _first_action_step(detail)
    service = _first_support_service(detail)

    parts = [intro]
    if step:
        parts.append(f"Next step: {step}")
    if service:
        if mode == "discreet":
            parts.append(f"A support contact is available: {service['phone_number']}")
        else:
            parts.append(f"{service['name']}: {service['phone_number']}")

    return " ".join(parts)


def build_support_reply(detail=None):
    """
    Builds a support-contacts reply. If `detail` (from get_situation_detail)
    is given, uses that situation's linked support services; otherwise
    falls back to the general emergency-services list.
    """
    if detail is not None:
        services = []
        for topic in detail["rights_topics"]:
            services.extend(topic["support_services"])
    else:
        services = list(
            SupportService.objects.filter(
                is_emergency_service=True, is_active=True
            )
            .order_by("name")
            .values("name", "phone_number")
        )

    lines = [
        f"{s['name']}: {s['phone_number']}"
        for s in services
        if s.get("phone_number")
    ]
    return "\n".join(lines) if lines else NO_SUPPORT_SERVICES_REPLY


def build_safety_reply(detail=None, trigger_key="immediate_danger"):
    if detail is not None:
        message = get_safety_message(detail["slug"], trigger_key)
        if message:
            return message
    return GENERAL_SAFETY_REPLY


def build_steps_reply(detail):
    steps = []
    for topic in detail["rights_topics"]:
        steps.extend(topic["action_steps"])
    if not steps:
        return NO_ACTION_STEPS_REPLY
    lines = [f"{i + 1}. {step['description']}" for i, step in enumerate(steps)]
    return "\n".join(lines)


def build_unmatched_reply():
    return UNMATCHED_REPLY


def build_followup_expired_reply():
    return FOLLOWUP_EXPIRED_REPLY
