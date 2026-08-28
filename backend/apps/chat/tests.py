import json
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from apps.chat import services
from apps.rights.models import (
    ActionStep,
    RightsTopic,
    SafetyResponse,
    Situation,
    SituationRightsTopic,
)
from apps.rights.services import get_situation_detail
from apps.support.models import SupportService


def _create_domestic_violence_situation():
    situation = Situation.objects.create(
        slug="domestic-violence",
        title="Domestic violence",
        description="Information on your legal protections.",
        risk_level="high_risk",
    )
    topic = RightsTopic.objects.create(
        slug="domestic-violence-protection",
        title="Your right to protection under the law",
        summary="Uganda's Domestic Violence Act protects you from abuse.",
        risk_level="high_risk",
    )
    SituationRightsTopic.objects.create(situation=situation, rights_topic=topic)
    ActionStep.objects.create(
        rights_topic=topic,
        order=1,
        title="Get to safety first",
        description="Prioritise getting somewhere safe.",
        is_safety_critical=True,
    )
    service = SupportService.objects.create(
        name="Uganda Police GBV Helpline",
        service_type="helpline",
        phone_number="0800199195",
        is_emergency_service=True,
    )
    topic.support_services.add(service)
    return situation


def _create_child_abuse_situation():
    situation = Situation.objects.create(
        slug="child-abuse",
        title="Child abuse or neglect",
        description="Information on a child's legal protections.",
        risk_level="high_risk",
    )
    topic = RightsTopic.objects.create(
        slug="child-protection-rights",
        title="A child's right to protection under the law",
        summary="Uganda's Children Act protects children from abuse.",
        risk_level="high_risk",
    )
    SituationRightsTopic.objects.create(situation=situation, rights_topic=topic)
    return situation


class NormalizeSituationSlugTests(TestCase):
    def test_returns_none_for_empty_input(self):
        self.assertIsNone(services.normalize_situation_slug(""))
        self.assertIsNone(services.normalize_situation_slug(None))

    def test_maps_legacy_home_safety_to_domestic_violence(self):
        self.assertEqual(
            services.normalize_situation_slug("home-safety"),
            "domestic-violence",
        )

    def test_maps_legacy_land_property_to_facing_eviction(self):
        self.assertEqual(
            services.normalize_situation_slug("land-property"),
            "facing-eviction",
        )

    def test_passes_through_slugs_without_an_alias(self):
        self.assertEqual(
            services.normalize_situation_slug("child-abuse"),
            "child-abuse",
        )


class FindSituationTests(TestCase):
    def test_keyword_match_is_aliased_to_current_pilot_slug(self):
        _create_domestic_violence_situation()
        detail = services.find_situation("my husband is beating me")
        self.assertIsNotNone(detail)
        self.assertEqual(detail["slug"], "domestic-violence")

    def test_child_abuse_keyword_resolves_to_real_situation(self):
        _create_child_abuse_situation()
        detail = services.find_situation("my child is being abused")
        self.assertIsNotNone(detail)
        self.assertEqual(detail["slug"], "child-abuse")

    @patch("apps.chat.services.ai_classifier.classify_situation")
    def test_falls_back_to_ai_classifier_when_no_keyword_matches(
        self, mock_classify
    ):
        _create_domestic_violence_situation()
        mock_classify.return_value = "domestic-violence"
        detail = services.find_situation("I feel afraid every night")
        self.assertIsNotNone(detail)
        self.assertEqual(detail["slug"], "domestic-violence")
        mock_classify.assert_called_once_with("I feel afraid every night")

    @patch("apps.chat.services.ai_classifier.classify_situation")
    def test_returns_none_when_nothing_matches(self, mock_classify):
        mock_classify.return_value = None
        detail = services.find_situation("hello there")
        self.assertIsNone(detail)

    @patch("apps.chat.services.ai_classifier.classify_situation")
    def test_returns_none_when_matched_slug_has_no_situation_row(
        self, mock_classify
    ):
        mock_classify.return_value = None
        detail = services.find_situation("I have a problem at work")
        self.assertIsNone(detail)


