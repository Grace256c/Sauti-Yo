"""
Referral service layer for citizens contacting via USSD/SMS/voice.

create_citizen_referral() is called directly by apps.channels (not over
HTTP), matching the existing apps.rights.services pattern. It is
risk-agnostic and trusts its caller on consent: gating out high_risk
situations and capturing genuine citizen consent are both the calling
channel's responsibility, not this function's.
"""

import logging

from django.db import transaction
from django.utils import timezone

from apps.partners.services import find_matching_organisations
from apps.referrals.models import Referral, ReferralStatusHistory
from apps.rights.models import Situation

logger = logging.getLogger(__name__)

# Channels track language as the short codes used by UssdSession.LANGUAGE_CHOICES
# (apps.channels.models); PartnerServiceConfiguration.languages stores the display
# names citizens/partners pick from in the web UI. This bridges the two vocabularies.
LANGUAGE_DISPLAY_NAMES = {
    "en": "English",
    "lg": "Luganda",
    "sw": "Kiswahili",
    "nyn": "Runyankole",
}


def create_citizen_referral(
    *, phone_number, situation_slug, district, language, origin_channel
):
    try:
        situation = Situation.objects.prefetch_related(
            "rights_links__rights_topic",
        ).get(slug=situation_slug, is_active=True)
    except Situation.DoesNotExist:
        return None

    link = situation.rights_links.order_by("id").first()
    if link is None:
        return None

    topic = link.rights_topic

    if not topic.rights_category:
        return None

    display_language = LANGUAGE_DISPLAY_NAMES.get(language, language)

    matches = find_matching_organisations(
        category=topic.rights_category,
        district=district,
        language=display_language,
        channel="phone",
    )

    if not matches:
        return None

    best_match = matches[0]

    try:
        with transaction.atomic():
            referral = Referral.objects.create(
                reference=Referral.generate_reference(),
                organisation_id=best_match["id"],
                rights_topic=topic,
                contact_phone=phone_number,
                district=district,
                language=display_language,
                preferred_support_channel="phone",
                citizen_consent_to_share=True,
                summary=(
                    f"{origin_channel.upper()} referral: citizen reported "
                    f"'{situation.title}'."
                ),
                status="new",
                shared_at=timezone.now(),
            )

            ReferralStatusHistory.objects.create(
                referral=referral,
                from_status="",
                to_status="new",
                changed_by=None,
                note=f"Referral created via {origin_channel}.",
            )
    except Exception:
        logger.exception(
            "Failed to create citizen referral for situation '%s'",
            situation_slug,
        )
        return None

    return referral
