from unittest.mock import MagicMock, patch

from django.db import IntegrityError
from django.test import TestCase

from apps.channels import africastalking_client
from apps.channels.models import SmsContext
from apps.channels.sms.keywords import (
    match_danger,
    match_discreet,
    match_followup,
    match_help,
    match_situation,
)


class SendSmsTests(TestCase):
    def setUp(self):
        self.mock_sms_service = MagicMock()
        africastalking_client._sms_service = self.mock_sms_service

    def tearDown(self):
        africastalking_client._sms_service = None

    def test_send_sms_calls_sdk_with_message_and_recipient(self):
        africastalking_client.send_sms("+256700000000", "Hello")
        self.mock_sms_service.send.assert_called_once_with(
            "Hello", ["+256700000000"], sender_id=None
        )

    def test_send_sms_passes_configured_sender_id(self):
        with self.settings(AFRICASTALKING_SMS_SENDER_ID="SAUTIYO"):
            africastalking_client.send_sms("+256700000000", "Hello")
        self.mock_sms_service.send.assert_called_once_with(
            "Hello", ["+256700000000"], sender_id="SAUTIYO"
        )

    @patch("apps.channels.africastalking_client.africastalking")
    def test_get_sms_service_initializes_sdk_with_settings_credentials(
        self, mock_at
    ):
        africastalking_client._sms_service = None
        with self.settings(
            AFRICASTALKING_USERNAME="sandbox",
            AFRICASTALKING_API_KEY="test-key",
        ):
            africastalking_client._get_sms_service()
        mock_at.initialize.assert_called_once_with("sandbox", "test-key")


class SmsContextModelTests(TestCase):
    def test_create_context_with_defaults(self):
        context = SmsContext.objects.create(
            phone_number="+256700000000", last_situation_slug="home-safety"
        )
        self.assertEqual(context.last_situation_slug, "home-safety")
        self.assertIsNotNone(context.updated_at)

    def test_phone_number_is_unique(self):
        SmsContext.objects.create(
            phone_number="+256700000000", last_situation_slug="home-safety"
        )
        with self.assertRaises(IntegrityError):
            SmsContext.objects.create(
                phone_number="+256700000000", last_situation_slug="work"
            )


class KeywordMatchingTests(TestCase):
    def test_match_situation_home_safety(self):
        self.assertEqual(match_situation("My husband beats me"), "home-safety")

    def test_match_situation_work(self):
        self.assertEqual(match_situation("I was fired from my job"), "work")

    def test_match_situation_land(self):
        self.assertEqual(
            match_situation("someone wants to evict me from my land"), "land"
        )

    def test_match_situation_child(self):
        self.assertEqual(
            match_situation("my child is unsafe at school"), "child"
        )

    def test_match_situation_returns_none_for_unmatched_text(self):
        self.assertIsNone(match_situation("hello there"))

    def test_match_danger_detects_danger_word(self):
        self.assertTrue(match_danger("he has a weapon right now"))

    def test_match_danger_false_for_safe_text(self):
        self.assertFalse(match_danger("I have a problem at work"))

    def test_match_followup_steps(self):
        self.assertEqual(match_followup("what are the steps"), "steps")

    def test_match_followup_support(self):
        self.assertEqual(match_followup("SUPPORT"), "support")

    def test_match_followup_returns_none(self):
        self.assertIsNone(match_followup("hello"))

    def test_match_help_matches_standalone_word(self):
        self.assertTrue(match_help("HELP"))

    def test_match_help_false_for_unrelated_text(self):
        self.assertFalse(match_help("helpful tips"))

    def test_match_discreet_detects_keyword(self):
        self.assertTrue(match_discreet("HOME DISCREET"))

    def test_match_discreet_false_by_default(self):
        self.assertFalse(match_discreet("HOME"))
