from django.core.management.base import BaseCommand
from django.db import transaction

from apps.content.models import ChannelContent


class Command(BaseCommand):
    help = "Seed ChannelContent entries for home-safety and land-property situations."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding channel content...")

        entries = [
            # --- home-safety (high-risk) ---
            {
                "content_key": "home_safety_intro",
                "language": "en",
                "channel": "ussd",
                "text": (
                    "I don't feel safe at home\n"
                    "1. Understand what this may mean\n"
                    "2. What can I do next?\n"
                    "3. Find support\n"
                    "0. Exit"
                ),
            },
            {
                "content_key": "home_safety_intro",
                "language": "en",
                "channel": "sms",
                "text": (
                    "Sauti Yo: If you don't feel safe at home, the "
                    "Domestic Violence Act protects you. Reply STEPS for "
                    "next steps or HELP for support numbers."
                ),
            },
            {
                "content_key": "home_safety_intro",
                "language": "en",
                "channel": "voice",
                "text": (
                    "If you don't feel safe at home, you may be "
                    "protected under the Domestic Violence Act. Press 1 "
                    "to hear what this may mean. Press 2 for next steps. "
                    "Press 3 for support."
                ),
            },
            # --- land-property (standard) ---
            {
                "content_key": "land_property_intro",
                "language": "en",
                "channel": "ussd",
                "text": (
                    "Land or property problem\n"
                    "1. Understand what this may mean\n"
                    "2. What can I do next?\n"
                    "3. Find support\n"
                    "0. Exit"
                ),
            },
            {
                "content_key": "land_property_intro",
                "language": "en",
                "channel": "sms",
                "text": (
                    "Sauti Yo: You may have a right to a share of "
                    "matrimonial property after separation. Reply STEPS "
                    "for next steps or HELP for support numbers."
                ),
            },
            {
                "content_key": "land_property_intro",
                "language": "en",
                "channel": "voice",
                "text": (
                    "You may have a right to a share of matrimonial "
                    "property after separation. Press 1 to hear what "
                    "this may mean. Press 2 for next steps. Press 3 for "
                    "support."
                ),
            },
        ]

        for item in entries:
            ChannelContent.objects.update_or_create(
                content_key=item["content_key"],
                language=item["language"],
                channel=item["channel"],
                defaults={
                    "text": item["text"],
                    "is_verified": False,
                    "reviewed_by": "",
                    "is_active": True,
                },
            )

        self.stdout.write(
            self.style.SUCCESS("Channel content seeded successfully.")
        )
