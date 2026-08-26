from apps.content.models import ChannelContent

SCREEN_BUDGET = 160
PAGE_SIZE = 5
TITLE_TRUNCATE_LENGTH = 40

DEFAULT_COPY = {
    "ussd.welcome": "Welcome to Sauti Yo",
    "ussd.language_prompt": (
        "1. English\n2. Luganda\n3. Kiswahili\n4. Runyankole"
    ),
    "ussd.main_menu": "1. Find my rights\n2. Get help now\n0. Exit",
    "ussd.invalid_choice": "Invalid choice.",
    "ussd.too_many_invalid": (
        "Too many invalid attempts. Please dial again."
    ),
    "ussd.goodbye": "Thank you for using Sauti Yo.",
    "ussd.not_found": (
        "Sorry, that information is no longer available."
    ),
    "ussd.no_situations": "No situations are available right now.",
    "ussd.choose_situation": "Choose a situation:",
    "ussd.related_rights": "Related rights:",
    "ussd.topic_menu": "1. Action steps\n2. Support contacts\n0. Back",
    "ussd.safety_continue": "1. Continue\n0. Back",
    "ussd.no_action_steps": (
        "No action steps are available for this topic."
    ),
    "ussd.no_support_contacts": "No support contacts are available.",
    "ussd.no_emergency_contacts": (
        "No emergency contacts are available right now."
    ),
    "ussd.more": "More",
    "ussd.back": "Back",
    "ussd.next": "Next",
}


def get_copy(content_key, language):
    content = ChannelContent.objects.filter(
        content_key=content_key,
        language=language,
        channel="ussd",
        is_active=True,
    ).first()
    if content:
        return content.text
    return DEFAULT_COPY.get(content_key, "")


def truncate(text, limit):
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def chunk_text(text, budget=SCREEN_BUDGET):
    words = text.split()
    chunks = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > budget:
            if current:
                chunks.append(current)
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks or [""]


def paginate_items(items, page, page_size=PAGE_SIZE):
    start = page * page_size
    end = start + page_size
    page_items = items[start:end]
    has_more = end < len(items)
    return page_items, has_more


def render_language_select(session):
    body = get_copy("ussd.welcome", session.language)
    prompt = get_copy("ussd.language_prompt", session.language)
    return f"{body}\n{prompt}", False


def transition_language_select(session, user_input):
    mapping = {"1": "en", "2": "lg", "3": "sw", "4": "nyn"}
    language = mapping.get(user_input)
    if language is None:
        return None
    session.language = language
    return "main_menu", {}


def render_main_menu(session):
    return get_copy("ussd.main_menu", session.language), False


def transition_main_menu(session, user_input):
    if user_input == "1":
        return "situation_list", {"page": 0}
    if user_input == "2":
        return "emergency_list", {"chunk_index": 0}
    if user_input == "0":
        return "goodbye", {}
    return None


def render_goodbye(session):
    return get_copy("ussd.goodbye", session.language), True
