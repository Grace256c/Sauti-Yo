from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.channels import africastalking_client
from apps.channels.models import SmsContext
from apps.channels.sms.handler import handle_sms_request
from apps.channels.sms.keywords import (
    match_danger,
    match_discreet,
    match_followup,
    match_help,
    match_situation,
)
from apps.rights.models import (
    ActionStep,
    RightsTopic,
    SafetyResponse,
    Situation,
    SituationRightsTopic,
)
from apps.rights.services import get_situation_detail
from apps.support.models import SupportService
from apps.channels.sms import templates


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


def _create_home_safety_situation():
    situation = Situation.objects.create(
        slug="home-safety",
        title="I don't feel safe at home",
        description="For situations involving abuse or fear at home.",
        risk_level="high_risk",
    )
    topic = RightsTopic.objects.create(
        slug="domestic-violence-rights",
        title="Domestic Violence & Your Rights",
        summary="The Domestic Violence Act protects you from abuse.",
        risk_level="high_risk",
    )
    SituationRightsTopic.objects.create(situation=situation, rights_topic=topic)
    ActionStep.objects.create(
        rights_topic=topic,
        order=1,
        title="Move somewhere safer",
        description="Move to a safer location if you can.",
        is_safety_critical=True,
    )
    SafetyResponse.objects.create(
        rights_topic=topic,
        trigger_key="immediate_danger",
        message="Your safety matters. Call Sauti 116.",
    )
    service = SupportService.objects.create(
        name="Sauti 116 - Child & GBV Helpline",
        service_type="helpline",
        phone_number="116",
        is_emergency_service=True,
    )
    topic.support_services.add(service)
    return situation


def _create_land_situation_without_safety_response():
    situation = Situation.objects.create(
        slug="land-property",
        title="Land or property problem",
        risk_level="standard",
    )
    topic = RightsTopic.objects.create(
        slug="matrimonial-property-rights",
        title="Property Rights After Separation",
        summary="You may have a right to a share of matrimonial property.",
    )
    SituationRightsTopic.objects.create(situation=situation, rights_topic=topic)
    return situation


class BuildSituationReplyTests(TestCase):
    def setUp(self):
        _create_home_safety_situation()
        self.detail = get_situation_detail("home-safety")

    def test_normal_mode_includes_full_names(self):
        reply = templates.build_situation_reply(self.detail, mode="normal")
        self.assertIn("Sauti 116 - Child & GBV Helpline", reply)
        self.assertIn("Move to a safer location", reply)

    def test_discreet_mode_omits_service_name(self):
        reply = templates.build_situation_reply(self.detail, mode="discreet")
        self.assertNotIn("Sauti 116 - Child & GBV Helpline", reply)
        self.assertIn("116", reply)

    def test_falls_back_to_description_without_channel_content(self):
        reply = templates.build_situation_reply(self.detail, mode="normal")
        self.assertIn(
            "For situations involving abuse or fear at home.", reply
        )

    def test_discreet_mode_omits_situation_identity(self):
        reply = templates.build_situation_reply(self.detail, mode="discreet")
        self.assertNotIn("I don't feel safe at home", reply)
        self.assertNotIn(
            "For situations involving abuse or fear at home.", reply
        )
        self.assertIn(templates.DISCREET_INTRO, reply)


class BuildSupportReplyTests(TestCase):
    def setUp(self):
        _create_home_safety_situation()
        self.detail = get_situation_detail("home-safety")

    def test_uses_situation_support_services_when_detail_given(self):
        reply = templates.build_support_reply(self.detail)
        self.assertIn("116", reply)

    def test_falls_back_to_no_services_message_when_empty(self):
        empty_detail = dict(self.detail)
        empty_detail["rights_topics"] = [
            dict(t, support_services=[]) for t in self.detail["rights_topics"]
        ]
        reply = templates.build_support_reply(empty_detail)
        self.assertEqual(reply, templates.NO_SUPPORT_SERVICES_REPLY)

    def test_uses_general_emergency_services_when_no_detail(self):
        SupportService.objects.create(
            name="Uganda Police GBV Helpline",
            service_type="helpline",
            phone_number="0800199195",
            is_emergency_service=True,
        )
        reply = templates.build_support_reply(None)
        self.assertIn("0800199195", reply)


class BuildSafetyReplyTests(TestCase):
    def setUp(self):
        _create_home_safety_situation()
        self.detail = get_situation_detail("home-safety")

    def test_uses_predefined_safety_message_when_detail_given(self):
        reply = templates.build_safety_reply(self.detail)
        self.assertEqual(reply, "Your safety matters. Call Sauti 116.")

    def test_falls_back_to_general_safety_reply_without_detail(self):
        reply = templates.build_safety_reply(None)
        self.assertIn("999", reply)

    def test_falls_back_to_general_safety_reply_when_no_matching_response(self):
        _create_land_situation_without_safety_response()
        detail = get_situation_detail("land-property")
        reply = templates.build_safety_reply(detail)
        self.assertIn("999", reply)


