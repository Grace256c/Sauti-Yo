from django.test import TestCase

from apps.legal_knowledge.models import (
    LegalDocument,
    LegalSection,
)
from apps.legal_knowledge.services import (
    search_legal_sections,
)


class LegalSectionSearchTests(TestCase):
    def setUp(self):
        self.constitution = LegalDocument.objects.create(
            title="Constitution of the Republic of Uganda",
            short_title="Constitution of Uganda",
            document_type="constitution",
        )

        self.employment_act = LegalDocument.objects.create(
            title="Employment Act",
            short_title="Employment Act",
            document_type="act",
        )

    def create_section(
        self,
        document,
        section_type,
        number,
        heading,
    ):
        return LegalSection.objects.create(
            document=document,
            section_type=section_type,
            section_number=number,
            heading=heading,
            text=f"Verified text for {heading}.",
        )

    def test_article_reference_only_matches_article(self):
        article = self.create_section(
            self.constitution,
            "article",
            "24",
            "Protection of dignity",
        )

        self.create_section(
            self.employment_act,
            "section",
            "24",
            "Employment provision",
        )

        results = search_legal_sections(
            "What does Article 24 say?"
        )

        self.assertEqual(results, [article])

    def test_section_reference_does_not_match_article(self):
        section = self.create_section(
            self.employment_act,
            "section",
            "24",
            "Employment provision",
        )

        self.create_section(
            self.constitution,
            "article",
            "24",
            "Protection of dignity",
        )

        results = search_legal_sections(
            "What does Section 24 say?"
        )

        self.assertEqual(results, [section])

    def test_constitution_reference_filters_document(self):
        constitution_article = self.create_section(
            self.constitution,
            "article",
            "24",
            "Protection of dignity",
        )

        other_document = LegalDocument.objects.create(
            title="Example Act",
            short_title="Example Act",
            document_type="act",
        )

        self.create_section(
            other_document,
            "article",
            "24",
            "Unrelated article",
        )

        results = search_legal_sections(
            "What does Article 24 of the Constitution say?"
        )

        self.assertEqual(
            results,
            [constitution_article],
        )

    def test_ambiguous_section_across_acts_is_not_guessed(self):
        self.create_section(
            self.employment_act,
            "section",
            "38",
            "Employment section 38",
        )

        second_act = LegalDocument.objects.create(
            title="Landlord and Tenant Act",
            short_title="Landlord and Tenant Act",
            document_type="act",
        )

        self.create_section(
            second_act,
            "section",
            "38",
            "Tenancy section 38",
        )

        results = search_legal_sections(
            "What does Section 38 say?"
        )

        self.assertEqual(results, [])

    def test_single_unambiguous_section_can_be_returned(self):
        section = self.create_section(
            self.employment_act,
            "section",
            "65C",
            "Protected reasons",
        )

        results = search_legal_sections(
            "Explain Section 65C"
        )

        self.assertEqual(results, [section])
