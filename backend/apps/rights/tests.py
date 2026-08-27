from django.test import TestCase
from rest_framework.test import APIClient

from apps.content.models import ChannelContent
from apps.rights.models import (
    ActionStep,
    LegalProvision,
    RightsTopic,
    SafetyResponse,
    Situation,
    SituationRightsTopic,
)
from apps.rights.services import (
    analyse_concern,
    get_channel_text,
    get_safety_message,
    get_situation_detail,
    list_active_situations,
)
from apps.support.models import SupportService


class RightsServicesTests(TestCase):
    def setUp(self):
        self.situation = Situation.objects.create(
            slug="home-safety",
            title="I don't feel safe at home",
            description="For situations involving abuse or fear at home.",
            risk_level="high_risk",
        )
        self.inactive_situation = Situation.objects.create(
            slug="inactive-situation",
            title="Inactive",
            is_active=False,
        )
        self.topic = RightsTopic.objects.create(
            slug="domestic-violence-rights",
            title="Domestic Violence & Your Rights",
            summary="The Domestic Violence Act protects you from abuse.",
            risk_level="high_risk",
        )
        SituationRightsTopic.objects.create(
            situation=self.situation, rights_topic=self.topic
        )
        self.action_step = ActionStep.objects.create(
            rights_topic=self.topic,
            order=1,
            title="Move somewhere safer",
            description="If you can safely do so, move to a safer location.",
            is_safety_critical=True,
        )
        self.safety_response = SafetyResponse.objects.create(
            rights_topic=self.topic,
            trigger_key="immediate_danger",
            message="Your safety matters. Call Sauti 116.",
        )
        self.support_service = SupportService.objects.create(
            name="Sauti 116 - Child & GBV Helpline",
            service_type="helpline",
            phone_number="116",
        )
        self.topic.support_services.add(self.support_service)


        self.legal_provision = LegalProvision.objects.create(
            rights_topic=self.topic,
            source_type="act",
            law_title="Domestic Violence Act, 2010",
            provision_reference="Section 10",
            provision_heading="Protection orders",
            provision_text=(
                "Reviewed legal provision text."
            ),
            plain_language_explanation=(
                "A person experiencing domestic violence may "
                "seek a protection order where the law allows."
            ),
            source_url="https://example.com/domestic-violence-act",
            jurisdiction="Uganda",
            verification_status="verified",
            order=1,
            is_active=True,
        )

    def test_list_active_situations_returns_active_only(self):
        result = list_active_situations()
        slugs = [item["slug"] for item in result]
        self.assertIn("home-safety", slugs)
        self.assertNotIn("inactive-situation", slugs)

    def test_get_situation_detail_returns_full_picture(self):
        detail = get_situation_detail("home-safety")
        self.assertEqual(detail["slug"], "home-safety")
        self.assertEqual(len(detail["rights_topics"]), 1)
        topic = detail["rights_topics"][0]
        self.assertEqual(topic["slug"], "domestic-violence-rights")
        self.assertEqual(len(topic["action_steps"]), 1)
        self.assertEqual(
            topic["action_steps"][0]["title"], "Move somewhere safer"
        )
        self.assertEqual(len(topic["safety_responses"]), 1)
        self.assertEqual(len(topic["support_services"]), 1)
        self.assertEqual(
            topic["support_services"][0]["name"],
            "Sauti 116 - Child & GBV Helpline",
        )


        self.assertEqual(
            len(topic["legal_provisions"]),
            1,
        )

        self.assertEqual(
            topic["legal_provisions"][0][
                "law_title"
            ],
            "Domestic Violence Act, 2010",
        )

        self.assertEqual(
            topic["legal_provisions"][0][
                "provision_reference"
            ],
            "Section 10",
        )

    def test_get_situation_detail_returns_none_for_missing_slug(self):
        self.assertIsNone(get_situation_detail("does-not-exist"))

    def test_get_channel_text_returns_text_when_exists(self):
        ChannelContent.objects.create(
            content_key="home_safety_intro",
            channel="sms",
            language="en",
            text="Custom SMS intro text.",
        )
        result = get_channel_text("home-safety", "sms", "en")
        self.assertEqual(result, "Custom SMS intro text.")

    def test_get_channel_text_returns_none_when_missing(self):
        result = get_channel_text("home-safety", "sms", "en")
        self.assertIsNone(result)

    def test_get_safety_message_returns_message_for_trigger_key(self):
        message = get_safety_message("home-safety", "immediate_danger")
        self.assertEqual(message, "Your safety matters. Call Sauti 116.")

    def test_get_safety_message_returns_none_when_no_match(self):
        message = get_safety_message("home-safety", "nonexistent_trigger")
        self.assertIsNone(message)

    def test_get_safety_message_falls_back_to_default_trigger_key(self):
        situation = Situation.objects.create(
            slug="fallback-test", title="Fallback Test", risk_level="high_risk"
        )
        topic = RightsTopic.objects.create(
            slug="fallback-topic", title="Fallback Topic", summary="summary"
        )
        SituationRightsTopic.objects.create(situation=situation, rights_topic=topic)
        SafetyResponse.objects.create(
            rights_topic=topic,
            trigger_key="default",
            message="Fallback safety message.",
        )
        message = get_safety_message("fallback-test", "immediate_danger")
        self.assertEqual(message, "Fallback safety message.")