class BuildStepsReplyTests(TestCase):
    def setUp(self):
        _create_home_safety_situation()
        self.detail = get_situation_detail("home-safety")

    def test_lists_action_steps(self):
        reply = templates.build_steps_reply(self.detail)
        self.assertIn("Move to a safer location", reply)

    def test_falls_back_when_no_steps(self):
        _create_land_situation_without_safety_response()
        detail = get_situation_detail("land-property")
        reply = templates.build_steps_reply(detail)
        self.assertEqual(reply, templates.NO_ACTION_STEPS_REPLY)


class FixedReplyTests(TestCase):
    def test_build_unmatched_reply(self):
        self.assertIn("HOME", templates.build_unmatched_reply())

    def test_build_followup_expired_reply(self):
        self.assertIn("STEPS", templates.build_followup_expired_reply())


class HandleSmsRequestTests(TestCase):
    def setUp(self):
        _create_home_safety_situation()

    @patch("apps.channels.sms.handler.send_sms")
    def test_situation_keyword_sends_normal_reply(self, mock_send):
        handle_sms_request("+256700000000", "My husband beats me")
        mock_send.assert_called_once()
        phone, message = mock_send.call_args[0]
        self.assertEqual(phone, "+256700000000")
        self.assertIn("Sauti 116 - Child & GBV Helpline", message)

    @patch("apps.channels.sms.handler.send_sms")
    def test_situation_keyword_with_discreet_omits_service_name(self, mock_send):
        handle_sms_request("+256700000000", "home discreet")
        message = mock_send.call_args[0][1]
        self.assertNotIn("Sauti 116 - Child & GBV Helpline", message)

    @patch("apps.channels.sms.handler.send_sms")
    def test_situation_keyword_creates_sms_context(self, mock_send):
        handle_sms_request("+256700000000", "my husband beats me")
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.last_situation_slug, "home-safety")

    @patch("apps.channels.sms.handler.send_sms")
    def test_danger_word_sends_safety_reply_with_context(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000", last_situation_slug="home-safety"
        )
        handle_sms_request("+256700000000", "he has a weapon right now")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, "Your safety matters. Call Sauti 116.")

    @patch("apps.channels.sms.handler.send_sms")
    def test_danger_word_sends_general_safety_reply_without_context(self, mock_send):
        handle_sms_request("+256711111111", "emergency, weapon")
        message = mock_send.call_args[0][1]
        self.assertIn("999", message)

    @patch("apps.channels.sms.handler.send_sms")
    def test_help_alone_sends_support_reply(self, mock_send):
        SupportService.objects.create(
            name="Uganda Police GBV Helpline",
            service_type="helpline",
            phone_number="0800199195",
            is_emergency_service=True,
        )
        handle_sms_request("+256700000000", "HELP")
        message = mock_send.call_args[0][1]
        self.assertIn("0800199195", message)

    @patch("apps.channels.sms.handler.send_sms")
    def test_followup_support_within_window(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000", last_situation_slug="home-safety"
        )
        handle_sms_request("+256700000000", "SUPPORT")
        message = mock_send.call_args[0][1]
        self.assertIn("116", message)

    @patch("apps.channels.sms.handler.send_sms")
    def test_followup_steps_within_window(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000", last_situation_slug="home-safety"
        )
        handle_sms_request("+256700000000", "STEPS")
        message = mock_send.call_args[0][1]
        self.assertIn("Move to a safer location", message)

    @patch("apps.channels.sms.handler.send_sms")
    def test_followup_expired_context(self, mock_send):
        context = SmsContext.objects.create(
            phone_number="+256700000000", last_situation_slug="home-safety"
        )
        SmsContext.objects.filter(pk=context.pk).update(
            updated_at=timezone.now() - timedelta(minutes=11)
        )
        handle_sms_request("+256700000000", "STEPS")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.build_followup_expired_reply())

    @patch("apps.channels.sms.handler.send_sms")
    def test_followup_without_any_context(self, mock_send):
        handle_sms_request("+256799999999", "SUPPORT")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.build_followup_expired_reply())

    @patch("apps.channels.sms.handler.send_sms")
    def test_unmatched_text_sends_fallback_reply(self, mock_send):
        handle_sms_request("+256700000000", "hello there")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.build_unmatched_reply())


class SmsCallbackViewTests(TestCase):
    def setUp(self):
        _create_home_safety_situation()

    @patch("apps.channels.sms.handler.send_sms")
    def test_valid_request_returns_200(self, mock_send):
        response = self.client.post(
            "/api/channels/sms/",
            {"from": "+256700000000", "text": "home"},
        )
        self.assertEqual(response.status_code, 200)
        mock_send.assert_called_once()

    def test_get_request_not_allowed(self):
        response = self.client.get("/api/channels/sms/")
        self.assertEqual(response.status_code, 405)

    @patch(
        "apps.channels.sms.views.handle_sms_request",
        side_effect=RuntimeError("boom"),
    )
    def test_unhandled_error_still_returns_200(self, mock_handle):
        response = self.client.post(
            "/api/channels/sms/",
            {"from": "+256700000000", "text": "home"},
        )
        self.assertEqual(response.status_code, 200)
