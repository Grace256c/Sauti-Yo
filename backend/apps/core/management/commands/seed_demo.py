from django.core.management.base import BaseCommand
from django.db import transaction

from apps.content.models import ChannelContent


class Command(BaseCommand):
    help = "Seed Sauti Yo with a small Rights-to-Action demo journey."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding Sauti Yo demo data...")

        # -------------------------------------------------
        # CHANNEL CONTENT
        # -------------------------------------------------
        #
        # Multilingual access supports accessibility.
        # It is NOT the central value proposition of Sauti Yo.
        #
        # Non-English entries remain explicitly unverified
        # until reviewed by appropriate language speakers.
        #
        # The "problem at work" rights content itself (situation,
        # topic, action steps) is now owned by seed_pilot_content.py,
        # which has real, cited sources. This command only seeds
        # generic per-channel preview copy.
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
