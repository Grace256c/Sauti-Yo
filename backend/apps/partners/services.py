"""
Partner-matching service layer.

find_matching_organisations() is called directly by apps.referrals.services
(for citizen referrals originating from USSD/SMS/voice) and by
PublicPartnerMatchAPIView (for the web citizen-support picker) - kept as a
single function so both callers see identical matching/scoring behavior.
"""

from apps.partners.models import PartnerOrganisation
from apps.partners.serializers import PublicPartnerMatchSerializer


def find_matching_organisations(category, district, language, channel):
    # Frontend uses "in-person"; backend stores "in_person".
    normalized_channel = (
        "in_person" if channel == "in-person" else channel
    )

    organisations = (
        PartnerOrganisation.objects
        .filter(
            is_active=True,
            is_test=False,
            service_configuration__accepting_referrals=True,
            verification_requests__status="verified",
        )
        .select_related(
            "support_service",
            "service_configuration",
        )
        .distinct()
    )

    matches = []

    for organisation in organisations:
        config = organisation.service_configuration

        if category not in (config.rights_categories or []):
            continue

        if not (
            config.nationwide
            or district in (config.districts_served or [])
        ):
            continue

        if language not in (config.languages or []):
            continue

        if normalized_channel not in (config.support_channels or []):
            continue

        score = 0
        reasons = []

        if category in (config.rights_categories or []):
            score += 30
            reasons.append("Supports this type of rights issue")

        if (
            config.nationwide
            or district in (config.districts_served or [])
        ):
            score += 25
            reasons.append(
                "Provides support nationally"
                if config.nationwide
                else f"Provides support in {district}"
            )

        if language in (config.languages or []):
            score += 20
            reasons.append(f"Provides support in {language}")

        if normalized_channel in (config.support_channels or []):
            score += 15

            channel_reason = {
                "remote": "Offers remote support",
                "phone": "Offers telephone support",
                "in_person": "Offers in-person support",
            }.get(
                normalized_channel,
                "Offers the preferred support method",
            )

            reasons.append(channel_reason)

        support_service = organisation.support_service

        data = {
            "id": organisation.id,
            "organisation_name": support_service.name,
            "organisation_type": organisation.organisation_type,
            "service_description": (
                config.service_description
                or support_service.description
                or ""
            ),
            "public_phone": organisation.public_phone,
            "public_email": organisation.public_email,
            "website": support_service.website,
            "districts_served": config.districts_served or [],
            "nationwide": config.nationwide,
            "languages": config.languages or [],
            "support_channels": config.support_channels or [],
            "rights_categories": config.rights_categories or [],
            "support_types": config.support_types or [],
            "free_services": config.free_services,
            "appointment_required": config.appointment_required,
            "availability_note": config.availability_note,
            "score": score,
            "reasons": reasons,
        }

        matches.append(PublicPartnerMatchSerializer(data).data)

    matches.sort(key=lambda item: item["score"], reverse=True)

    return matches
