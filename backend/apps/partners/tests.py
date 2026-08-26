from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.support.models import SupportService

from .models import (
    PartnerMember,
    PartnerOrganisation,
    PartnerServiceConfiguration,
)


User = get_user_model()


class PartnerAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user_one = User.objects.create_user(
            username="partner_one",
            password="TestPassword123!",
            email="partner-one@example.com",
        )

        self.user_two = User.objects.create_user(
            username="partner_two",
            password="TestPassword123!",
            email="partner-two@example.com",
        )

        service_one = SupportService.objects.create(
            name="Partner Organisation One",
            service_type="Legal Aid",
            verification_status="review_required",
            is_active=True,
        )

        service_two = SupportService.objects.create(
            name="Partner Organisation Two",
            service_type="Community Support",
            verification_status="review_required",
            is_active=True,
        )

        self.organisation_one = (
            PartnerOrganisation.objects.create(
                support_service=service_one,
                organisation_type="legal_aid",
                registration_number="TEST-001",
                headquarters_district="Kampala",
                is_active=True,
            )
        )

        self.organisation_two = (
            PartnerOrganisation.objects.create(
                support_service=service_two,
                organisation_type="ngo",
                registration_number="TEST-002",
                headquarters_district="Wakiso",
                is_active=True,
            )
        )

        PartnerServiceConfiguration.objects.create(
            organisation=self.organisation_one
        )

        PartnerServiceConfiguration.objects.create(
            organisation=self.organisation_two
        )

        PartnerMember.objects.create(
            organisation=self.organisation_one,
            user=self.user_one,
            role="owner",
            is_active=True,
        )

        PartnerMember.objects.create(
            organisation=self.organisation_two,
            user=self.user_two,
            role="owner",
            is_active=True,
        )

    def test_anonymous_user_cannot_access_partner(self):
        response = self.client.get(
            f"/api/partners/{self.organisation_one.id}/"
        )

        self.assertIn(
            response.status_code,
            [401, 403],
        )

    def test_partner_can_access_own_organisation(self):
        self.client.force_authenticate(
            user=self.user_one
        )

        response = self.client.get(
            f"/api/partners/{self.organisation_one.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["support_service"]["name"],
            "Partner Organisation One",
        )

    def test_partner_cannot_access_other_organisation(self):
        self.client.force_authenticate(
            user=self.user_one
        )

        response = self.client.get(
            f"/api/partners/{self.organisation_two.id}/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_owner_can_update_service_configuration(self):
        self.client.force_authenticate(
            user=self.user_one
        )

        response = self.client.patch(
            (
                f"/api/partners/"
                f"{self.organisation_one.id}/services/"
            ),
            {
                "languages": [
                    "English",
                    "Luganda",
                ],
                "districts_served": [
                    "Kampala",
                    "Wakiso",
                ],
                "accepting_referrals": True,
                "weekly_referral_limit": 10,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.data["accepting_referrals"]
        )

        self.assertEqual(
            response.data["weekly_referral_limit"],
            10,
        )

    def test_owner_can_submit_verification(self):
        self.client.force_authenticate(
            user=self.user_one
        )

        response = self.client.post(
            (
                f"/api/partners/"
                f"{self.organisation_one.id}/verification/"
            ),
            {
                "declaration_accurate": True,
                "declaration_authorised": True,
                "declaration_consent": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["status"],
            "submitted",
        )

        self.assertEqual(
            response.data["submitted_by"],
            self.user_one.id,
        )