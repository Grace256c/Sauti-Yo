from pathlib import Path
import json

from django.conf import settings
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
        #
        # Naming convention: content_key = "{situation_slug_with_underscores}_intro"
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
        # 5. LOAD FROM seed/support_services.json AND
        #    seed/rights.json (family-safety + property topics)
        # -------------------------------------------------

        seed_dir = Path(settings.BASE_DIR) / "seed"

        with open(seed_dir / "support_services.json", encoding="utf-8") as f:
            services_data = json.load(f)

        services_by_name = {}
        for item in services_data:
            service, _ = SupportService.objects.update_or_create(
                name=item["name"],
                defaults={k: v for k, v in item.items() if k != "name"},
            )
            services_by_name[item["name"]] = service

        with open(seed_dir / "rights.json", encoding="utf-8") as f:
            rights_data = json.load(f)

        topics_by_slug = {}
        for topic_item in rights_data["rights_topics"]:
            topic, _ = RightsTopic.objects.update_or_create(
                slug=topic_item["slug"],
                defaults={
                    "title": topic_item["title"],
                    "summary": topic_item["summary"],
                    "source_name": topic_item.get("source_name", ""),
                    "source_url": topic_item.get("source_url", ""),
                    "verification_status": topic_item.get(
                        "verification_status", "review_required"
                    ),
                    "is_active": True,
                },
            )
            topics_by_slug[topic_item["slug"]] = topic

            linked_services = [
                services_by_name[name]
                for name in topic_item.get("support_services", [])
            ]
            topic.support_services.set(linked_services)

            for step in topic_item.get("action_steps", []):
                ActionStep.objects.update_or_create(
                    rights_topic=topic,
                    order=step["order"],
                    defaults={
                        "title": step["title"],
                        "description": step["description"],
                        "is_safety_critical": step.get(
                            "is_safety_critical", False
                        ),
                        "is_active": True,
                    },
                )

            for safety in topic_item.get("safety_responses", []):
                SafetyResponse.objects.update_or_create(
                    rights_topic=topic,
                    trigger_key=safety["trigger_key"],
                    defaults={
                        "message": safety["message"],
                        "is_active": True,
                    },
                )

        for situation_item in rights_data["situations"]:
            demo_situation, _ = Situation.objects.update_or_create(
                slug=situation_item["slug"],
                defaults={
                    "title": situation_item["title"],
                    "description": situation_item.get("description", ""),
                    "risk_level": situation_item.get(
                        "risk_level", "standard"
                    ),
                    "is_active": True,
                },
            )
            for topic_slug in situation_item.get("rights_topics", []):
                SituationRightsTopic.objects.get_or_create(
                    situation=demo_situation,
                    rights_topic=topics_by_slug[topic_slug],
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Sauti Yo demo data seeded successfully."
            )
        )
