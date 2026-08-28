from unittest.mock import patch

from django.test import TestCase

from apps.chat.services import (
    build_chat_response,
    should_reuse_situation,
)


class ChatConversationContextTests(TestCase):
    def test_next_steps_is_contextual_follow_up(self):
        self.assertTrue(
            should_reuse_situation(
                "Guide me on the next steps"
            )
        )

    def test_reporting_question_is_contextual_follow_up(self):
        self.assertTrue(
            should_reuse_situation(
                "Can I report this to police?"
            )
        )

    def test_new_legal_question_does_not_force_old_context(self):
        self.assertFalse(
            should_reuse_situation(
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

        result = build_chat_response(
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
    def test_general_legal_question_does_not_require_situation(
        self,
        get_situation_detail,
        find_situation,
        generate_ai_reply,
    ):
        result = build_chat_response(
            message="What does Article 24 say?",
            language="en",
            situation_slug="domestic-violence",
        )

        self.assertTrue(result["matched"])
        self.assertEqual(
            result["reply"],
            "Article 24 protects dignity.",
        )
        self.assertIsNone(
            result["situation"]
        )

        get_situation_detail.assert_not_called()
