from django.core.management.base import BaseCommand
from django.db import transaction

from apps.rights.models import (
    ActionStep,
    RightsTopic,
    SafetyResponse,
    Situation,
    SituationRightsTopic,
)
from apps.support.models import SupportService


class Command(BaseCommand):
    help = (
        "Seed Sauti Yo with pilot rights content (workplace, housing, "
        "domestic violence, sexual harassment). Idempotent — safe to re-run."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding Sauti Yo pilot content...")

        self._seed_workplace()
        self._seed_eviction()

        self.stdout.write(
            self.style.SUCCESS("Sauti Yo pilot content seeded successfully.")
        )

    def _support_service(self, **kwargs):
        name = kwargs.pop("name")
        service, _ = SupportService.objects.update_or_create(
            name=name,
            defaults={
                "verification_status": "review_required",
                "is_active": True,
                **kwargs,
            },
        )
        return service

    def _seed_action_steps(self, rights_topic, steps):
        for order, title, description, is_safety_critical in steps:
            ActionStep.objects.update_or_create(
                rights_topic=rights_topic,
                order=order,
                defaults={
                    "title": title,
                    "description": description,
                    "is_safety_critical": is_safety_critical,
                    "is_active": True,
                },
            )

    def _seed_workplace(self):
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

        rights_topic, _ = RightsTopic.objects.update_or_create(
            slug="workplace-rights",
            defaults={
                "title": "Understanding your workplace rights",
                "summary": (
                    "Sauti Yo can help you understand the issue, "
                    "review relevant rights information, and identify "
                    "possible next steps."
                ),
                "risk_level": "standard",
                "source_name": "Employment Act, 2006 (Cap 226), Laws of Uganda",
                "source_url": (
                    "https://bills.parliament.ug/attachments/Laws%20of%20"
                    "Uganda%20(Acts)%20-%20THE%20EMPLOYMENT%20ACT,%202006.pdf"
                ),
                "reviewed_by": "",
                "verification_status": "review_required",
                "is_active": True,
            },
        )

        SituationRightsTopic.objects.get_or_create(
            situation=situation,
            rights_topic=rights_topic,
        )

        self._seed_action_steps(
            rights_topic,
            [
                (
                    1,
                    "Understand what happened",
                    "Identify the workplace issue and keep a clear "
                    "record of important details.",
                    False,
                ),
                (
                    2,
                    "Understand the relevant right",
                    "Review verified information that may apply to "
                    "your situation.",
                    False,
                ),
                (
                    3,
                    "Keep useful information",
                    "Where safe, keep relevant documents, dates, "
                    "messages, or other records.",
                    False,
                ),
                (
                    4,
                    "Choose a practical next step",
                    "Consider an appropriate next action or connect "
                    "with a verified support service.",
                    False,
                ),
            ],
        )

        legal_aid = self._support_service(
            name="Uganda Law Society Legal Aid Project",
            service_type="Legal Aid",
            description=(
                "Free legal advice, representation, and referrals for "
                "the poor, indigent, and vulnerable."
            ),
            phone_number="0800100150",
            coverage="National",
            is_emergency_service=False,
        )
        rights_topic.support_services.add(legal_aid)

    def _seed_eviction(self):
        situation, _ = Situation.objects.update_or_create(
            slug="facing-eviction",
            defaults={
                "title": "I'm facing eviction or a housing problem",
                "description": (
                    "Understand your rights as a tenant, what a lawful "
                    "eviction looks like, and what to do if you're "
                    "being evicted unfairly."
                ),
                "risk_level": "standard",
                "is_active": True,
            },
        )

        rights_topic, _ = RightsTopic.objects.update_or_create(
            slug="housing-and-eviction-rights",
            defaults={
                "title": "Your rights as a tenant",
                "summary": (
                    "Ugandan law sets minimum notice periods before you "
                    "can be evicted and requires evictions to follow a "
                    "lawful process. If you're evicted unlawfully, you "
                    "have a right to seek relief."
                ),
                "risk_level": "standard",
                "source_name": (
                    "Landlord and Tenant Act, 2022 (Chapter 238), "
                    "Laws of Uganda"
                ),
                "source_url": (
                    "https://ulii.org/en/akn/ug/act/2022/9/"
                    "eng@2023-12-31/source"
                ),
                "reviewed_by": "",
                "verification_status": "review_required",
                "is_active": True,
            },
        )

        SituationRightsTopic.objects.get_or_create(
            situation=situation,
            rights_topic=rights_topic,
        )

        self._seed_action_steps(
            rights_topic,
            [
                (
                    1,
                    "Check your notice period",
                    "By law you must be given written notice before "
                    "eviction: at least 7 days for a weekly tenancy, "
                    "30 days for a monthly tenancy, or 60 days for a "
                    "yearly tenancy. A shorter period in your tenancy "
                    "agreement is not valid.",
                    False,
                ),
                (
                    2,
                    "Know what a lawful eviction looks like",
                    "For non-payment of rent, your landlord can only "
                    "re-enter after your payment is more than 30 days "
                    "overdue, and the eviction must happen with the "
                    "Local Council and Police present.",
                    False,
                ),
                (
                    3,
                    "Keep your records",
                    "Keep your tenancy agreement and proof of rent "
                    "payments — these matter if you need to show an "
                    "eviction was unlawful.",
                    False,
                ),
                (
                    4,
                    "Get help if you're evicted unlawfully",
                    "If your landlord evicts you without following the "
                    "law, you can seek relief from court, including "
                    "compensation. Free legal aid is available.",
                    False,
                ),
            ],
        )

        legal_aid = self._support_service(
            name="Uganda Law Society Legal Aid Project",
            service_type="Legal Aid",
            description=(
                "Free legal advice, representation, and referrals for "
                "the poor, indigent, and vulnerable."
            ),
            phone_number="0800100150",
            coverage="National",
            is_emergency_service=False,
        )
        rights_topic.support_services.add(legal_aid)
