from django.core.management.base import BaseCommand
from django.db import transaction

from apps.rights.models import (
    LegalProvision,
    RightsTopic,
)


class Command(BaseCommand):
    help = (
        "Seed reviewed-source legal knowledge used by "
        "the Sauti Yo Rights-to-Action engine."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        self._seed_workplace()
        self._seed_eviction()
        self._seed_domestic_violence()
        self._seed_sexual_harassment()

        self.stdout.write(
            self.style.SUCCESS(
                "Legal knowledge seed completed."
            )
        )

        self.stdout.write(
            self.style.WARNING(
                "Seeded legal provisions remain "
                "review_required until approved by "
                "an authorised legal reviewer."
            )
        )

    def _seed_provisions(
        self,
        topic,
        provisions,
    ):
        for item in provisions:
            provision, created = (
                LegalProvision.objects.update_or_create(
                    rights_topic=topic,
                    law_title=item["law_title"],
                    provision_reference=item[
                        "provision_reference"
                    ],
                    defaults={
                        "source_type":
                            item["source_type"],
                        "provision_heading":
                            item[
                                "provision_heading"
                            ],
                        "provision_text":
                            item.get(
                                "provision_text",
                                "",
                            ),
                        "plain_language_explanation":
                            item[
                                "plain_language_explanation"
                            ],
                        "source_url":
                            item["source_url"],
                        "jurisdiction":
                            item.get(
                                "jurisdiction",
                                "Uganda",
                            ),
                        "verification_status":
                            "review_required",
                        "order":
                            item["order"],
                        "is_active":
                            True,
                    },
                )
            )

            self.stdout.write(
                (
                    "Created"
                    if created
                    else "Updated"
                )
                + ": "
                + provision.law_title
                + " — "
                + provision.provision_reference
            )

    def _seed_workplace(self):
        topic = RightsTopic.objects.get(
            slug="workplace-rights",
        )

        self._seed_provisions(
            topic,
            [
                {
                    "source_type":
                        "constitution",
                    "law_title":
                        (
                            "Constitution of the "
                            "Republic of Uganda"
                        ),
                    "provision_reference":
                        "Article 21",
                    "provision_heading":
                        (
                            "Equality and freedom "
                            "from discrimination"
                        ),
                    "plain_language_explanation":
                        (
                            "Everyone is equal before "
                            "and under the law and is "
                            "entitled to equal protection "
                            "of the law. The Constitution "
                            "also protects people from "
                            "discrimination on grounds "
                            "including sex, race, colour, "
                            "ethnic origin, tribe, birth, "
                            "creed or religion, social or "
                            "economic standing, political "
                            "opinion, and disability."
                        ),
                    "source_url":
                        (
                            "https://ulii.org/en/akn/ug/"
                            "act/statute/1995/"
                            "constitution/"
                            "eng@2023-12-31"
                        ),
                    "order":
                        1,
                },
                {
                    "source_type":
                        "act",
                    "law_title":
                        "Employment Act",
                    "provision_reference":
                        "Section 5",
                    "provision_heading":
                        (
                            "Discrimination in "
                            "employment"
                        ),
                    "plain_language_explanation":
                        (
                            "Discrimination in employment "
                            "is unlawful. Employment "
                            "decisions should not unfairly "
                            "disadvantage a person on "
                            "protected grounds such as "
                            "race, colour, sex, religion, "
                            "political opinion, national "
                            "extraction, social origin, "
                            "HIV status, or disability. "
                            "The law also requires equal "
                            "remuneration for male and "
                            "female employees for work "
                            "of equal value."
                        ),
                    "source_url":
                        (
                            "https://ulii.org/en/akn/ug/"
                            "act/2006/6/"
                            "eng@2026-06-05"
                        ),
                    "order":
                        2,
                },
                {
                    "source_type":
                        "act",
                    "law_title":
                        "Employment Act",
                    "provision_reference":
                        "Section 6A",
                    "provision_heading":
                        (
                            "Prohibition of intimidation "
                            "or harassment against an "
                            "employee"
                        ),
                    "plain_language_explanation":
                        (
                            "An employer or the employer's "
                            "agent must not intimidate or "
                            "harass an employee at the "
                            "workplace. This includes "
                            "certain written, verbal or "
                            "physical abuse and behaviour "
                            "that interferes with work or "
                            "creates an intimidating, "
                            "hostile or offensive working "
                            "environment."
                        ),
                    "source_url":
                        (
                            "https://ulii.org/en/akn/ug/"
                            "act/2006/6/"
                            "eng@2026-06-05"
                        ),
                    "order":
                        3,
                },
                {
                    "source_type":
                        "act",
                    "law_title":
                        "Employment Act",
                    "provision_reference":
                        "Section 65C",
                    "provision_heading":
                        (
                            "Circumstances that do not "
                            "warrant dismissal or "
                            "disciplinary penalty"
                        ),
                    "plain_language_explanation":
                        (
                            "An employer must not dismiss "
                            "or discipline an employee for "
                            "certain protected reasons. "
                            "These include pregnancy, "
                            "taking lawful leave, lawful "
                            "trade union involvement, "
                            "certain protected personal "
                            "characteristics, or bringing "
                            "a complaint or legal "
                            "proceeding against an "
                            "employer, subject to the "
                            "conditions set out in the law."
                        ),
                    "source_url":
                        (
                            "https://ulii.org/en/akn/ug/"
                            "act/2006/6/"
                            "eng@2026-06-05"
                        ),
                    "order":
                        4,
                },
            ],
        )


    def _seed_eviction(self):
        topic = RightsTopic.objects.get(
            slug="housing-and-eviction-rights",
        )

        self._seed_provisions(
            topic,
            [
                {
                    "source_type": "act",
                    "law_title": (
                        "Landlord and Tenant Act, 2022"
                    ),
                    "provision_reference": "Section 38",
                    "provision_heading": (
                        "Termination after notice"
                    ),
                    "plain_language_explanation": (
                        "Where this section applies to a "
                        "residential tenancy, the Act sets "
                        "minimum notice periods for termination. "
                        "A weekly tenancy requires seven days' "
                        "notice, a monthly tenancy requires "
                        "thirty days' notice, and a year-to-year "
                        "tenancy requires sixty days' notice. "
                        "The parties may agree to a longer period."
                    ),
                    "source_url": (
                        "https://ulii.org/en/akn/ug/"
                        "act/2022/9/"
                        "eng@2023-12-31"
                    ),
                    "order": 1,
                },
                {
                    "source_type": "act",
                    "law_title": (
                        "Landlord and Tenant Act, 2022"
                    ),
                    "provision_reference": "Section 41",
                    "provision_heading": (
                        "Tenant or landlord may challenge "
                        "termination in court"
                    ),
                    "plain_language_explanation": (
                        "A tenant or landlord may challenge "
                        "termination of a tenancy in court. "
                        "If the court finds that the termination "
                        "was not justified or did not comply with "
                        "the Act, it may reinstate the tenancy, "
                        "award damages, or give another "
                        "appropriate remedy."
                    ),
                    "source_url": (
                        "https://ulii.org/en/akn/ug/"
                        "act/2022/9/"
                        "eng@2023-12-31"
                    ),
                    "order": 2,
                },
                {
                    "source_type": "act",
                    "law_title": (
                        "Landlord and Tenant Act, 2022"
                    ),
                    "provision_reference": "Section 45",
                    "provision_heading": (
                        "Unlawful eviction of tenant"
                    ),
                    "plain_language_explanation": (
                        "A landlord must not evict or compel "
                        "a tenant to leave except in accordance "
                        "with the Act or the tenancy agreement. "
                        "A tenant affected by an unlawful eviction "
                        "may seek relief from court, and the Act "
                        "provides for compensation in qualifying "
                        "cases."
                    ),
                    "source_url": (
                        "https://ulii.org/en/akn/ug/"
                        "act/2022/9/"
                        "eng@2023-12-31"
                    ),
                    "order": 3,
                },
            ],
        )

    def _seed_domestic_violence(self):
        topic = RightsTopic.objects.get(
            slug="domestic-violence-protection",
        )

        self._seed_provisions(
            topic,
            [
                {
                    "source_type": "constitution",
                    "law_title": (
                        "Constitution of the Republic of Uganda"
                    ),
                    "provision_reference": "Article 24",
                    "provision_heading": (
                        "Respect for human dignity and "
                        "protection from inhuman treatment"
                    ),
                    "plain_language_explanation": (
                        "The Constitution provides that no person "
                        "shall be subjected to torture or cruel, "
                        "inhuman or degrading treatment or "
                        "punishment."
                    ),
                    "source_url": (
                        "https://ulii.org/en/akn/ug/"
                        "act/statute/1995/constitution/"
                        "eng@2023-12-31"
                    ),
                    "order": 1,
                },
                {
                    "source_type": "act",
                    "law_title": "Domestic Violence Act, 2010",
                    "provision_reference": "Section 9",
                    "provision_heading": (
                        "Application for protection order"
                    ),
                    "plain_language_explanation": (
                        "A victim, or a representative of a "
                        "victim, may apply to a magistrate's "
                        "court for a protection order. The Act "
                        "also provides for urgent applications "
                        "where waiting for ordinary court hours "
                        "may cause undue hardship."
                    ),
                    "source_url": (
                        "https://ulii.org/en/akn/ug/"
                        "act/2010/3/"
                        "eng@2023-12-31"
                    ),
                    "order": 2,
                },
                {
                    "source_type": "act",
                    "law_title": "Domestic Violence Act, 2010",
                    "provision_reference": "Section 10",
                    "provision_heading": (
                        "Issue of interim protection order"
                    ),
                    "plain_language_explanation": (
                        "A court may issue an interim protection "
                        "order where there is an immediate need "
                        "to protect a victim from threatened, "
                        "ongoing or past domestic violence."
                    ),
                    "source_url": (
                        "https://ulii.org/en/akn/ug/"
                        "act/2010/3/"
                        "eng@2023-12-31"
                    ),
                    "order": 3,
                },
                {
                    "source_type": "act",
                    "law_title": "Domestic Violence Act, 2010",
                    "provision_reference": "Sections 11–12",
                    "provision_heading": (
                        "Protection orders and their contents"
                    ),
                    "plain_language_explanation": (
                        "The court may issue a protection order "
                        "where domestic violence has occurred, "
                        "is occurring, or is threatened. "
                        "Depending on the circumstances, an order "
                        "may restrict contact or access and may "
                        "require the perpetrator to stay away "
                        "from certain places or leave the home."
                    ),
                    "source_url": (
                        "https://ulii.org/en/akn/ug/"
                        "act/2010/3/"
                        "eng@2023-12-31"
                    ),
                    "order": 4,
                },
            ],
        )

    def _seed_sexual_harassment(self):
        topic = RightsTopic.objects.get(
            slug="sexual-harassment-rights",
        )

        self._seed_provisions(
            topic,
            [
                {
                    "source_type": "act",
                    "law_title": "Employment Act",
                    "provision_reference": "Section 6",
                    "provision_heading": (
                        "Sexual harassment in employment"
                    ),
                    "plain_language_explanation": (
                        "The Employment Act describes sexual "
                        "harassment in employment, including "
                        "unwelcome sexual requests, sexual "
                        "language, visual material or physical "
                        "behaviour that negatively affects an "
                        "employee's work, performance or job "
                        "satisfaction. An affected employee may "
                        "complain to a labour officer."
                    ),
                    "source_url": (
                        "https://ulii.org/en/akn/ug/"
                        "act/2006/6/"
                        "eng@2026-06-05"
                    ),
                    "order": 1,
                },
                {
                    "source_type": "act",
                    "law_title": "Employment Act",
                    "provision_reference": "Section 6A",
                    "provision_heading": (
                        "Prohibition of intimidation or "
                        "harassment against an employee"
                    ),
                    "plain_language_explanation": (
                        "An employer or the employer's agent "
                        "must not intimidate or harass an "
                        "employee at the workplace. The section "
                        "covers certain written, verbal and "
                        "physical abuse and hostile or offensive "
                        "workplace behaviour."
                    ),
                    "source_url": (
                        "https://ulii.org/en/akn/ug/"
                        "act/2006/6/"
                        "eng@2026-06-05"
                    ),
                    "order": 2,
                },
                {
                    "source_type": "constitution",
                    "law_title": (
                        "Constitution of the Republic of Uganda"
                    ),
                    "provision_reference": "Article 21",
                    "provision_heading": (
                        "Equality and freedom from discrimination"
                    ),
                    "plain_language_explanation": (
                        "The Constitution protects equality "
                        "before and under the law and protects "
                        "people from discrimination on specified "
                        "grounds, including sex."
                    ),
                    "source_url": (
                        "https://ulii.org/en/akn/ug/"
                        "act/statute/1995/constitution/"
                        "eng@2023-12-31"
                    ),
                    "order": 3,
                },
            ],
        )
