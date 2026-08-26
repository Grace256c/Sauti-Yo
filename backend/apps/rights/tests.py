from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient

from .models import (

    IssueOutcome,
    RightsTopic,
    Situation,
    
)


class IssueOutcomeAPITests(TestCase):

    def test_unlinked_issue_outcome_returns_200(self):
        IssueOutcome.objects.create(
        category_slug="safety-protection",
        issue_slug="violence",
        heading="Your situation involves a serious safety concern.",
        introduction=(
            "This outcome is mapped to the citizen rights journey "
            "and requires verified content before production use."
        ),
    )

        response = self.client.get(
        "/api/rights/outcomes/safety-protection/violence/",
        HTTP_HOST="localhost",
    )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["situation"])
        self.assertEqual(response.data["rights_topics"], [])
        
    def setUp(self):
        self.client = APIClient()

        self.situation = Situation.objects.create(
            slug="problem-at-work",
            title="I have a problem at work",
            description="Workplace problem",
            risk_level="standard",
        )

        self.topic = RightsTopic.objects.create(
            slug="workplace-rights",
            title="Understanding your workplace rights",
            summary="Workplace rights information",
        )

        self.outcome = IssueOutcome.objects.create(
            category_slug="work-employment",
            issue_slug="unpaid",
            heading="Your situation appears to involve a pay problem.",
            introduction="The issue appears to involve unpaid wages.",
            situation=self.situation,
            evidence_items=[
                "Employment contract",
                "Payslips",
            ],
        )

        self.outcome.rights_topics.add(self.topic)

    def test_valid_issue_outcome_returns_200(self):
        response = self.client.get(
            "/api/rights/outcomes/work-employment/unpaid/",
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["category_slug"],
            "work-employment",
        )
        self.assertEqual(
            response.data["issue_slug"],
            "unpaid",
        )

    def test_invalid_issue_outcome_returns_404(self):
        response = self.client.get(
            "/api/rights/outcomes/work-employment/not-real/",
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 404)

    def test_inactive_issue_outcome_returns_404(self):
        self.outcome.is_active = False
        self.outcome.save()

        response = self.client.get(
            "/api/rights/outcomes/work-employment/unpaid/",
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 404)

    def test_response_contains_linked_rights_topic(self):
        response = self.client.get(
            "/api/rights/outcomes/work-employment/unpaid/",
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["rights_topics"][0]["slug"],
            "workplace-rights",
        )

    def test_duplicate_category_and_issue_is_rejected(self):
        with self.assertRaises(IntegrityError):
            IssueOutcome.objects.create(
                category_slug="work-employment",
                issue_slug="unpaid",
                heading="Duplicate",
                introduction="Duplicate outcome",
            )
