import re

DANGER_WORDS = [
    "danger", "weapon", "threatened", "emergency", "hurt", "right now",
]

SITUATION_KEYWORDS = {
    "home-safety": ["home", "abuse", "husband", "wife", "beat", "unsafe"],
    "work": ["work", "job", "salary", "fired", "boss"],
    "land": ["land", "plot", "evict", "property"],
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
