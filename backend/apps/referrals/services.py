"""
Referral service layer for citizens contacting via USSD/SMS/voice.

create_citizen_referral() is called directly by apps.channels (not over
HTTP), matching the existing apps.rights.services pattern. It is
risk-agnostic and trusts its caller on consent: gating out high_risk
situations and capturing genuine citizen consent are both the calling
channel's responsibility, not this function's.
"""

from django.utils import timezone

from apps.partners.services import find_matching_organisations
from apps.referrals.models import Referral, ReferralStatusHistory
from apps.rights.models import Situation


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

    matches = find_matching_organisations(
        category=topic.slug,
        district=district,
        language=language,
        channel="phone",
    )

    if not matches:
        return None

    best_match = matches[0]

    referral = Referral.objects.create(
        reference=Referral.generate_reference(),
        organisation_id=best_match["id"],
        rights_topic=topic,
        contact_phone=phone_number,
        district=district,
        language=language,
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

    return referral
