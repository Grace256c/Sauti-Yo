"""
Internal service layer for the Rights-to-Action Engine.

These functions are called DIRECTLY by other Django apps in this same
project (mainly `apps.channels`, once Person 3 builds it) - not over HTTP.
This is different from `views.py`, which serves the REST API used by the
external React frontend.

Keeping this distinction explicit matters: USSD/SMS/Voice responses need to
be fast and can't depend on this server making an HTTP request to itself.
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
        .values("slug", "title", "risk_level")
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
    """
    detail = get_situation_detail(situation_slug)
    if not detail:
        return None
    for topic in detail["rights_topics"]:
        for response in topic["safety_responses"]:
            if response["trigger_key"] == trigger_key:
                return response["message"]
    return None
