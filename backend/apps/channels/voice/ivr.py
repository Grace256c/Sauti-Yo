from xml.sax.saxutils import escape, quoteattr

# NOTE: Africa's Talking's exact Voice XML attribute names/defaults
# (finishOnKey, maxLength, trimSilence, playBeep, timeout) should be
# double-checked against Africa's Talking's Voice API reference before
# this goes live against a real account - written here from the
# documented verb shapes, not verified against a live sandbox call.

GREETING_TEXT = (
    "Welcome to Sauti Yo. In your own words, briefly describe what's "
    "happening. When you're done, stay quiet for a moment, or press the "
    "pound key."
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


def build_greeting_xml():
    return _response(_say(GREETING_TEXT), _record())


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
