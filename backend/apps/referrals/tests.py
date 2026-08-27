from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.partners.models import (
    PartnerMember,
    PartnerOrganisation,
    PartnerServiceConfiguration,
    PartnerVerificationRequest,
)
from apps.support.models import SupportService

from .models import (
    Referral,
    ReferralStatusHistory,
)


User = get_user_model()


class ReferralAPITests(TestCase):
    def setUp(self):
        self.client_one = APIClient()
        self.client_two = APIClient()

        self.user_one = User.objects.create_user(
            username="referral_partner_one",
            password="TestPassword123!",
        )

        self.user_two = User.objects.create_user(
            username="referral_partner_two",
            password="TestPassword123!",
        )

        service_one = SupportService.objects.create(
            name="Referral Partner One",
            service_type="Legal Aid",
            verification_status="verified",
            is_active=True,
        )

        service_two = SupportService.objects.create(
            name="Referral Partner Two",
            service_type="Community Support",
            verification_status="verified",
            is_active=True,
        )

        self.organisation_one = (
            PartnerOrganisation.objects.create(
                support_service=service_one,
                organisation_type="legal_aid",
                is_active=True,
            )
        )

        self.organisation_two = (
            PartnerOrganisation.objects.create(
                support_service=service_two,
                organisation_type="ngo",
                is_active=True,
            )
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

        self.referral = Referral.objects.create(
            reference="SY-REF-TEST-001",
            organisation=self.organisation_one,
            summary="Test referral.",
            district="Kampala",
            language="English",
            preferred_support_channel="phone",
            citizen_consent_to_share=True,
            status="new",
        )

        ReferralStatusHistory.objects.create(
            referral=self.referral,
            from_status="",
            to_status="new",
            note="Referral created.",
        )

        self.client_one.force_authenticate(
            user=self.user_one
        )

        self.client_two.force_authenticate(
            user=self.user_two
        )

    def test_partner_can_access_own_referral(self):
        response = self.client_one.get(
            f"/api/referrals/{self.referral.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_partner_cannot_access_other_referral(self):
        response = self.client_two.get(
            f"/api/referrals/{self.referral.id}/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_referral_list_is_organisation_scoped(self):
        response_one = self.client_one.get(
            "/api/referrals/"
        )

        response_two = self.client_two.get(
            "/api/referrals/"
        )

        self.assertEqual(
            response_one.status_code,
            200,
        )

        self.assertEqual(
            len(response_one.data),
            1,
        )

        self.assertEqual(
            response_two.status_code,
            200,
        )

        self.assertEqual(
            len(response_two.data),
            0,
        )

    def test_status_transition_is_recorded(self):
        response = self.client_one.post(
            f"/api/referrals/{self.referral.id}/status/",
            {
                "status": "reviewing",
                "note": "Review started.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["status"],
            "reviewing",
        )

        history = (
            ReferralStatusHistory.objects
            .filter(referral=self.referral)
            .order_by("created_at")
        )

        self.assertEqual(
            history.count(),
            2,
        )

        latest = history.last()

        self.assertEqual(
            latest.from_status,
            "new",
        )

        self.assertEqual(
            latest.to_status,
            "reviewing",
        )

        self.assertEqual(
            latest.changed_by,
            self.user_one,
        )

    def test_invalid_status_transition_is_rejected(self):
        response = self.client_one.post(
            f"/api/referrals/{self.referral.id}/status/",
            {
                "status": "completed",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.referral.refresh_from_db()

        self.assertEqual(
            self.referral.status,
            "new",
        )


class CitizenReferralTestOrganisationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        service = SupportService.objects.create(
            name="Citizen Referral Test Partner",
            service_type="Legal Aid",
            verification_status="verified",
            is_active=True,
        )

        self.organisation = PartnerOrganisation.objects.create(
            support_service=service,
            organisation_type="legal_aid",
            is_active=True,
            is_test=True,
        )

        PartnerServiceConfiguration.objects.create(
            organisation=self.organisation,
            rights_categories=["work-employment"],
            languages=["English"],
            support_channels=["phone"],
            districts_served=["Kampala"],
            accepting_referrals=True,
        )

        PartnerVerificationRequest.objects.create(
            organisation=self.organisation,
            status="verified",
        )

    def test_test_partner_cannot_receive_citizen_referral(self):
        response = self.client.post(
            "/api/referrals/citizen/create/",
            {
                "organisation": self.organisation.id,
                "rights_topic": None,
                "summary": "Citizen needs legal assistance.",
                "district": "Kampala",
                "language": "English",
                "preferred_support_channel": "phone",
                "citizen_consent_to_share": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            Referral.objects.count(),
            0,
        )


class ReferralContactPhoneFieldTests(TestCase):
    def test_contact_phone_defaults_to_blank(self):
        service = SupportService.objects.create(
            name="Contact Phone Field Test Partner",
            service_type="Legal Aid",
            verification_status="verified",
            is_active=True,
        )

        organisation = PartnerOrganisation.objects.create(
            support_service=service,
            organisation_type="legal_aid",
            is_active=True,
        )

        referral = Referral.objects.create(
            reference="SY-REF-CONTACT-PHONE-TEST",
            organisation=organisation,
            citizen_consent_to_share=True,
            status="new",
        )

        self.assertEqual(referral.contact_phone, "")

    def test_contact_phone_can_be_set(self):
        service = SupportService.objects.create(
            name="Contact Phone Field Test Partner Two",
            service_type="Legal Aid",
            verification_status="verified",
            is_active=True,
        )

        organisation = PartnerOrganisation.objects.create(
            support_service=service,
            organisation_type="legal_aid",
            is_active=True,
        )

        referral = Referral.objects.create(
            reference="SY-REF-CONTACT-PHONE-TEST-2",
            organisation=organisation,
            contact_phone="+256700000000",
            citizen_consent_to_share=True,
            status="new",
        )

        self.assertEqual(referral.contact_phone, "+256700000000")


class ReferralGenerateReferenceTests(TestCase):
    def test_generate_reference_has_expected_prefix_and_length(self):
        reference = Referral.generate_reference()

        self.assertTrue(reference.startswith("SY-REF-"))
        self.assertEqual(len(reference), len("SY-REF-") + 32)

    def test_generate_reference_is_unique_across_calls(self):
        first = Referral.generate_reference()
        second = Referral.generate_reference()

        self.assertNotEqual(first, second)
