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


from apps.rights.models import RightsTopic, Situation


def _topics_for_situation(situation):
    return (
        RightsTopic.objects.filter(
            situation_links__situation=situation,
            is_active=True,
        )
        .order_by("title")
        .distinct()
    )


def _enter_topic(situation_slug, topic):
    context = {
        "situation_slug": situation_slug,
        "topic_slug": topic.slug,
        "chunk_index": 0,
    }
    if getattr(topic, "risk_level", "standard") in ("sensitive", "high_risk"):
        safety = topic.safety_responses.filter(
            trigger_key="default", is_active=True
        ).first()
        if safety is not None:
            return "safety_gate", context
    return "topic_detail", context


def _chunked_screen(text, chunk_index, trailing_options, language):
    chunks = chunk_text(text) if text else [""]
    chunk_index = max(0, min(chunk_index, len(chunks) - 1))
    body = chunks[chunk_index]
    is_last = chunk_index == len(chunks) - 1
    if is_last:
        screen = f"{body}\n\n{trailing_options}" if trailing_options else body
    else:
        more = get_copy("ussd.more", language)
        back = get_copy("ussd.back", language)
        screen = f"{body}\n\n1. {more}\n0. {back}"
    return screen, is_last


def _is_last_chunk(text, chunk_index):
    chunks = chunk_text(text) if text else [""]
    return max(0, min(chunk_index, len(chunks) - 1)) == len(chunks) - 1


def render_situation_list(session):
    situations = list(
        Situation.objects.filter(is_active=True).order_by("title")
    )
    page = session.context.get("page", 0)
    page_items, has_more = paginate_items(situations, page, PAGE_SIZE)
    back = get_copy("ussd.back", session.language)

    if not page_items:
        body = get_copy("ussd.no_situations", session.language)
        return f"{body}\n\n0. {back}", False

    lines = [get_copy("ussd.choose_situation", session.language)]
    for index, situation in enumerate(page_items, start=1):
        lines.append(f"{index}. {truncate(situation.title, TITLE_TRUNCATE_LENGTH)}")
    if has_more:
        lines.append(f"8. {get_copy('ussd.more', session.language)}")
    lines.append(f"0. {back}")
    return "\n".join(lines), False


def transition_situation_list(session, user_input):
    situations = list(
        Situation.objects.filter(is_active=True).order_by("title")
    )
    page = session.context.get("page", 0)
    page_items, has_more = paginate_items(situations, page, PAGE_SIZE)

    if user_input == "0":
        return "main_menu", {}
    if user_input == "8" and has_more:
        return "situation_list", {"page": page + 1}
    if user_input.isdigit():
        choice = int(user_input)
        if 1 <= choice <= len(page_items):
            situation = page_items[choice - 1]
            topics = list(_topics_for_situation(situation)[:9])
            if len(topics) == 1:
                return _enter_topic(situation.slug, topics[0])
            return (
                "situation_detail",
                {"situation_slug": situation.slug, "chunk_index": 0},
            )
    return None


def render_situation_detail(session):
    situation = Situation.objects.filter(
        slug=session.context.get("situation_slug"), is_active=True
    ).first()
    if situation is None:
        return get_copy("ussd.not_found", session.language), False

    topics = list(_topics_for_situation(situation)[:9])
    chunk_index = session.context.get("chunk_index", 0)
    back = get_copy("ussd.back", session.language)

    if topics:
        lines = [get_copy("ussd.related_rights", session.language)]
        for index, topic in enumerate(topics, start=1):
            lines.append(f"{index}. {truncate(topic.title, TITLE_TRUNCATE_LENGTH)}")
        lines.append(f"0. {back}")
        trailing = "\n".join(lines)
    else:
        trailing = f"0. {back}"

    text = situation.description or situation.title
    return _chunked_screen(text, chunk_index, trailing, session.language)


def transition_situation_detail(session, user_input):
    situation = Situation.objects.filter(
        slug=session.context.get("situation_slug"), is_active=True
    ).first()
    if situation is None:
        return "situation_list", {"page": 0}

    topics = list(_topics_for_situation(situation)[:9])
    chunk_index = session.context.get("chunk_index", 0)
    text = situation.description or situation.title
    is_last = _is_last_chunk(text, chunk_index)

    if not is_last:
        if user_input == "1":
            return (
                "situation_detail",
                {**session.context, "chunk_index": chunk_index + 1},
            )
        if user_input == "0":
            return "situation_list", {"page": 0}
        return None

    if user_input == "0":
        return "situation_list", {"page": 0}
    if topics and user_input.isdigit():
        choice = int(user_input)
        if 1 <= choice <= len(topics):
            return _enter_topic(situation.slug, topics[choice - 1])
    return None