class LegalProvisionTests(TestCase):
    def test_legal_provision_preserves_structured_reference(
        self,
    ):
        topic = RightsTopic.objects.create(
            slug="equality-rights",
            title="Equality rights",
            summary="General equality information.",
        )

        provision = LegalProvision.objects.create(
            rights_topic=topic,
            source_type="constitution",
            law_title=(
                "Constitution of the Republic of Uganda"
            ),
            provision_reference="Article 21",
            provision_heading=(
                "Equality and freedom from discrimination"
            ),
            plain_language_explanation=(
                "The Constitution protects equality "
                "before and under the law."
            ),
            verification_status="review_required",
        )

        self.assertEqual(
            provision.provision_reference,
            "Article 21",
        )

        self.assertEqual(
            provision.source_type,
            "constitution",
        )

        self.assertEqual(
            str(provision),
            (
                "Constitution of the Republic of Uganda "
                "— Article 21"
            ),
        )



class ConcernAnalysisTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.work = Situation.objects.create(
            slug="problem-at-work",
            title="Problem at work",
            description="Workplace rights problem.",
        )

        self.work_topic = RightsTopic.objects.create(
            slug="workplace-rights",
            title="Workplace rights",
            summary="Workplace legal information.",
        )

        SituationRightsTopic.objects.create(
            situation=self.work,
            rights_topic=self.work_topic,
        )

        LegalProvision.objects.create(
            rights_topic=self.work_topic,
            source_type="act",
            law_title="Employment Act",
            provision_reference="Section 65C",
            provision_heading="Protected reasons",
            plain_language_explanation=(
                "Certain protected reasons do not "
                "justify dismissal."
            ),
            source_url="https://example.com/employment",
            verification_status="review_required",
        )

        ActionStep.objects.create(
            rights_topic=self.work_topic,
            order=1,
            title="Keep records",
            description="Keep useful employment records.",
        )

        self.eviction = Situation.objects.create(
            slug="facing-eviction",
            title="Eviction or housing problem",
            description="Tenant and eviction rights.",
        )

        self.eviction_topic = RightsTopic.objects.create(
            slug="housing-and-eviction-rights",
            title="Tenant rights",
            summary="Tenant legal information.",
        )

        SituationRightsTopic.objects.create(
            situation=self.eviction,
            rights_topic=self.eviction_topic,
        )

        LegalProvision.objects.create(
            rights_topic=self.eviction_topic,
            source_type="act",
            law_title="Landlord and Tenant Act, 2022",
            provision_reference="Section 45",
            provision_heading="Unlawful eviction",
            plain_language_explanation=(
                "A landlord must follow the law."
            ),
        )

        self.domestic = Situation.objects.create(
            slug="domestic-violence",
            title="Domestic violence",
            description="Domestic violence protection.",
            risk_level="high_risk",
        )

        self.domestic_topic = RightsTopic.objects.create(
            slug="domestic-violence-protection",
            title="Protection rights",
            summary="Domestic violence law.",
            risk_level="high_risk",
        )

        SituationRightsTopic.objects.create(
            situation=self.domestic,
            rights_topic=self.domestic_topic,
        )

        SafetyResponse.objects.create(
            rights_topic=self.domestic_topic,
            trigger_key="default",
            message="Prioritise your immediate safety.",
        )

        self.sexual = Situation.objects.create(
            slug="sexual-harassment",
            title="Sexual harassment",
            description="Sexual harassment rights.",
            risk_level="sensitive",
        )

        self.sexual_topic = RightsTopic.objects.create(
            slug="sexual-harassment-rights",
            title="Sexual harassment rights",
            summary="Sexual harassment law.",
            risk_level="sensitive",
        )

        SituationRightsTopic.objects.create(
            situation=self.sexual,
            rights_topic=self.sexual_topic,
        )

        LegalProvision.objects.create(
            rights_topic=self.sexual_topic,
            source_type="act",
            law_title="Employment Act",
            provision_reference="Section 6",
            provision_heading="Sexual harassment",
            plain_language_explanation=(
                "The Employment Act addresses "
                "sexual harassment in employment."
            ),
        )

    def test_service_matches_pregnancy_dismissal_to_work(self):
        result = analyse_concern(
            "My boss fired me because I became pregnant."
        )

        self.assertIsNotNone(result)

        self.assertEqual(
            result["situation"]["slug"],
            "problem-at-work",
        )

        provisions = result["situation"][
            "rights_topics"
        ][0]["legal_provisions"]

        self.assertEqual(
            provisions[0]["provision_reference"],
            "Section 65C",
        )

    def test_service_matches_eviction(self):
        result = analyse_concern(
            "My landlord says I must leave the house."
        )

        self.assertEqual(
            result["situation"]["slug"],
            "facing-eviction",
        )

    def test_service_prioritises_sexual_harassment(self):
        result = analyse_concern(
            "My boss keeps making unwanted sexual "
            "comments at work."
        )

        self.assertEqual(
            result["situation"]["slug"],
            "sexual-harassment",
        )

    def test_service_matches_domestic_violence(self):
        result = analyse_concern(
            "My abusive partner beats me at home."
        )

        self.assertEqual(
            result["situation"]["slug"],
            "domestic-violence",
        )

        responses = result["situation"][
            "rights_topics"
        ][0]["safety_responses"]

        self.assertEqual(
            len(responses),
            1,
        )

    def test_service_returns_none_for_unknown_concern(self):
        result = analyse_concern(
            "I want information about registering a company."
        )

        self.assertIsNone(result)

    def test_api_returns_grounded_match(self):
        response = self.client.post(
            "/api/rights/analyse/",
            {
                "concern": (
                    "My employer fired me "
                    "because I became pregnant."
                )
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.data["matched"],
        )

        self.assertEqual(
            response.data["situation"]["slug"],
            "problem-at-work",
        )

    def test_api_returns_unmatched_without_inventing_law(self):
        response = self.client.post(
            "/api/rights/analyse/",
            {
                "concern": (
                    "How do I register a new company?"
                )
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            response.data["matched"],
        )

        self.assertNotIn(
            "situation",
            response.data,
        )

    def test_api_rejects_blank_concern(self):
        response = self.client.post(
            "/api/rights/analyse/",
            {
                "concern": "",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )
