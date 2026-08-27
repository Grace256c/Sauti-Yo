"""
Internal service layer for the Rights-to-Action Engine.

These functions are called directly by other Django apps in this same
project (mainly apps.channels) - not over HTTP. USSD/SMS/Voice responses
need to be fast and can't depend on this server making an HTTP request to
itself.
"""

from apps.content.models import ChannelContent
from apps.rights.models import Situation


def list_active_situations():
    """
    Returns a simple list for building a situation-picker menu
    (e.g. the USSD 'What's happening?' screen).
    """
    return list(
        Situation.objects.filter(is_active=True)
        .order_by("title")
        .values("slug", "title", "description", "risk_level")
    )


def get_situation_detail(slug):
    """
    Returns the full Rights-to-Action picture for one situation:
    linked rights topics, their action steps, safety responses, and
    support services. Returns None if the slug doesn't exist or isn't active.
    """
    try:
        situation = Situation.objects.prefetch_related(
            "rights_links__rights_topic__action_steps",
            "rights_links__rights_topic__safety_responses",
            "rights_links__rights_topic__support_services",
            "rights_links__rights_topic__legal_provisions",
        ).get(slug=slug, is_active=True)
    except Situation.DoesNotExist:
        return None

    topics = []
    for link in situation.rights_links.all():
        topic = link.rights_topic
        topics.append({
            "slug": topic.slug,
            "title": topic.title,
            "summary": topic.summary,
            "action_steps": [
                {
                    "order": step.order,
                    "title": step.title,
                    "description": step.description,
                    "is_safety_critical": step.is_safety_critical,
                }
                for step in topic.action_steps.filter(is_active=True).order_by("order")
            ],
            "safety_responses": [
                {"trigger_key": r.trigger_key, "message": r.message}
                for r in topic.safety_responses.filter(is_active=True)
            ],
            "support_services": [
                {
                    "name": s.name,
                    "phone_number": s.phone_number,
                    "is_emergency_service": s.is_emergency_service,
                }
                for s in topic.support_services.filter(is_active=True)
            ],
            "legal_provisions": [
                {
                    "source_type": provision.source_type,
                    "law_title": provision.law_title,
                    "provision_reference":
                        provision.provision_reference,
                    "provision_heading":
                        provision.provision_heading,
                    "plain_language_explanation":
                        provision.plain_language_explanation,
                    "source_url": provision.source_url,
                    "jurisdiction": provision.jurisdiction,
                    "verification_status":
                        provision.verification_status,
                }
                for provision in topic.legal_provisions.filter(
                    is_active=True
                ).order_by("order", "id")
            ],
        })

    return {
        "slug": situation.slug,
        "title": situation.title,
        "description": situation.description,
        "risk_level": situation.risk_level,
        "rights_topics": topics,
    }


def get_channel_text(situation_slug, channel, language="en"):
    """
    Looks up pre-written, channel-specific copy for a situation, following
    the naming convention: content_key = "{slug_with_underscores}_intro"

    Returns None if nobody's written channel-specific text for this
    situation yet - callers should fall back to Situation.description
    in that case, not treat it as an error.
    """
    content_key = f"{situation_slug.replace('-', '_')}_intro"
    try:
        content = ChannelContent.objects.get(
            content_key=content_key,
            channel=channel,
            language=language,
            is_active=True,
        )
        return content.text
    except ChannelContent.DoesNotExist:
        return None


def get_safety_message(situation_slug, trigger_key="immediate_danger"):
    """
    Returns the predefined safety response for a high-risk situation.

    This function exists specifically so channel code NEVER has to
    construct safety-critical wording itself - it always comes from a
    human-reviewed SafetyResponse row. Returns None if no matching
    safety response exists.

    Tries `trigger_key` first, then falls back to the "default" trigger
    key if nothing matched - different channels in this codebase have
    used different trigger_key conventions (USSD uses "default"; this
    function's own default is "immediate_danger"), so this fallback keeps
    both working against the same seeded content.
    """
    detail = get_situation_detail(situation_slug)
    if not detail:
        return None
    for topic in detail["rights_topics"]:
        for response in topic["safety_responses"]:
            if response["trigger_key"] == trigger_key:
                return response["message"]
    if trigger_key != "default":
        for topic in detail["rights_topics"]:
            for response in topic["safety_responses"]:
                if response["trigger_key"] == "default":
                    return response["message"]
    return None



def _normalise_concern_text(text):
    return " ".join(
        (text or "")
        .lower()
        .strip()
        .split()
    )


def analyse_concern(concern):
    """
    Match a citizen's free-text concern to one active Sauti Yo
    situation and return database-grounded rights information.

    This matcher is deliberately deterministic. It may choose which
    stored record is relevant, but it never generates legal facts.
    """
    text = _normalise_concern_text(concern)

    if not text:
        return None

    situation_keywords = {
        "domestic-violence": {
            "domestic violence": 10,
            "partner beats": 10,
            "husband beats": 10,
            "wife beats": 10,
            "abusive partner": 9,
            "abuse at home": 9,
            "violence at home": 9,
            "beaten at home": 9,
            "threatened at home": 8,
            "protection order": 8,
            "abuser": 7,
            "domestic abuse": 10,
        },
        "facing-eviction": {
            "eviction": 10,
            "evicted": 10,
            "landlord": 7,
            "tenant": 6,
            "rent": 4,
            "notice to leave": 9,
            "kicked out": 8,
            "forced to leave": 8,
            "house": 2,
            "tenancy": 7,
        },
        "sexual-harassment": {
            "sexual harassment": 12,
            "sexually harassed": 12,
            "sexual advances": 11,
            "unwanted touching": 10,
            "sexual comments": 10,
            "sexual messages": 10,
            "asked for sex": 10,
            "sexual favour": 10,
            "sexual favors": 10,
            "harassed sexually": 12,
        },
        "problem-at-work": {
            "work": 3,
            "workplace": 4,
            "employer": 6,
            "boss": 5,
            "job": 4,
            "salary": 7,
            "wages": 7,
            "unpaid": 8,
            "dismissed": 8,
            "dismissal": 8,
            "fired": 9,
            "terminated": 8,
            "pregnant": 8,
            "pregnancy": 8,
            "discrimination": 7,
            "harassment": 4,
            "disciplinary": 6,
            "leave": 4,
            "trade union": 5,
        },
    }

    scored = []

    for slug, keywords in situation_keywords.items():
        score = sum(
            weight
            for phrase, weight in keywords.items()
            if phrase in text
        )

        if score > 0:
            scored.append(
                (
                    score,
                    slug,
                )
            )

    if not scored:
        return None

    scored.sort(
        key=lambda item: (
            -item[0],
            item[1],
        )
    )

    best_score, best_slug = scored[0]

    # Require more than a very weak generic match.
    if best_score < 4:
        return None

    detail = get_situation_detail(best_slug)

    if not detail:
        return None

    return {
        "concern": concern.strip(),
        "match_method": "deterministic",
        "match_score": best_score,
        "situation": detail,
    }
