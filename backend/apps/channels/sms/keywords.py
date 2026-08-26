import re

DANGER_WORDS = [
    "danger", "weapon", "threatened", "emergency", "hurt", "right now",
]

SITUATION_KEYWORDS = {
    "home-safety": ["home", "abuse", "husband", "wife", "beat", "unsafe"],
    "problem-at-work": ["work", "job", "salary", "fired", "boss"],
    "land-property": ["land", "plot", "evict", "property"],
    # No Situation exists yet under any slug for "child" in this codebase.
    # Kept as a placeholder key so the keyword still matches; the None-guard
    # in handler.py makes this safe until a real situation is seeded — at
    # that point, update this key to the real slug.
    "child": ["child", "school", "minor", "kid"],
}

FOLLOWUP_WORDS = {
    "steps": ["step"],
    "support": ["support"],
}


def _normalize(text):
    return (text or "").strip().lower()


def match_danger(text):
    normalized = _normalize(text)
    return any(word in normalized for word in DANGER_WORDS)


def match_situation(text):
    normalized = _normalize(text)
    for slug in sorted(SITUATION_KEYWORDS):
        if any(word in normalized for word in SITUATION_KEYWORDS[slug]):
            return slug
    return None


def match_followup(text):
    normalized = _normalize(text)
    for intent in ("steps", "support"):
        if any(word in normalized for word in FOLLOWUP_WORDS[intent]):
            return intent
    return None


def match_help(text):
    normalized = _normalize(text)
    return bool(re.search(r"\bhelp\b", normalized))


def match_discreet(text):
    normalized = _normalize(text)
    return "discreet" in normalized


NOT_SAFE_ANSWER_PHRASES = ["not safe", "unsafe", "not okay", "not ok"]


def match_not_safe_answer(text):
    normalized = _normalize(text)
    if match_danger(text):
        return True
    if re.search(r"\bno\b", normalized):
        return True
    return any(phrase in normalized for phrase in NOT_SAFE_ANSWER_PHRASES)
