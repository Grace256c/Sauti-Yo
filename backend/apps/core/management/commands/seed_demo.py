from django.core.management.base import BaseCommand
from django.db import transaction

from apps.content.models import ChannelContent
from apps.rights.models import (
    ActionStep,
    RightsTopic,
    SafetyResponse,
    Situation,
    SituationRightsTopic,
)
from apps.support.models import SupportService


class Command(BaseCommand):
    help = "Seed Sauti Yo with a small Rights-to-Action demo journey."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding Sauti Yo demo data...")

        # -------------------------------------------------
        # 1. DEMO SITUATION
        # -------------------------------------------------

        situation, _ = Situation.objects.update_or_create(
            slug="problem-at-work",
            defaults={
                "title": "I have a problem at work",
                "description": (
                    "Understand your rights and explore practical "
                    "next steps for a workplace problem."
                ),
                "risk_level": "standard",
                "is_active": True,
            },
        )

        # -------------------------------------------------
        # 2. RIGHTS TOPIC
        # -------------------------------------------------

        rights_topic, _ = RightsTopic.objects.update_or_create(
            slug="workplace-rights",
            defaults={
                "title": "Understanding your workplace rights",
                "summary": (
                    "Sauti Yo can help you understand the issue, "
                    "review relevant rights information, and identify "
                    "possible next steps."
                ),
                "source_name": "Demo content — verification required",
                "reviewed_by": "",
                "verification_status": "review_required",
                "is_active": True,
            },
        )

        SituationRightsTopic.objects.get_or_create(
            situation=situation,
            rights_topic=rights_topic,
        )

        # -------------------------------------------------
        # 3. RIGHTS-TO-ACTION STEPS
        # -------------------------------------------------

        steps = [
            (
                1,
                "Understand what happened",
                "Identify the workplace issue and keep a clear "
                "record of important details.",
            ),
            (
                2,
                "Understand the relevant right",
                "Review verified information that may apply to "
                "your situation.",
            ),
            (
                3,
                "Keep useful information",
                "Where safe, keep relevant documents, dates, "
                "messages, or other records.",
            ),
            (
                4,
                "Choose a practical next step",
                "Consider an appropriate next action or connect "
                "with a verified support service.",
            ),
        ]

        for order, title, description in steps:
            ActionStep.objects.update_or_create(
                rights_topic=rights_topic,
                order=order,
                defaults={
                    "title": title,
                    "description": description,
                    "is_safety_critical": False,
                    "is_active": True,
                },
            )

        # -------------------------------------------------
        # 4. CHANNEL CONTENT
        # -------------------------------------------------
        #
        # Multilingual access supports accessibility.
        # It is NOT the central value proposition of Sauti Yo.
        #
        # Non-English entries remain explicitly unverified
        # until reviewed by appropriate language speakers.
        # -------------------------------------------------

        channel_content = [
            {
                "content_key": "problem_at_work_intro",
                "language": "en",
                "channel": "web",
                "text": (
                    "Having a problem at work? Sauti Yo can help "
                    "you understand the issue, learn about relevant "
                    "rights, and explore practical next steps."
                ),
                "is_verified": False,
            },
            {
                "content_key": "problem_at_work_intro",
                "language": "en",
                "channel": "ussd",
                "text": (
                    "Problem at work?\n"
                    "1. Understand the issue\n"
                    "2. Learn your rights\n"
                    "3. What can I do next?\n"
                    "4. Find support"
                ),
                "is_verified": False,
            },
            {
                "content_key": "problem_at_work_intro",
                "language": "en",
                "channel": "sms",
                "text": (
                    "Sauti Yo: Understand your workplace issue, "
                    "learn about relevant rights and find practical "
                    "next steps."
                ),
                "is_verified": False,
            },
            {
                "content_key": "problem_at_work_intro",
                "language": "en",
                "channel": "voice",
                "text": (
                    "Welcome to Sauti Yo. If you are having a "
                    "problem at work, we can help you understand "
                    "the situation, learn about relevant rights, "
                    "and hear possible next steps."
                ),
                "is_verified": False,
            },
        ]

        for item in channel_content:
            ChannelContent.objects.update_or_create(
                content_key=item["content_key"],
                language=item["language"],
                channel=item["channel"],
                defaults={
                    "text": item["text"],
                    "is_verified": item["is_verified"],
                    "reviewed_by": "",
                    "is_active": True,
                },
            )

        # -------------------------------------------------
        # 5. SUPPORT SERVICES (shared across situations below)
        # -------------------------------------------------

        support_services = [
            {
                "name": "Sauti 116 - Child & GBV Helpline",
                "service_type": "helpline",
                "description": (
                    "Free, 24/7, all networks. Run by the Ministry of "
                    "Gender, Labour & Social Development with UNICEF. "
                    "Handles child abuse and GBV cases."
                ),
                "phone_number": "116",
                "availability": "24/7",
                "coverage": "National",
                "verification_status": "review_required",
                "is_emergency_service": True,
            },
            {
                "name": "Uganda Police GBV Toll-Free Helpline",
                "service_type": "police",
                "description": (
                    "Department of Child & Family Protection, Police "
                    "HQ Naguru."
                ),
                "phone_number": "0800199195",
                "availability": "24/7",
                "coverage": "National",
                "verification_status": "review_required",
                "is_emergency_service": True,
            },
            {
                "name": "FIDA Uganda",
                "service_type": "legal_aid",
                "description": (
                    "Free legal advice for women, provided by the "
                    "Uganda Women Lawyers Association. Verify current "
                    "number before real deployment."
                ),
                "phone_number": "0800132132",
                "availability": "Business hours",
                "coverage": "National",
                "verification_status": "review_required",
                "is_emergency_service": False,
            },
        ]

        support_by_name = {}
        for item in support_services:
            service, _ = SupportService.objects.update_or_create(
                name=item["name"],
                defaults={**item, "is_active": True},
            )
            support_by_name[item["name"]] = service

        # -------------------------------------------------
        # 6. HOME SAFETY SITUATION (high risk)
        # -------------------------------------------------

        home_safety, _ = Situation.objects.update_or_create(
            slug="home-safety",
            defaults={
                "title": "I don't feel safe at home",
                "description": (
                    "For situations involving abuse, threats, or fear "
                    "at home."
                ),
                "risk_level": "high_risk",
                "is_active": True,
            },
        )

        domestic_violence_topic, _ = RightsTopic.objects.update_or_create(
            slug="domestic-violence-rights",
            defaults={
                "title": "Domestic Violence & Your Rights",
                "risk_level": "high_risk",
                "summary": (
                    "The Domestic Violence Act protects you from "
                    "physical, sexual, economic and emotional abuse by "
                    "a spouse, partner or family member. You can apply "
                    "for a protection order from a Magistrate's Court "
                    "without needing a lawyer. Police must record your "
                    "complaint - they cannot turn you away as a family "
                    "matter."
                ),
                "source_name": "Domestic Violence Act, 2010",
                "reviewed_by": "",
                "verification_status": "review_required",
                "is_active": True,
            },
        )
        domestic_violence_topic.support_services.set([
            support_by_name["Sauti 116 - Child & GBV Helpline"],
            support_by_name["Uganda Police GBV Toll-Free Helpline"],
        ])

        SituationRightsTopic.objects.get_or_create(
            situation=home_safety,
            rights_topic=domestic_violence_topic,
        )

        home_safety_steps = [
            (
                1,
                "If in immediate danger, move somewhere safer",
                "If you can safely do so, move to a safer location "
                "before anything else.",
                True,
            ),
            (
                2,
                "Call a free helpline",
                "Sauti 116 or the Police GBV line are both free and "
                "available 24/7.",
                True,
            ),
            (
                3,
                "Ask for a PF3 medical form if injured",
                "This form is free from a government health centre "
                "and helps document your case.",
                False,
            ),
            (
                4,
                "Apply for a protection order",
                "You can apply at a Magistrate's Court without needing "
                "a lawyer.",
                False,
            ),
        ]

        for order, title, description, is_safety_critical in home_safety_steps:
            ActionStep.objects.update_or_create(
                rights_topic=domestic_violence_topic,
                order=order,
                defaults={
                    "title": title,
                    "description": description,
                    "is_safety_critical": is_safety_critical,
                    "is_active": True,
                },
            )

        SafetyResponse.objects.update_or_create(
            rights_topic=domestic_violence_topic,
            trigger_key="immediate_danger",
            defaults={
                "message": (
                    "Your safety matters. You are not alone, and this "
                    "is not your fault. If you are in immediate "
                    "danger, consider moving somewhere safer if you "
                    "can. Free, trusted support: Sauti 116, or the "
                    "Police GBV line on 0800199195."
                ),
                "is_active": True,
            },
        )

        # -------------------------------------------------
        # 7. LAND / PROPERTY SITUATION (standard risk)
        # -------------------------------------------------

        land_property, _ = Situation.objects.update_or_create(
            slug="land-property",
            defaults={
                "title": "Land or property problem",
                "description": (
                    "For questions about property rights, especially "
                    "after separation."
                ),
                "risk_level": "standard",
                "is_active": True,
            },
        )

        matrimonial_property_topic, _ = RightsTopic.objects.update_or_create(
            slug="matrimonial-property-rights",
            defaults={
                "title": "Property Rights After Separation",
                "risk_level": "standard",
                "summary": (
                    "Under the Succession Act, a wife - including in "
                    "a customary marriage - generally has a right to "
                    "a share of matrimonial property acquired during "
                    "the marriage, even if it is registered in the "
                    "husband's name alone."
                ),
                "source_name": "Succession Act",
                "reviewed_by": "",
                "verification_status": "review_required",
                "is_active": True,
            },
        )
        matrimonial_property_topic.support_services.set([
            support_by_name["FIDA Uganda"],
        ])

        SituationRightsTopic.objects.get_or_create(
            situation=land_property,
            rights_topic=matrimonial_property_topic,
        )

        land_property_steps = [
            (
                1,
                "Do not sign away property rights",
                "Avoid signing any documents about the property "
                "before getting advice.",
            ),
            (
                2,
                "Contact a legal aid clinic",
                "FIDA Uganda offers free guidance on matrimonial "
                "property matters.",
            ),
            (
                3,
                "Keep property documents safe",
                "Hold on to any paperwork related to the property in "
                "a safe place.",
            ),
        ]

        for order, title, description in land_property_steps:
            ActionStep.objects.update_or_create(
                rights_topic=matrimonial_property_topic,
                order=order,
                defaults={
                    "title": title,
                    "description": description,
                    "is_safety_critical": False,
                    "is_active": True,
                },
            )

        # -------------------------------------------------
        # 8. CHANNEL CONTENT FOR THE NEW SITUATIONS (SMS only -
        #    web/ussd/voice copy for these two is a separate task)
        # -------------------------------------------------

        more_channel_content = [
            {
                "content_key": "home_safety_intro",
                "language": "en",
                "channel": "sms",
                "text": (
                    "Sauti Yo: The Domestic Violence Act protects you "
                    "from abuse by a spouse, partner or family member. "
                    "You can get a protection order without a lawyer."
                ),
                "is_verified": False,
            },
            {
                "content_key": "land_property_intro",
                "language": "en",
                "channel": "sms",
                "text": (
                    "Sauti Yo: A wife generally has a right to a "
                    "share of matrimonial property acquired during "
                    "the marriage, even if registered in the "
                    "husband's name alone."
                ),
                "is_verified": False,
            },
        ]

        for item in more_channel_content:
            ChannelContent.objects.update_or_create(
                content_key=item["content_key"],
                language=item["language"],
                channel=item["channel"],
                defaults={
                    "text": item["text"],
                    "is_verified": item["is_verified"],
                    "reviewed_by": "",
                    "is_active": True,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Sauti Yo demo data seeded successfully."
            )
        )