class BuildContextTests(TestCase):
    def test_no_detail_returns_placeholder_message(self):
        context = services.build_context(None)
        self.assertIn("No matching Sauti Yo practical rights guidance", context)

    def test_includes_action_steps_safety_and_support(self):
        detail = {
            "title": "Domestic violence",
            "description": "Information on your legal protections.",
            "risk_level": "high_risk",
            "rights_topics": [
                {
                    "title": "Your right to protection under the law",
                    "summary": "Protection order info.",
                    "action_steps": [
                        {
                            "order": 1,
                            "title": "Get to safety first",
                            "description": "Prioritise getting somewhere safe.",
                        }
                    ],
                    "safety_responses": [
                        {"trigger_key": "default", "message": "Call 116."}
                    ],
                    "support_services": [
                        {"name": "Sauti 116", "phone_number": "116"}
                    ],
                }
            ],
        }
        context = services.build_context(detail)
        self.assertIn("Domestic violence", context)
        self.assertIn("Get to safety first", context)
        self.assertIn("Call 116.", context)
        self.assertIn("Sauti 116 - 116", context)


class GenerateAiReplyMissingKeyTests(TestCase):
    def setUp(self):
        services._client = None

    def tearDown(self):
        services._client = None

    @override_settings(OPENAI_API_KEY="")
    def test_returns_none_and_skips_call_when_api_key_unset(self):
        result = services.generate_ai_reply("hello", None)
        self.assertIsNone(result)


