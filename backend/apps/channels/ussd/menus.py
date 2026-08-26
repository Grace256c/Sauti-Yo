from apps.content.models import ChannelContent

SCREEN_BUDGET = 160
PAGE_SIZE = 5
TITLE_TRUNCATE_LENGTH = 40

DEFAULT_COPY = {
    "ussd.welcome": "Welcome to Sauti Yo",
    "ussd.language_prompt": (
        "1. English\n2. Luganda\n3. Kiswahili\n4. Runyankole"
    ),
    "ussd.language_unavailable": (
        "That language is not available yet. Please choose English for now."
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
    "ussd.continue": "1. Continue\n0. Back",
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


def _wrap_words(words, budget):
    # A non-positive budget would make the hard-split loop below spin forever.
    # No current caller can produce one (every budget is floored at 20), but a
    # hang inside a request handler is far worse than a degenerate wrap.
    budget = max(budget, 1)
    lines = []
    current = ""
    for word in words:
        while len(word) > budget:
            if current:
                lines.append(current)
                current = ""
            lines.append(word[:budget])
            word = word[budget:]
        candidate = f"{current} {word}".strip()
        if len(candidate) > budget:
            if current:
                lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def chunk_text(text, budget=SCREEN_BUDGET):
    if not text:
        return [""]
    lines = []
    for paragraph in text.split("\n"):
        lines.extend(_wrap_words(paragraph.split(" "), budget) if paragraph else [""])

    chunks = []
    current_lines = []
    current_len = 0
    for line in lines:
        added_len = len(line) + (1 if current_lines else 0)
        if current_lines and current_len + added_len > budget:
            chunks.append("\n".join(current_lines))
            current_lines = [line]
            current_len = len(line)
        else:
            current_lines.append(line)
            current_len += added_len
    if current_lines:
        chunks.append("\n".join(current_lines))
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
    if session.context.get("unavailable_notice"):
        requested = session.context.get("requested_language", session.language)
        notice = get_copy("ussd.language_unavailable", requested)
        return f"{notice}\n\n{body}\n{prompt}", False
    return f"{body}\n{prompt}", False


def transition_language_select(session, user_input):
    mapping = {"1": "en", "2": "lg", "3": "sw", "4": "nyn"}
    language = mapping.get(user_input)
    if language is None:
        return None
    if language != "en":
        return "language_select", {
            "unavailable_notice": True,
            "requested_language": language,
        }
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
    if topic.risk_level in ("sensitive", "high_risk"):
        return "safety_gate", context
    return "topic_detail", context


def _chunked_screen(text, chunk_index, trailing_options, language):
    more = get_copy("ussd.more", language)
    back = get_copy("ussd.back", language)
    more_back = f"1. {more}\n0. {back}"
    reserved = max(len(trailing_options), len(more_back))
    body_budget = max(SCREEN_BUDGET - reserved - 2, 20)

    chunks = chunk_text(text, budget=body_budget) if text else [""]
    chunk_index = max(0, min(chunk_index, len(chunks) - 1))
    body = chunks[chunk_index]
    is_last = chunk_index == len(chunks) - 1
    if is_last:
        screen = f"{body}\n\n{trailing_options}" if trailing_options else body
    else:
        screen = f"{body}\n\n{more_back}"
    return screen, is_last


def _fit_numbered_lines(items, start_index, label_fn, budget, max_items=8):
    lines = []
    index = start_index
    while index < len(items) and len(lines) < max_items:
        candidate_line = f"{len(lines) + 1}. {label_fn(items[index])}"
        candidate_text = "\n".join(lines + [candidate_line])
        if lines and len(candidate_text) > budget:
            break
        lines.append(candidate_line)
        index += 1
    has_more = index < len(items)
    shown_items = items[start_index:index]
    return lines, shown_items, index, has_more


def _situation_list_page(session):
    situations = list(Situation.objects.filter(is_active=True).order_by("title"))
    start_index = session.context.get("page", 0)
    back = get_copy("ussd.back", session.language)
    header = get_copy("ussd.choose_situation", session.language)
    more_label = get_copy("ussd.more", session.language)

    reserved = len(header) + 1 + len(f"8. {more_label}") + 1 + len(f"0. {back}") + 2
    budget = max(SCREEN_BUDGET - reserved, 20)

    lines, shown, next_index, has_more = _fit_numbered_lines(
        situations,
        start_index,
        lambda s: truncate(s.title, TITLE_TRUNCATE_LENGTH),
        budget,
        max_items=7,
    )
    return situations, header, lines, shown, next_index, has_more, back, more_label


def render_situation_list(session):
    situations, header, lines, shown, next_index, has_more, back, more_label = (
        _situation_list_page(session)
    )

    if not situations:
        body = get_copy("ussd.no_situations", session.language)
        return f"{body}\n\n0. {back}", False

    screen_lines = [header] + lines
    if has_more:
        screen_lines.append(f"8. {more_label}")
    screen_lines.append(f"0. {back}")
    return "\n".join(screen_lines), False


def transition_situation_list(session, user_input):
    situations, header, lines, shown, next_index, has_more, back, more_label = (
        _situation_list_page(session)
    )

    if user_input == "0":
        return "main_menu", {}
    if user_input == "8" and has_more:
        return "situation_list", {"page": next_index}
    if user_input.isdigit():
        choice = int(user_input)
        if 1 <= choice <= len(shown):
            situation = shown[choice - 1]
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

    if session.context.get("stage") == "topics":
        return _render_situation_topics(session, situation)

    topics = list(_topics_for_situation(situation)[:9])
    back = get_copy("ussd.back", session.language)
    trailing = get_copy("ussd.continue", session.language) if topics else f"0. {back}"

    chunk_index = session.context.get("chunk_index", 0)
    text = situation.description or situation.title
    screen, _ = _chunked_screen(text, chunk_index, trailing, session.language)
    return screen, False


def transition_situation_detail(session, user_input):
    situation = Situation.objects.filter(
        slug=session.context.get("situation_slug"), is_active=True
    ).first()
    if situation is None:
        return "situation_list", {"page": 0}

    if session.context.get("stage") == "topics":
        return _transition_situation_topics(session, user_input, situation)

    topics = list(_topics_for_situation(situation)[:9])
    back = get_copy("ussd.back", session.language)
    trailing = get_copy("ussd.continue", session.language) if topics else f"0. {back}"

    chunk_index = session.context.get("chunk_index", 0)
    text = situation.description or situation.title
    _, is_last = _chunked_screen(text, chunk_index, trailing, session.language)

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
    if topics and user_input == "1":
        return (
            "situation_detail",
            {
                "situation_slug": situation.slug,
                "stage": "topics",
                "page": 0,
            },
        )
    return None


def _situation_topics_page(session, topics):
    start_index = session.context.get("page", 0)
    back = get_copy("ussd.back", session.language)
    header = get_copy("ussd.related_rights", session.language)
    more_label = get_copy("ussd.more", session.language)

    reserved = len(header) + 1 + len(f"8. {more_label}") + 1 + len(f"0. {back}") + 2
    budget = max(SCREEN_BUDGET - reserved, 20)

    lines, shown, next_index, has_more = _fit_numbered_lines(
        topics,
        start_index,
        lambda t: truncate(t.title, TITLE_TRUNCATE_LENGTH),
        budget,
        max_items=7,
    )
    return header, lines, shown, next_index, has_more, back, more_label


def _render_situation_topics(session, situation):
    topics = list(_topics_for_situation(situation)[:9])
    header, lines, shown, next_index, has_more, back, more_label = (
        _situation_topics_page(session, topics)
    )
    screen_lines = [header] + lines
    if has_more:
        screen_lines.append(f"8. {more_label}")
    screen_lines.append(f"0. {back}")
    return "\n".join(screen_lines), False


def _transition_situation_topics(session, user_input, situation):
    topics = list(_topics_for_situation(situation)[:9])
    header, lines, shown, next_index, has_more, back, more_label = (
        _situation_topics_page(session, topics)
    )

    if user_input == "0":
        return "situation_list", {"page": 0}
    if user_input == "8" and has_more:
        return (
            "situation_detail",
            {
                "situation_slug": situation.slug,
                "stage": "topics",
                "page": next_index,
            },
        )
    if user_input.isdigit():
        choice = int(user_input)
        if 1 <= choice <= len(shown):
            return _enter_topic(situation.slug, shown[choice - 1])
    return None


def _back_to_topic_detail(situation_slug, topic_slug):
    return "topic_detail", {
        "situation_slug": situation_slug,
        "topic_slug": topic_slug,
        "chunk_index": 9999,
    }


def _back_from_topic(situation_slug, topic_slug):
    situation = Situation.objects.filter(
        slug=situation_slug, is_active=True
    ).first()
    if situation is None:
        return "situation_list", {"page": 0}
    topics = list(_topics_for_situation(situation)[:9])
    if len(topics) <= 1:
        return "situation_list", {"page": 0}
    return (
        "situation_detail",
        {"situation_slug": situation_slug, "stage": "topics", "page": 0},
    )


def render_topic_detail(session):
    topic = RightsTopic.objects.filter(
        slug=session.context.get("topic_slug"), is_active=True
    ).first()
    if topic is None:
        return get_copy("ussd.not_found", session.language), False

    chunk_index = session.context.get("chunk_index", 0)
    menu = get_copy("ussd.topic_menu", session.language)
    text = topic.summary or topic.title
    screen, _ = _chunked_screen(text, chunk_index, menu, session.language)
    return screen, False


def transition_topic_detail(session, user_input):
    situation_slug = session.context.get("situation_slug")
    topic_slug = session.context.get("topic_slug")
    topic = RightsTopic.objects.filter(slug=topic_slug, is_active=True).first()
    if topic is None:
        return "situation_list", {"page": 0}

    chunk_index = session.context.get("chunk_index", 0)
    text = topic.summary or topic.title
    menu = get_copy("ussd.topic_menu", session.language)
    _, is_last = _chunked_screen(text, chunk_index, menu, session.language)

    if not is_last:
        if user_input == "1":
            return (
                "topic_detail",
                {**session.context, "chunk_index": chunk_index + 1},
            )
        if user_input == "0":
            return _back_from_topic(situation_slug, topic_slug)
        return None

    if user_input == "1":
        return (
            "action_steps",
            {
                "situation_slug": situation_slug,
                "topic_slug": topic_slug,
                "step_index": 0,
                "chunk_index": 0,
            },
        )
    if user_input == "2":
        return (
            "support_contacts",
            {
                "situation_slug": situation_slug,
                "topic_slug": topic_slug,
                "chunk_index": 0,
            },
        )
    if user_input == "0":
        return _back_from_topic(situation_slug, topic_slug)
    return None


def render_safety_gate(session):
    topic = RightsTopic.objects.filter(
        slug=session.context.get("topic_slug"), is_active=True
    ).first()
    if topic is None:
        return get_copy("ussd.not_found", session.language), False

    safety = topic.safety_responses.filter(
        trigger_key="default", is_active=True
    ).first()
    message = safety.message if safety else topic.summary or topic.title
    chunk_index = session.context.get("chunk_index", 0)
    options = get_copy("ussd.safety_continue", session.language)
    screen, _ = _chunked_screen(message, chunk_index, options, session.language)
    return screen, False


def transition_safety_gate(session, user_input):
    situation_slug = session.context.get("situation_slug")
    topic_slug = session.context.get("topic_slug")
    topic = RightsTopic.objects.filter(slug=topic_slug, is_active=True).first()
    if topic is None:
        return "situation_list", {"page": 0}

    safety = topic.safety_responses.filter(
        trigger_key="default", is_active=True
    ).first()
    message = safety.message if safety else topic.summary or topic.title
    chunk_index = session.context.get("chunk_index", 0)
    options = get_copy("ussd.safety_continue", session.language)
    _, is_last = _chunked_screen(message, chunk_index, options, session.language)

    if not is_last:
        if user_input == "1":
            return (
                "safety_gate",
                {**session.context, "chunk_index": chunk_index + 1},
            )
        if user_input == "0":
            return _back_from_topic(situation_slug, topic_slug)
        return None

    if user_input == "1":
        return (
            "topic_detail",
            {
                "situation_slug": situation_slug,
                "topic_slug": topic_slug,
                "chunk_index": 0,
            },
        )
    if user_input == "0":
        return _back_from_topic(situation_slug, topic_slug)
    return None


def render_action_steps(session):
    topic = RightsTopic.objects.filter(
        slug=session.context.get("topic_slug"), is_active=True
    ).first()
    if topic is None:
        return get_copy("ussd.not_found", session.language), False

    steps = list(
        topic.action_steps.filter(is_active=True).order_by("order", "id")
    )
    back_label = get_copy("ussd.back", session.language)
    if not steps:
        body = get_copy("ussd.no_action_steps", session.language)
        return f"{body}\n\n0. {back_label}", False

    step_index = min(session.context.get("step_index", 0), len(steps) - 1)
    step = steps[step_index]
    text = f"Step {step_index + 1}/{len(steps)}: {step.title}\n{step.description}"
    chunk_index = session.context.get("chunk_index", 0)

    has_next = step_index + 1 < len(steps)
    if has_next:
        next_label = get_copy("ussd.next", session.language)
        trailing = f"1. {next_label}\n0. {back_label}"
    else:
        trailing = f"0. {back_label}"

    screen, _ = _chunked_screen(text, chunk_index, trailing, session.language)
    return screen, False


def transition_action_steps(session, user_input):
    situation_slug = session.context.get("situation_slug")
    topic_slug = session.context.get("topic_slug")
    topic = RightsTopic.objects.filter(slug=topic_slug, is_active=True).first()
    if topic is None:
        return "situation_list", {"page": 0}

    steps = list(
        topic.action_steps.filter(is_active=True).order_by("order", "id")
    )
    if not steps:
        if user_input == "0":
            return _back_to_topic_detail(situation_slug, topic_slug)
        return None

    step_index = min(session.context.get("step_index", 0), len(steps) - 1)
    step = steps[step_index]
    text = f"Step {step_index + 1}/{len(steps)}: {step.title}\n{step.description}"
    chunk_index = session.context.get("chunk_index", 0)
    has_next = step_index + 1 < len(steps)
    back_label = get_copy("ussd.back", session.language)
    if has_next:
        next_label = get_copy("ussd.next", session.language)
        trailing = f"1. {next_label}\n0. {back_label}"
    else:
        trailing = f"0. {back_label}"
    _, is_last = _chunked_screen(text, chunk_index, trailing, session.language)

    if not is_last:
        if user_input == "1":
            return (
                "action_steps",
                {**session.context, "chunk_index": chunk_index + 1},
            )
        if user_input == "0":
            return _back_to_topic_detail(situation_slug, topic_slug)
        return None

    if has_next and user_input == "1":
        return (
            "action_steps",
            {
                "situation_slug": situation_slug,
                "topic_slug": topic_slug,
                "step_index": step_index + 1,
                "chunk_index": 0,
            },
        )
    if user_input == "0":
        return _back_to_topic_detail(situation_slug, topic_slug)
    return None


from apps.support.models import SupportService


def _format_contacts(services):
    lines = []
    for service in services:
        phone = service.phone_number or service.alternate_phone_number or "N/A"
        lines.append(f"{service.name}: {phone}")
    return "\n".join(lines)


def render_support_contacts(session):
    topic = RightsTopic.objects.filter(
        slug=session.context.get("topic_slug"), is_active=True
    ).first()
    if topic is None:
        return get_copy("ussd.not_found", session.language), False

    services = list(topic.support_services.filter(is_active=True).order_by("name"))
    chunk_index = session.context.get("chunk_index", 0)
    back = f"0. {get_copy('ussd.back', session.language)}"

    if not services:
        body = get_copy("ussd.no_support_contacts", session.language)
        return f"{body}\n\n{back}", False

    screen, _ = _chunked_screen(
        _format_contacts(services), chunk_index, back, session.language
    )
    return screen, False


def transition_support_contacts(session, user_input):
    situation_slug = session.context.get("situation_slug")
    topic_slug = session.context.get("topic_slug")
    topic = RightsTopic.objects.filter(slug=topic_slug, is_active=True).first()
    if topic is None:
        return "situation_list", {"page": 0}

    services = list(topic.support_services.filter(is_active=True).order_by("name"))
    if not services:
        if user_input == "0":
            return _back_to_topic_detail(situation_slug, topic_slug)
        return None

    chunk_index = session.context.get("chunk_index", 0)
    back = f"0. {get_copy('ussd.back', session.language)}"
    _, is_last = _chunked_screen(
        _format_contacts(services), chunk_index, back, session.language
    )

    if not is_last:
        if user_input == "1":
            return (
                "support_contacts",
                {**session.context, "chunk_index": chunk_index + 1},
            )
        if user_input == "0":
            return _back_to_topic_detail(situation_slug, topic_slug)
        return None

    if user_input == "0":
        return _back_to_topic_detail(situation_slug, topic_slug)
    return None


def render_emergency_list(session):
    services = list(
        SupportService.objects.filter(
            is_emergency_service=True, is_active=True
        ).order_by("name")
    )
    chunk_index = session.context.get("chunk_index", 0)
    back = f"0. {get_copy('ussd.back', session.language)}"

    if not services:
        body = get_copy("ussd.no_emergency_contacts", session.language)
        return f"{body}\n\n{back}", False

    screen, _ = _chunked_screen(
        _format_contacts(services), chunk_index, back, session.language
    )
    return screen, False


def transition_emergency_list(session, user_input):
    services = list(
        SupportService.objects.filter(
            is_emergency_service=True, is_active=True
        ).order_by("name")
    )
    if not services:
        if user_input == "0":
            return "main_menu", {}
        return None

    chunk_index = session.context.get("chunk_index", 0)
    back = f"0. {get_copy('ussd.back', session.language)}"
    _, is_last = _chunked_screen(
        _format_contacts(services), chunk_index, back, session.language
    )

    if not is_last:
        if user_input == "1":
            return (
                "emergency_list",
                {**session.context, "chunk_index": chunk_index + 1},
            )
        if user_input == "0":
            return "main_menu", {}
        return None

    if user_input == "0":
        return "main_menu", {}
    return None


RENDER_HANDLERS = {
    "language_select": render_language_select,
    "main_menu": render_main_menu,
    "goodbye": render_goodbye,
    "situation_list": render_situation_list,
    "situation_detail": render_situation_detail,
    "safety_gate": render_safety_gate,
    "topic_detail": render_topic_detail,
    "action_steps": render_action_steps,
    "support_contacts": render_support_contacts,
    "emergency_list": render_emergency_list,
}

TRANSITION_HANDLERS = {
    "language_select": transition_language_select,
    "main_menu": transition_main_menu,
    "situation_list": transition_situation_list,
    "situation_detail": transition_situation_detail,
    "safety_gate": transition_safety_gate,
    "topic_detail": transition_topic_detail,
    "action_steps": transition_action_steps,
    "support_contacts": transition_support_contacts,
    "emergency_list": transition_emergency_list,
}


def render_state(state, session):
    return RENDER_HANDLERS[state](session)


def transition_state(state, session, user_input):
    return TRANSITION_HANDLERS[state](session, user_input)
