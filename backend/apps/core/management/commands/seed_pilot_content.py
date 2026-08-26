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
        "domestic violence, sexual harassment). Idempotent - safe to re-run."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding Sauti Yo pilot content...")

        self._seed_workplace()
        self._seed_eviction()
        self._seed_domestic_violence()
        self._seed_sexual_harassment()

        self.stdout.write(
            self.style.SUCCESS("Sauti Yo pilot content seeded successfully.")
        )
        self.stdout.write(
            self.style.WARNING(
                "All seeded content has verification_status='review_required' "
                "and has NOT been reviewed by a human with legal/NGO authority. "
                "Do not treat this as verified before a real review happens."
            )
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
                    "Review information that may apply to "
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
                    "with a support service.",
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
                    "payments - these matter if you need to show an "
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

    def _seed_domestic_violence(self):
        situation, _ = Situation.objects.update_or_create(
            slug="domestic-violence",
            defaults={
                "title": "I'm experiencing domestic violence",
                "description": (
                    "Information on your legal protections and how to "
                    "get immediate help if you or someone you know is "
                    "experiencing domestic violence."
                ),
                "risk_level": "high_risk",
                "is_active": True,
            },
        )

        rights_topic, _ = RightsTopic.objects.update_or_create(
            slug="domestic-violence-protection",
            defaults={
                "title": "Your right to protection under the law",
                "summary": (
                    "Uganda's Domestic Violence Act lets you apply for "
                    "a protection order against an abuser, including "
                    "without them being present, and courts can order "
                    "an abuser to leave the home."
                ),
                "risk_level": "high_risk",
                "source_name": (
                    "Domestic Violence Act, 2010 (Act No. 3 of 2010), "
                    "Laws of Uganda"
                ),
                "source_url": (
                    "https://ulii.org/en/akn/ug/act/2010/3/eng@2023-12-31"
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

        SafetyResponse.objects.update_or_create(
            rights_topic=rights_topic,
            trigger_key="default",
            defaults={
                "message": (
                    "If you are in immediate danger, get to a safe "
                    "place if you can and call the Uganda Police GBV "
                    "Helpline on 0800 199 195 (toll-free) or go to the "
                    "nearest police station now. This is not a "
                    "substitute for emergency help - it's here so you "
                    "know your rights once you're safe: Ugandan law "
                    "lets you apply for a protection order against an "
                    "abuser, and a court can order them to leave your "
                    "home."
                ),
                "is_active": True,
            },
        )

        self._seed_action_steps(
            rights_topic,
            [
                (
                    1,
                    "Get to safety first",
                    "If you're in danger right now, prioritise getting "
                    "somewhere safe over anything else on this list.",
                    True,
                ),
                (
                    2,
                    "Report to the Police Family & Child Protection desk",
                    "You can report at any police station, or call the "
                    "GBV helpline on 0800 199 195.",
                    False,
                ),
                (
                    3,
                    "Ask about a protection order",
                    "You or someone on your behalf can apply to a "
                    "magistrate's court for a protection order - this "
                    "can be done without your abuser present.",
                    False,
                ),
                (
                    4,
                    "Reach out for ongoing support",
                    "Organisations like MIFUMI and FIDA-Uganda offer "
                    "confidential help, counselling, and further legal "
                    "support.",
                    False,
                ),
            ],
        )

        police_gbv = self._support_service(
            name="Uganda Police GBV Helpline",
            service_type="Emergency / GBV Response",
            description=(
                "Toll-free helpline run by the Uganda Police Force "
                "Department of Child and Family Protection for "
                "reporting gender-based violence and getting help."
            ),
            phone_number="0800199195",
            coverage="National",
            is_emergency_service=True,
        )
        mifumi = self._support_service(
            name="MIFUMI Domestic Violence Helpline",
            service_type="Counselling & Shelter",
            description=(
                "Confidential helpline and support services for "
                "women, children, and youth affected by domestic "
                "violence."
            ),
            phone_number="0800200250",
            coverage="National",
            is_emergency_service=False,
        )
        fida = self._support_service(
            name="FIDA-Uganda",
            service_type="Legal Aid",
            description=(
                "Free legal aid and support from the Uganda "
                "Association of Women Lawyers."
            ),
            phone_number="0800111511",
            coverage="National",
            is_emergency_service=False,
        )
        rights_topic.support_services.add(police_gbv, mifumi, fida)

    def _seed_sexual_harassment(self):
        situation, _ = Situation.objects.update_or_create(
            slug="sexual-harassment",
            defaults={
                "title": "I'm experiencing sexual harassment",
                "description": (
                    "Information on your rights if you're facing "
                    "sexual harassment, particularly at work, and how "
                    "to report it safely."
                ),
                "risk_level": "sensitive",
                "is_active": True,
            },
        )

        rights_topic, _ = RightsTopic.objects.update_or_create(
            slug="sexual-harassment-rights",
            defaults={
                "title": "Your rights against sexual harassment",
                "summary": (
                    "Ugandan law requires workplaces to have a sexual "
                    "harassment policy and gives you the right to "
                    "report confidentially, including to a Labour "
                    "Officer."
                ),
                "risk_level": "sensitive",
                "source_name": (
                    "Employment Act, 2006, s.7(1). Also see Employment "
                    "(Sexual Harassment) Regulations, 2012 (S.I. 15 of "
                    "2012), https://ulii.org/en/akn/ug/act/si/2012/15/"
                    "eng@2012-04-20/source (regulations URL not "
                    "independently verified)"
                ),
                "source_url": (
                    "https://ulii.org/en/akn/ug/act/2006/6/"
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

        SafetyResponse.objects.update_or_create(
            rights_topic=rights_topic,
            trigger_key="default",
            defaults={
                "message": (
                    "This section covers sexual harassment, which can "
                    "be difficult to read about. Confidential help is "
                    "available if you'd rather talk to someone first "
                    "- FIDA-Uganda (0800 111 511) offers free, "
                    "confidential legal support."
                ),
                "is_active": True,
            },
        )

        self._seed_action_steps(
            rights_topic,
            [
                (
                    1,
                    "Write down what happened",
                    "Note the date, what happened, and any witnesses, "
                    "as soon as you safely can.",
                    False,
                ),
                (
                    2,
                    "Report it internally first, if safe to do so",
                    "Workplaces with 25+ staff are legally required to "
                    "have a sexual harassment policy and committee - "
                    "you can report to them or your supervisor.",
                    False,
                ),
                (
                    3,
                    "Report to a Labour Officer if needed",
                    "If it's unresolved or you don't feel safe reporting "
                    "internally, a Labour Officer must keep your report "
                    "confidential.",
                    False,
                ),
                (
                    4,
                    "Get free legal advice",
                    "FIDA-Uganda and the Uganda Law Society Legal Aid "
                    "Project both offer free, confidential support.",
                    False,
                ),
            ],
        )

        fida = self._support_service(
            name="FIDA-Uganda",
            service_type="Legal Aid",
            description=(
                "Free legal aid and support from the Uganda "
                "Association of Women Lawyers."
            ),
            phone_number="0800111511",
            coverage="National",
            is_emergency_service=False,
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
        rights_topic.support_services.add(fida, legal_aid)