class GenerateAiReplyTests(TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        services._client = self.mock_client

    def tearDown(self):
        services._client = None

    def test_returns_stripped_reply_text(self):
        self.mock_client.responses.create.return_value.output_text = (
            "  Here is what you should know.  "
        )
        result = services.generate_ai_reply("what are my rights", None)
        self.assertEqual(result, "Here is what you should know.")

    def test_returns_none_when_reply_is_empty(self):
        self.mock_client.responses.create.return_value.output_text = "   "
        result = services.generate_ai_reply("what are my rights", None)
        self.assertIsNone(result)

    def test_returns_none_and_logs_when_client_raises(self):
        self.mock_client.responses.create.side_effect = RuntimeError("boom")
        with self.assertLogs("apps.chat.services", level="WARNING") as captured:
            result = services.generate_ai_reply("what are my rights", None)
        self.assertIsNone(result)
        self.assertTrue(
            any("failed" in msg.lower() for msg in captured.output)
        )


class BuildChatResponseTests(TestCase):
    def test_empty_message_returns_prompt_without_calling_anything(self):
        with patch("apps.chat.services.find_situation") as mock_find:
            result = services.build_chat_response("   ")
        mock_find.assert_not_called()
        self.assertFalse(result["matched"])
        self.assertIsNone(result["situation"])

    @patch("apps.chat.services.generate_ai_reply")
    @patch("apps.chat.services.find_situation")
    def test_matched_with_ai_reply(self, mock_find, mock_generate):
        mock_find.return_value = {
            "slug": "domestic-violence",
            "title": "Domestic violence",
            "risk_level": "high_risk",
        }
        mock_generate.return_value = "Here is grounded legal guidance."
        result = services.build_chat_response("my husband is beating me")
        self.assertTrue(result["matched"])
        self.assertEqual(result["reply"], "Here is grounded legal guidance.")
        self.assertEqual(
            result["situation"],
            {
                "slug": "domestic-violence",
                "title": "Domestic violence",
                "risk_level": "high_risk",
            },
        )

    @patch("apps.chat.services.generate_ai_reply")
    @patch("apps.chat.services.find_situation")
    def test_falls_back_to_situation_description_when_ai_unavailable(
        self, mock_find, mock_generate
    ):
        mock_find.return_value = {
            "slug": "domestic-violence",
            "title": "Domestic violence",
            "description": "Information on your legal protections.",
            "risk_level": "high_risk",
        }
        mock_generate.return_value = None
        result = services.build_chat_response("my husband is beating me")
        self.assertTrue(result["matched"])
        self.assertEqual(
            result["reply"], "Information on your legal protections."
        )

    @patch("apps.chat.services.generate_ai_reply")
    @patch("apps.chat.services.find_situation")
    def test_unmatched_when_neither_ai_nor_situation_available(
        self, mock_find, mock_generate
    ):
        mock_find.return_value = None
        mock_generate.return_value = None
        result = services.build_chat_response("hello there")
        self.assertFalse(result["matched"])
        self.assertIsNone(result["situation"])
        self.assertIn(
            "could not find enough verified legal information", result["reply"]
        )


class ChatAPIViewTests(TestCase):
    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    @patch("apps.chat.views.build_chat_response")
    def test_post_returns_chat_response_body(self, mock_build):
        mock_build.return_value = {
            "matched": False,
            "reply": "hi",
            "situation": None,
        }
        response = self.client.post(
            "/api/chat/",
            data=json.dumps({"message": "hello", "language": "en"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), mock_build.return_value)
        mock_build.assert_called_once_with(message="hello", language="en", situation_slug=None)

    def test_non_string_message_does_not_crash(self):
        response = self.client.post(
            "/api/chat/",
            data=json.dumps({"message": 123, "language": "en"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["matched"])

    @patch("apps.chat.views.build_chat_response")
    def test_non_string_language_falls_back_to_en(self, mock_build):
        mock_build.return_value = {
            "matched": False,
            "reply": "hi",
            "situation": None,
        }
        self.client.post(
            "/api/chat/",
            data=json.dumps({"message": "hello", "language": ["en"]}),
            content_type="application/json",
        )
        mock_build.assert_called_once_with(message="hello", language="en", situation_slug=None)

    @patch("apps.chat.views.build_chat_response")
    def test_eleventh_request_within_a_minute_is_throttled(self, mock_build):
        mock_build.return_value = {
            "matched": False,
            "reply": "hi",
            "situation": None,
        }
        statuses = []
        for _ in range(11):
            response = self.client.post(
                "/api/chat/",
                data=json.dumps({"message": "hello", "language": "en"}),
                content_type="application/json",
            )
            statuses.append(response.status_code)
        self.assertEqual(statuses[:10], [200] * 10)
        self.assertEqual(statuses[10], 429)


class ChatConversationContextTests(TestCase):
    def test_next_steps_is_contextual_follow_up(self):
        self.assertTrue(
            services.should_reuse_situation(
                "Guide me on the next steps"
            )
        )

    def test_reporting_question_is_contextual_follow_up(self):
        self.assertTrue(
            services.should_reuse_situation(
                "Can I report this to police?"
            )
        )

    def test_new_legal_question_does_not_force_old_context(self):
        self.assertFalse(
            services.should_reuse_situation(
                "What does Article 24 say?"
            )
        )

    @patch(
        "apps.chat.services.generate_ai_reply",
        return_value=None,
    )
    @patch(
        "apps.chat.services.find_situation",
        return_value=None,
    )
    @patch(
        "apps.chat.services.get_situation_detail",
    )
    def test_follow_up_reuses_previous_situation(
        self,
        get_situation_detail,
        find_situation,
        generate_ai_reply,
    ):
        get_situation_detail.return_value = {
            "slug": "domestic-violence",
            "title": "Domestic Violence",
            "description": (
                "You have the right to seek safety "
                "and support."
            ),
            "risk_level": "high_risk",
            "rights_topics": [],
        }

        result = services.build_chat_response(
            message="Guide me on the next steps",
            language="en",
            situation_slug="domestic-violence",
        )

        self.assertTrue(result["matched"])
        self.assertEqual(
            result["situation"]["slug"],
            "domestic-violence",
        )
        self.assertEqual(
            result["reply"],
            "You have the right to seek safety and support.",
        )

        get_situation_detail.assert_called_once_with(
            "domestic-violence"
        )

    @patch(
        "apps.chat.services.generate_ai_reply",
        return_value="Article 24 protects dignity.",
    )
    @patch(
        "apps.chat.services.find_situation",
        return_value=None,
    )
    @patch(
        "apps.chat.services.get_situation_detail",
    )
    def test_general_legal_question_does_not_reuse_situation(
        self,
        get_situation_detail,
        find_situation,
        generate_ai_reply,
    ):
        result = services.build_chat_response(
            message="What does Article 24 say?",
            language="en",
            situation_slug="domestic-violence",
        )

        self.assertTrue(result["matched"])
        self.assertEqual(
            result["reply"],
            "Article 24 protects dignity.",
        )
        self.assertIsNone(result["situation"])

        get_situation_detail.assert_not_called()
