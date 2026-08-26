import logging
import re

import anthropic
from django.conf import settings

from apps.rights.services import list_active_situations

logger = logging.getLogger(__name__)

MODEL = "claude-haiku-4-5"

CLASSIFIER_SYSTEM_PROMPT = (
    "You are a strict classifier for Sauti Yo, a rights-to-action SMS "
    "service. Given a list of known situations and a free-text message "
    "from a citizen, respond with ONLY the matching situation's slug, "
    "or the single word NONE if nothing clearly matches. Never explain, "
    "never add commentary, never invent a slug that isn't in the list."
)

REWORD_SYSTEM_PROMPT = (
    "You rewrite Sauti Yo SMS replies in a warmer, more conversational "
    "tone. You MUST NOT add, remove, or change any fact, phone number, "
    "name, or instruction in the original message - only rephrase how "
    "it is said. Keep it concise. Reply with ONLY the reworded "
    "message, nothing else."
)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.LLM_API_KEY, max_retries=0)
    return _client


def classify_situation(text):
    """
    Classifies free text against the catalog of known situations using
    Claude. Returns the matching situation slug, or None if nothing
    matched, the API key isn't configured, or the call failed for any
    reason - every failure mode is treated identically to "no match" so
    the caller can safely fall back to the unmatched-keyword reply.
    """
    if not settings.LLM_API_KEY or not text.strip():
        return None

    situations = list_active_situations()
    if not situations:
        return None

    valid_slugs = {s["slug"] for s in situations}
    catalog = "\n".join(
        f"{s['slug']}: {s['title']} - {s['description']}"
        if s["description"]
        else f"{s['slug']}: {s['title']}"
        for s in situations
    )

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
        reply_text = next(
            (block.text for block in response.content if block.type == "text"),
            "",
        ).strip()
    except Exception:
        # Any failure (auth, rate limit, network, timeout, malformed
        # response, unexpected SDK error) degrades to "no match" - a
        # classification failure has a well-defined safe fallback, so it
        # must never crash the SMS handler over this call.
        logger.warning("Situation classification failed", exc_info=True)
        return None

    if reply_text in valid_slugs:
        return reply_text
    return None


def reword_reply(template_text):
    """
    Asks Claude to rephrase an already-composed, verified SMS reply in a
    warmer tone, without changing any fact. Returns the reworded text,
    or None if rewording isn't possible/safe - the caller should send
    the original `template_text` unchanged in that case. Every failure
    mode (missing key, empty input, API error, or the reworded text
    dropping, corrupting, or inventing a phone number relative to the
    original) returns None.
    """
    if not settings.LLM_API_KEY or not template_text.strip():
        return None

    phone_numbers = re.findall(r"\d{3,}", template_text)

    try:
        client = _get_client()
        response = client.with_options(timeout=5.0).messages.create(
            model=MODEL,
            max_tokens=200,
            system=REWORD_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": template_text}],
        )
        reworded = next(
            (block.text for block in response.content if block.type == "text"),
            "",
        ).strip()
    except Exception:
        logger.warning("Reply rewording failed", exc_info=True)
        return None

    if not reworded:
        return None
    if set(re.findall(r"\d{3,}", reworded)) != set(phone_numbers):
        logger.warning("Reworded reply altered a phone number, discarding")
        return None
    return reworded
