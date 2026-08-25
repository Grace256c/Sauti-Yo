from django.core.management.base import BaseCommand
from django.db import transaction

from apps.content.models import ChannelContent
from apps.rights.models import (
    ActionStep,
    RightsTopic,
    Situation,
    SituationRightsTopic,
)


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

        self.stdout.write(
            self.style.SUCCESS(
                "Sauti Yo demo data seeded successfully."
            )
        )