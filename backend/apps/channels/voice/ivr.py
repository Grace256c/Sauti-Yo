from xml.sax.saxutils import escape, quoteattr

# NOTE: Africa's Talking's exact Voice XML attribute names/defaults
# (finishOnKey, maxLength, trimSilence, playBeep, timeout) should be
# double-checked against Africa's Talking's Voice API reference before
# this goes live against a real account - written here from the
# documented verb shapes, not verified against a live sandbox call.

LANGUAGE_PROMPT = (
    "Welcome to Sauti Yo. "
    "Choose your language. "
    "Press 1 for English. "
    "Press 2 for Luganda. "
    "Press 3 for Kiswahili. "
    "Press 4 for Runyankole. "
    "Press 0 to exit."
)

MAIN_MENU_PROMPT = (
    "Main menu. "
    "Press 1 to find your rights. "
    "Press 2 to get help now. "
    "Press 0 to exit."
)

SAFETY_CHECKIN_PROMPT = (
    "Are you safe right now? Press 1 if you are safe. "
    "Press 2 if you are not."
)
DISCREET_SAFETY_CHECKIN_PROMPT = (
    "Press 1 to continue. Press 2 if you need help now."
)

POST_REPLY_MENU_PROMPT = (
    "To hear support contacts, press 1. To hear that again, press 2. "
    "To be connected now, press 3. To end this call, press 0."
)

CRISIS_CONNECT_PROMPT = (
    "Press 1 to connect to that support line now. Stay on the line to "
    "end the call."
)

CONNECT_FAILED_TEXT_TEMPLATE = (
    "That number isn't answering right now. You can reach them "
    "directly at {phone_number}."
)

RETRY_PROMPT = (
    "Sorry, I didn't catch that. Please describe what's happening after "
    "the beep."
)
GIVE_UP_TEXT = (
    "I'm sorry, I still couldn't understand. Please call back, or send "
    "a text instead. Goodbye."
)
CLOSING_TEXT = "Thank you for calling Sauti Yo. Take care."


def _say(text):
    return f"<Say>{escape(text)}</Say>"


def _record():
    return (
        '<Record trimSilence="true" maxLength="120" finishOnKey="#" '
        'playBeep="true"/>'
    )


def _get_digits(prompt, num_digits=1, timeout=10):
    return (
        f'<GetDigits timeout="{timeout}" numDigits="{num_digits}">'
        f"{_say(prompt)}"
        "</GetDigits>"
    )


def _dial(phone_number):
    return (
        f"<Dial phoneNumbers={quoteattr(phone_number)} record=\"false\" "
        'maxDuration="300"/>'
    )


def _response(*fragments):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>" + "".join(fragments) + "</Response>"
    )


def build_language_menu_xml():
    return _response(_get_digits(LANGUAGE_PROMPT, num_digits=1))


def build_main_menu_xml():
    return _response(_get_digits(MAIN_MENU_PROMPT, num_digits=1))


def build_rights_menu_xml(topics):
    if not topics:
        prompt = (
            "No related rights are available for this situation. "
            "Press 9 to go back. Press 0 to exit."
        )
        return _response(_get_digits(prompt, num_digits=1))

    parts = ["Related rights."]

    for number, topic in enumerate(topics, start=1):
        parts.append(f"Press {number} for {topic.title}.")

    parts.append("Press 9 to go back.")
    parts.append("Press 0 to exit.")

    return _response(_get_digits(" ".join(parts), num_digits=1))


def build_emergency_contacts_xml(services):
    if not services:
        text = "No emergency contacts are available right now."
    else:
        parts = ["Get help now."]
        for service in services:
            phone = (
                service.phone_number
                or service.alternate_phone_number
                or "number unavailable"
            )

            detail = service.name
            if service.availability:
                detail += f". Available {service.availability}"
            detail += f". Phone {phone}."

            parts.append(detail)

        text = " ".join(parts)

    prompt = (
        f"{text} "
        "Press 9 to return to the main menu. "
        "Press 0 to exit."
    )

    return _response(_get_digits(prompt, num_digits=1))


def build_action_steps_xml(topic):
    steps = list(
        topic.action_steps.filter(is_active=True).order_by("order", "id")
    )

    if not steps:
        text = "No action steps are available for this topic."
    else:
        parts = ["Here are the action steps."]
        for number, step in enumerate(steps, start=1):
            parts.append(
                f"Step {number}. {step.title}. {step.description}"
            )
        text = " ".join(parts)

    prompt = (
        f"{text} "
        "Press 9 to go back to this right. "
        "Press 0 to exit."
    )
    return _response(_get_digits(prompt, num_digits=1))


def build_support_contacts_xml(topic):
    services = list(
        topic.support_services.filter(is_active=True).order_by("name")
    )

    if not services:
        text = "No support contacts are available for this topic."
    else:
        parts = ["Here are the support contacts."]
        for service in services:
            phone = (
                service.phone_number
                or service.alternate_phone_number
                or "number unavailable"
            )
            parts.append(f"{service.name}. Phone {phone}.")
        text = " ".join(parts)

    prompt = (
        f"{text} "
        "Press 9 to go back to this right. "
        "Press 0 to exit."
    )
    return _response(_get_digits(prompt, num_digits=1))


def build_topic_detail_xml(topic):
    text = topic.summary or topic.title
    prompt = (
        f"{text} "
        "Press 1 for action steps. "
        "Press 2 for support contacts. "
        "Press 9 to go back. "
        "Press 0 to exit."
    )
    return _response(_get_digits(prompt, num_digits=1))


def build_situation_menu_xml(situations, has_more=False):
    if not situations:
        prompt = (
            "No situations are available right now. "
            "Press 9 to go back. Press 0 to exit."
        )
        return _response(_get_digits(prompt, num_digits=1))

    parts = ["Choose a situation."]

    for number, situation in enumerate(situations, start=1):
        parts.append(f"Press {number} for {situation.title}.")

    if has_more:
        parts.append("Press 8 for more.")

    parts.append("Press 9 to go back.")
    parts.append("Press 0 to exit.")

    return _response(_get_digits(" ".join(parts), num_digits=1))




def build_safety_checkin_xml(discreet):
    prompt = (
        DISCREET_SAFETY_CHECKIN_PROMPT if discreet else SAFETY_CHECKIN_PROMPT
    )
    return _response(_get_digits(prompt, num_digits=1))


def build_reply_xml(spoken_text):
    return _response(
        _say(spoken_text), _get_digits(POST_REPLY_MENU_PROMPT, num_digits=1)
    )


def build_safety_reply_with_connect_xml(safety_text):
    return _response(
        _say(safety_text), _get_digits(CRISIS_CONNECT_PROMPT, num_digits=1)
    )


def build_dial_xml(phone_number):
    fallback_text = CONNECT_FAILED_TEXT_TEMPLATE.format(
        phone_number=phone_number
    )
    return _response(_dial(phone_number), _say(fallback_text))


def build_unmatched_xml(retry):
    if retry:
        return _response(_say(RETRY_PROMPT), _record())
    return build_final_message_xml(GIVE_UP_TEXT)


def build_final_message_xml(spoken_text):
    return _response(_say(spoken_text))


def build_closing_xml():
    return build_final_message_xml(CLOSING_TEXT)
