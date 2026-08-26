import anthropic
from django.conf import settings

from apps.rights.services import list_active_situations

MODEL = "claude-haiku-4-5"

CLASSIFIER_SYSTEM_PROMPT = (
    "You are a strict classifier for Sauti Yo, a rights-to-action SMS "
    "service. Given a list of known situations and a free-text message "
    "from a citizen, respond with ONLY the matching situation's slug, "
    "or the single word NONE if nothing clearly matches. Never explain, "
    "never add commentary, never invent a slug that isn't in the list."
)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.LLM_API_KEY)
    return _client


def classify_situation(text):
    """
    Classifies free text against the catalog of known situations using
    Claude. Returns the matching situation slug, or None if nothing
    matched, the API key isn't configured, or the call failed for any
    reason - every failure mode is treated identically to "no match" so
    the caller can safely fall back to the unmatched-keyword reply.
    """
    if not settings.LLM_API_KEY:
        return None

    situations = list_active_situations()
    if not situations:
        return None

    valid_slugs = {s["slug"] for s in situations}
    catalog = "\n".join(f"{s['slug']}: {s['title']}" for s in situations)

    try:
        client = _get_client()
        response = client.with_options(timeout=5.0).messages.create(
            model=MODEL,
            max_tokens=32,
            system=CLASSIFIER_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Known situations:\n{catalog}\n\nMessage: {text}"
                    ),
                }
            ],
        )
    except Exception:
        # Any failure (auth, rate limit, network, timeout, unexpected SDK
        # error) degrades to "no match" - a classification failure has a
        # well-defined safe fallback, so it must never crash the SMS
        # handler over this call.
        return None

    reply_text = next(
        (block.text for block in response.content if block.type == "text"),
        "",
    ).strip()

    if reply_text in valid_slugs:
        return reply_text
    return None
