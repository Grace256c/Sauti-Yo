from django.test import TestCase

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
