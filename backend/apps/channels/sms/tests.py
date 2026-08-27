from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.channels import africastalking_client
from apps.channels.models import SmsContext
from apps.channels.sms import ai_classifier, handler
from apps.channels.sms.handler import handle_sms_request
from apps.channels.sms.keywords import (
    match_consent_no,
    match_consent_yes,
    match_danger,
    match_discreet,
    match_followup,
    match_help,
    match_language_command,
    match_not_safe_answer,
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
from apps.partners.models import (
    PartnerOrganisation,
    PartnerServiceConfiguration,
    PartnerVerificationRequest,
)
from apps.referrals.models import Referral
from apps.channels.sms import templates


class SendSmsTests(TestCase):
    def setUp(self):
        self.mock_sms_service = MagicMock()
        africastalking_client._sms_service = self.mock_sms_service

    def tearDown(self):
        africastalking_client._sms_service = None

    def test_send_sms_calls_sdk_with_message_and_recipient(self):
        with self.settings(AFRICASTALKING_SMS_SENDER_ID=""):
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

    def test_discreet_defaults_to_false(self):
        context = SmsContext.objects.create(
            phone_number="+256700000000", last_situation_slug="home-safety"
        )
        self.assertFalse(context.discreet)

    def test_pending_safety_check_defaults_to_false(self):
        context = SmsContext.objects.create(
            phone_number="+256700000000", last_situation_slug="home-safety"
        )
        self.assertFalse(context.pending_safety_check)


    def test_language_defaults_to_english(self):
        context = SmsContext.objects.create(
            phone_number="+256700000001",
        )
        self.assertEqual(context.language, "en")
        self.assertEqual(context.last_situation_slug, "")

    def test_pending_referral_step_defaults_to_blank(self):
        context = SmsContext.objects.create(
            phone_number="+256700000002",
        )
        self.assertEqual(context.pending_referral_step, "")

    def test_pending_referral_step_can_be_set(self):
        context = SmsContext.objects.create(
            phone_number="+256700000003",
            pending_referral_step="consent",
        )
        self.assertEqual(context.pending_referral_step, "consent")


class MatchNotSafeAnswerTests(TestCase):
    def test_matches_no(self):
        self.assertTrue(match_not_safe_answer("no"))

    def test_matches_unsafe(self):
        self.assertTrue(match_not_safe_answer("unsafe"))

    def test_matches_not_safe_phrase(self):
        self.assertTrue(match_not_safe_answer("not safe"))

    def test_matches_danger_word(self):
        self.assertTrue(match_not_safe_answer("there's a weapon here"))

    def test_matches_scared(self):
        self.assertTrue(match_not_safe_answer("I'm scared"))

    def test_matches_afraid(self):
        self.assertTrue(match_not_safe_answer("I am afraid"))

    def test_matches_help_me(self):
        self.assertTrue(match_not_safe_answer("help me"))

    def test_matches_hes_here_without_apostrophe(self):
        self.assertTrue(match_not_safe_answer("hes here"))

    def test_matches_hes_here_with_apostrophe(self):
        self.assertTrue(match_not_safe_answer("he's here"))

    def test_matches_he_is_here(self):
        self.assertTrue(match_not_safe_answer("he is here"))

    def test_false_for_yes(self):
        self.assertFalse(match_not_safe_answer("yes"))

    def test_false_for_okay(self):
        self.assertFalse(match_not_safe_answer("I'm okay"))

    def test_does_not_false_positive_on_know(self):
        self.assertFalse(match_not_safe_answer("I don't know what to do"))

    def test_does_not_false_positive_on_info(self):
        self.assertFalse(match_not_safe_answer("send me more info please"))


class MatchConsentTests(TestCase):
    def test_match_consent_yes_matches_bare_yes(self):
        self.assertTrue(match_consent_yes("yes"))

    def test_match_consent_yes_matches_yes_in_sentence(self):
        self.assertTrue(match_consent_yes("yes please connect me"))

    def test_match_consent_yes_matches_short_form(self):
        self.assertTrue(match_consent_yes("y"))

    def test_match_consent_yes_false_for_no(self):
        self.assertFalse(match_consent_yes("no"))

    def test_match_consent_no_matches_bare_no(self):
        self.assertTrue(match_consent_no("no"))

    def test_match_consent_no_matches_short_form(self):
        self.assertTrue(match_consent_no("n"))

    def test_match_consent_no_false_for_yes(self):
        self.assertFalse(match_consent_no("yes"))


class KeywordMatchingTests(TestCase):
    def test_match_situation_home_safety(self):
        self.assertEqual(match_situation("My husband beats me"), "home-safety")

    def test_match_situation_work(self):
        self.assertEqual(
            match_situation("I was fired from my job"), "problem-at-work"
        )

    def test_match_situation_land(self):
        self.assertEqual(
            match_situation("someone wants to evict me from my land"),
            "land-property",
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


def _create_problem_at_work_situation():
    situation = Situation.objects.create(
        slug="problem-at-work",
        title="I have a problem at work",
        description=(
            "Understand your rights and explore practical next steps "
            "for a workplace problem."
        ),
        risk_level="standard",
    )
    topic = RightsTopic.objects.create(
        slug="workplace-rights",
        title="Understanding your workplace rights",
        summary=(
            "Sauti Yo can help you understand the issue, review "
            "relevant rights information, and identify possible next "
            "steps."
        ),
    )
    SituationRightsTopic.objects.create(situation=situation, rights_topic=topic)
    ActionStep.objects.create(
        rights_topic=topic,
        order=1,
        title="Understand what happened",
        description=(
            "Identify the workplace issue and keep a clear record of "
            "important details."
        ),
    )
    return situation


    def test_match_language_menu(self):
        self.assertEqual(
            match_language_command("LANG"),
            "menu",
        )

    def test_match_luganda_language(self):
        self.assertEqual(
            match_language_command("LANG LG"),
            "lg",
        )

    def test_match_kiswahili_language(self):
        self.assertEqual(
            match_language_command("language kiswahili"),
            "sw",
        )

    def test_match_runyankole_language(self):
        self.assertEqual(
            match_language_command("LANG NYN"),
            "nyn",
        )

    def test_match_language_command_ignores_normal_text(self):
        self.assertIsNone(
            match_language_command(
                "I have a problem at work"
            )
        )


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

    def test_discreet_mode_omits_service_names(self):
        reply = templates.build_support_reply(self.detail, mode="discreet")
        self.assertNotIn("Sauti 116 - Child & GBV Helpline", reply)
        self.assertIn("116", reply)


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

    def test_discreet_mode_returns_neutral_reply(self):
        reply = templates.build_steps_reply(self.detail, mode="discreet")
        self.assertEqual(reply, templates.DISCREET_STEPS_REPLY)


class FixedReplyTests(TestCase):
    def test_build_unmatched_reply(self):
        self.assertIn("HOME", templates.build_unmatched_reply())

    def test_build_followup_expired_reply(self):
        self.assertIn("STEPS", templates.build_followup_expired_reply())


class ReferralTemplateTests(TestCase):
    def test_build_referral_consent_prompt(self):
        self.assertEqual(
            templates.build_referral_consent_prompt(),
            templates.REFERRAL_CONSENT_PROMPT,
        )

    def test_build_referral_district_prompt(self):
        self.assertEqual(
            templates.build_referral_district_prompt(),
            templates.REFERRAL_DISTRICT_PROMPT,
        )

    def test_build_referral_confirmation_reply(self):
        service = SupportService.objects.create(
            name="Referral Template Test Partner",
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
            reference="SY-REF-TEMPLATE-TEST",
            organisation=organisation,
            citizen_consent_to_share=True,
            status="new",
        )

        message = templates.build_referral_confirmation_reply(referral)

        self.assertIn("Referral Template Test Partner", message)
        self.assertIn("SY-REF-TEMPLATE-TEST", message)


@override_settings(LLM_API_KEY="")
class HandleSmsRequestTests(TestCase):
    def setUp(self):
        _create_home_safety_situation()
        cache.clear()

    @patch("apps.channels.sms.handler.send_sms")
    def test_situation_keyword_sends_normal_reply(self, mock_send):
        # home-safety is high_risk, so the first message about it triggers
        # the safety check-in question first (see SafetyCheckinTests);
        # answering it resolves to the normal situation reply.
        handle_sms_request("+256700000000", "My husband beats me")
        handle_sms_request("+256700000000", "yes")
        phone, message = mock_send.call_args[0]
        self.assertEqual(phone, "+256700000000")
        self.assertIn("Sauti 116 - Child & GBV Helpline", message)

    @patch("apps.channels.sms.handler.ai_classifier.reword_reply")
    @patch("apps.channels.sms.handler.send_sms")
    def test_situation_keyword_with_discreet_omits_service_name(
        self, mock_send, mock_reword
    ):
        # home-safety is high_risk, so the first message about it triggers
        # the safety check-in question first (see SafetyCheckinTests);
        # answering it resolves to the discreet situation reply.
        mock_reword.return_value = None
        handle_sms_request("+256700000000", "home discreet")
        handle_sms_request("+256700000000", "yes")
        second_message = mock_send.call_args_list[1][0][1]
        self.assertNotIn("Sauti 116 - Child & GBV Helpline", second_message)

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

    @patch("apps.channels.sms.handler.send_sms")
    def test_work_keyword_resolves_to_real_situation(self, mock_send):
        _create_problem_at_work_situation()
        handle_sms_request("+256700000000", "I was fired from my job")
        message = mock_send.call_args[0][1]
        self.assertIn("Identify the workplace issue", message)

    @patch("apps.channels.sms.handler.send_sms")
    def test_land_keyword_resolves_to_real_situation(self, mock_send):
        _create_land_situation_without_safety_response()
        handle_sms_request("+256700000000", "they want to evict me from my land")
        mock_send.assert_called_once()
        message = mock_send.call_args[0][1]
        self.assertNotEqual(message, templates.build_unmatched_reply())

    @patch("apps.channels.sms.handler.send_sms")
    def test_unseeded_situation_keyword_sends_unmatched_reply_not_crash(
        self, mock_send
    ):
        handle_sms_request("+256700000000", "my child is unsafe at school")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.build_unmatched_reply())

    @patch("apps.channels.sms.handler.send_sms")
    def test_discreet_context_persists_to_support_followup(self, mock_send):
        handle_sms_request("+256700000000", "home discreet")
        handle_sms_request("+256700000000", "SUPPORT")
        message = mock_send.call_args[0][1]
        self.assertNotIn("Sauti 116 - Child & GBV Helpline", message)

    @patch("apps.channels.sms.handler.send_sms")
    def test_discreet_context_persists_to_steps_followup(self, mock_send):
        handle_sms_request("+256700000000", "home discreet")
        handle_sms_request("+256700000000", "STEPS")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.DISCREET_STEPS_REPLY)

    @patch("apps.channels.sms.handler.send_sms")
    def test_long_reply_is_truncated_to_max_length(self, mock_send):
        situation = Situation.objects.create(
            slug="problem-at-work",
            title="I have a problem at work",
            risk_level="standard",
        )
        topic = RightsTopic.objects.create(
            slug="workplace-rights",
            title="Understanding your workplace rights",
            summary="summary",
        )
        SituationRightsTopic.objects.create(situation=situation, rights_topic=topic)
        for i in range(10):
            ActionStep.objects.create(
                rights_topic=topic,
                order=i,
                title=f"Step {i}",
                description="A" * 50,
            )
        handle_sms_request("+256700000000", "I was fired from my job")
        handle_sms_request("+256700000000", "STEPS")
        message = mock_send.call_args[0][1]
        self.assertLessEqual(len(message), handler.MAX_SMS_LENGTH)
        self.assertTrue(message.endswith("..."))

    @patch("apps.channels.sms.handler.send_sms")
    def test_rate_limit_blocks_excess_messages_from_same_number(self, mock_send):
        for _ in range(5):
            handle_sms_request("+256700000000", "hello")
        mock_send.reset_mock()
        handle_sms_request("+256700000000", "hello")
        mock_send.assert_not_called()


class SmsLanguageTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch("apps.channels.sms.handler.send_sms")
    def test_lang_command_shows_language_menu(
        self,
        mock_send,
    ):
        handle_sms_request(
            "+256700001001",
            "LANG",
        )

        message = mock_send.call_args.args[1]

        self.assertIn("LANG EN", message)
        self.assertIn("LANG LG", message)
        self.assertIn("LANG SW", message)
        self.assertIn("LANG NYN", message)

    @patch("apps.channels.sms.handler.send_sms")
    def test_luganda_selection_is_persisted(
        self,
        mock_send,
    ):
        phone = "+256700001002"

        handle_sms_request(
            phone,
            "LANG LG",
        )

        context = SmsContext.objects.get(
            phone_number=phone,
        )

        self.assertEqual(context.language, "lg")
        self.assertIn(
            "Luganda",
            mock_send.call_args.args[1],
        )

    @patch("apps.channels.sms.handler.send_sms")
    def test_kiswahili_selection_is_persisted(
        self,
        mock_send,
    ):
        phone = "+256700001003"

        handle_sms_request(
            phone,
            "LANG SW",
        )

        context = SmsContext.objects.get(
            phone_number=phone,
        )

        self.assertEqual(context.language, "sw")
        self.assertIn(
            "Kiswahili",
            mock_send.call_args.args[1],
        )

    @patch("apps.channels.sms.handler.send_sms")
    def test_runyankole_selection_is_persisted(
        self,
        mock_send,
    ):
        phone = "+256700001004"

        handle_sms_request(
            phone,
            "LANG NYN",
        )

        context = SmsContext.objects.get(
            phone_number=phone,
        )

        self.assertEqual(context.language, "nyn")
        self.assertIn(
            "Runyankole",
            mock_send.call_args.args[1],
        )

    @patch("apps.channels.sms.handler.send_sms")
    def test_language_survives_expired_situation_context(
        self,
        mock_send,
    ):
        phone = "+256700001005"

        context = SmsContext.objects.create(
            phone_number=phone,
            last_situation_slug="problem-at-work",
            language="lg",
        )

        SmsContext.objects.filter(
            pk=context.pk,
        ).update(
            updated_at=timezone.now()
            - timedelta(minutes=20)
        )

        handle_sms_request(
            phone,
            "something unmatched",
        )

        context.refresh_from_db()

        self.assertEqual(context.language, "lg")
        self.assertEqual(
            context.last_situation_slug,
            "",
        )

        self.assertIn(
            "Wandiika",
            mock_send.call_args.args[1],
        )

    @patch("apps.channels.sms.handler.send_sms")
    def test_can_switch_back_to_english(
        self,
        mock_send,
    ):
        phone = "+256700001006"

        SmsContext.objects.create(
            phone_number=phone,
            language="lg",
        )

        handle_sms_request(
            phone,
            "LANG EN",
        )

        context = SmsContext.objects.get(
            phone_number=phone,
        )

        self.assertEqual(context.language, "en")

        self.assertIn(
            "Language set to English",
            mock_send.call_args.args[1],
        )


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


@override_settings(LLM_API_KEY="")
class AiFallbackTests(TestCase):
    def setUp(self):
        _create_home_safety_situation()
        cache.clear()

    @patch("apps.channels.sms.handler.ai_classifier.reword_reply")
    @patch("apps.channels.sms.handler.ai_classifier.classify_situation")
    @patch("apps.channels.sms.handler.send_sms")
    def test_ai_classified_slug_sends_situation_reply(
        self, mock_send, mock_classify, mock_reword
    ):
        # home-safety is high_risk, so the first message about it triggers
        # the safety check-in question first (see SafetyCheckinTests);
        # answering it resolves to the normal situation reply.
        mock_reword.return_value = None
        mock_classify.return_value = "home-safety"
        handle_sms_request(
            "+256700000000", "I'm scared of my spouse and don't know what to do"
        )
        handle_sms_request("+256700000000", "yes")
        message = mock_send.call_args[0][1]
        self.assertIn("Sauti 116 - Child & GBV Helpline", message)

    @patch("apps.channels.sms.handler.ai_classifier.classify_situation")
    @patch("apps.channels.sms.handler.send_sms")
    def test_ai_classified_slug_persists_sms_context(
        self, mock_send, mock_classify
    ):
        mock_classify.return_value = "home-safety"
        handle_sms_request(
            "+256700000000", "I'm scared of my spouse and don't know what to do"
        )
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.last_situation_slug, "home-safety")

    @patch("apps.channels.sms.handler.ai_classifier.classify_situation")
    @patch("apps.channels.sms.handler.send_sms")
    def test_ai_no_match_sends_unmatched_reply(self, mock_send, mock_classify):
        mock_classify.return_value = None
        handle_sms_request("+256700000000", "what time is it")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.build_unmatched_reply())


def _mock_text_response(text):
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.content = [block]
    return response


class ClassifySituationTests(TestCase):
    def setUp(self):
        _create_home_safety_situation()
        self.mock_client = MagicMock()
        ai_classifier._client = self.mock_client

    def tearDown(self):
        ai_classifier._client = None

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_slug_when_model_names_real_situation(self):
        self.mock_client.with_options.return_value.messages.create.return_value = (
            _mock_text_response("home-safety")
        )
        result = ai_classifier.classify_situation("someone hurt me at home")
        self.assertEqual(result, "home-safety")

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_none_when_model_says_none(self):
        self.mock_client.with_options.return_value.messages.create.return_value = (
            _mock_text_response("NONE")
        )
        result = ai_classifier.classify_situation("what's the weather today")
        self.assertIsNone(result)

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_none_for_hallucinated_slug(self):
        self.mock_client.with_options.return_value.messages.create.return_value = (
            _mock_text_response("made-up-slug")
        )
        result = ai_classifier.classify_situation("something unrelated")
        self.assertIsNone(result)

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_none_when_client_raises(self):
        self.mock_client.with_options.return_value.messages.create.side_effect = (
            RuntimeError("boom")
        )
        with self.assertLogs(
            "apps.channels.sms.ai_classifier", level="WARNING"
        ) as captured:
            result = ai_classifier.classify_situation("anything")
        self.assertIsNone(result)
        self.assertTrue(
            any("classification failed" in msg.lower() for msg in captured.output)
        )

    @override_settings(LLM_API_KEY="")
    def test_returns_none_and_skips_call_when_api_key_unset(self):
        result = ai_classifier.classify_situation("anything")
        self.assertIsNone(result)
        self.mock_client.with_options.assert_not_called()

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_none_and_skips_call_for_empty_text(self):
        result = ai_classifier.classify_situation("   ")
        self.assertIsNone(result)
        self.mock_client.with_options.assert_not_called()

    @patch("apps.channels.sms.ai_classifier.anthropic")
    @override_settings(LLM_API_KEY="test-key")
    def test_client_constructed_with_no_retries_and_short_timeout(
        self, mock_anthropic_module
    ):
        ai_classifier._client = None
        mock_anthropic_module.Anthropic.return_value.with_options.return_value.messages.create.return_value = (
            _mock_text_response("NONE")
        )
        ai_classifier.classify_situation("anything")
        mock_anthropic_module.Anthropic.assert_called_once_with(
            api_key="test-key", max_retries=0
        )
        mock_anthropic_module.Anthropic.return_value.with_options.assert_called_once_with(
            timeout=5.0
        )


class RewordReplyTests(TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        ai_classifier._client = self.mock_client

    def tearDown(self):
        ai_classifier._client = None

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_reworded_text_when_facts_preserved(self):
        self.mock_client.with_options.return_value.messages.create.return_value = (
            _mock_text_response(
                "I'm sorry you're going through this. Call 116 for free help."
            )
        )
        result = ai_classifier.reword_reply("Sauti 116: Call 116 for help.")
        self.assertEqual(
            result,
            "I'm sorry you're going through this. Call 116 for free help.",
        )

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_none_when_phone_number_dropped(self):
        self.mock_client.with_options.return_value.messages.create.return_value = (
            _mock_text_response("I'm sorry you're going through this.")
        )
        result = ai_classifier.reword_reply("Sauti 116: Call 116 for help.")
        self.assertIsNone(result)

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_none_when_client_raises(self):
        self.mock_client.with_options.return_value.messages.create.side_effect = (
            RuntimeError("boom")
        )
        result = ai_classifier.reword_reply("Some template text")
        self.assertIsNone(result)

    @override_settings(LLM_API_KEY="")
    def test_returns_none_and_skips_call_when_api_key_unset(self):
        result = ai_classifier.reword_reply("Some template text")
        self.assertIsNone(result)
        self.mock_client.with_options.assert_not_called()

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_none_for_empty_template_text(self):
        result = ai_classifier.reword_reply("   ")
        self.assertIsNone(result)
        self.mock_client.with_options.assert_not_called()

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_reworded_text_when_original_has_no_phone_number(self):
        self.mock_client.with_options.return_value.messages.create.return_value = (
            _mock_text_response("I'm here for you.")
        )
        result = ai_classifier.reword_reply("You're not alone in this.")
        self.assertEqual(result, "I'm here for you.")

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_none_when_phone_number_corrupted(self):
        self.mock_client.with_options.return_value.messages.create.return_value = (
            _mock_text_response("Please call 1167 for help.")
        )
        result = ai_classifier.reword_reply("Sauti 116: Call 116 for help.")
        self.assertIsNone(result)

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_none_when_phone_number_invented(self):
        self.mock_client.with_options.return_value.messages.create.return_value = (
            _mock_text_response("You're not alone. Call 0800111222 now.")
        )
        result = ai_classifier.reword_reply("You're not alone in this.")
        self.assertIsNone(result)


@override_settings(LLM_API_KEY="")
class SafetyCheckinTests(TestCase):
    """
    LLM_API_KEY is pinned empty at the class level so every test here is
    safe from hitting the real Anthropic API by default - several of
    these tests exercise paths (a non-high-risk reply, a topic switch,
    a post-danger-word follow-up) that reach reword_reply()/
    classify_situation() without explicitly mocking them. Tests that DO
    need to control the AI's behavior mock it explicitly via @patch,
    which overrides this regardless of the empty key.
    """

    def setUp(self):
        _create_home_safety_situation()
        cache.clear()

    @patch("apps.channels.sms.handler.send_sms")
    def test_new_high_risk_topic_sends_only_checkin_question(self, mock_send):
        handle_sms_request("+256700000000", "my husband beats me")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.SAFETY_CHECKIN_QUESTION)
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertTrue(context.pending_safety_check)
        self.assertEqual(context.last_situation_slug, "home-safety")

    @patch("apps.channels.sms.handler.send_sms")
    def test_non_high_risk_topic_skips_checkin(self, mock_send):
        _create_land_situation_without_safety_response()
        handle_sms_request("+256700000000", "they want to evict me from my land")
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertFalse(context.pending_safety_check)
        message = mock_send.call_args[0][1]
        self.assertNotEqual(message, templates.SAFETY_CHECKIN_QUESTION)

    @patch("apps.channels.sms.handler.ai_classifier.reword_reply")
    @patch("apps.channels.sms.handler.send_sms")
    def test_repeat_message_about_same_pending_topic_does_not_retrigger_checkin(
        self, mock_send, mock_reword
    ):
        mock_reword.return_value = None
        handle_sms_request("+256700000000", "my husband beats me")
        handle_sms_request("+256700000000", "my husband beats me")
        second_message = mock_send.call_args_list[1][0][1]
        self.assertNotEqual(second_message, templates.SAFETY_CHECKIN_QUESTION)

    @patch("apps.channels.sms.handler.ai_classifier.reword_reply")
    @patch("apps.channels.sms.handler.send_sms")
    def test_pending_checkin_answered_unsafe_sends_verbatim_safety_reply(
        self, mock_send, mock_reword
    ):
        handle_sms_request("+256700000000", "my husband beats me")
        handle_sms_request("+256700000000", "unsafe")
        second_message = mock_send.call_args_list[1][0][1]
        self.assertEqual(second_message, "Your safety matters. Call Sauti 116.")
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertFalse(context.pending_safety_check)
        mock_reword.assert_not_called()

    @patch("apps.channels.sms.handler.send_sms")
    def test_pending_checkin_answered_no_sends_verbatim_safety_reply(
        self, mock_send
    ):
        handle_sms_request("+256700000000", "my husband beats me")
        handle_sms_request("+256700000000", "no")
        second_message = mock_send.call_args_list[1][0][1]
        self.assertEqual(second_message, "Your safety matters. Call Sauti 116.")

    @patch("apps.channels.sms.handler.ai_classifier.reword_reply")
    @patch("apps.channels.sms.handler.send_sms")
    def test_pending_checkin_answered_yes_sends_situation_reply(
        self, mock_send, mock_reword
    ):
        mock_reword.return_value = None
        handle_sms_request("+256700000000", "my husband beats me")
        handle_sms_request("+256700000000", "yes")
        second_message = mock_send.call_args_list[1][0][1]
        self.assertIn("Sauti 116 - Child & GBV Helpline", second_message)
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertFalse(context.pending_safety_check)

    @patch("apps.channels.sms.handler.send_sms")
    def test_pending_checkin_answered_with_different_topic_switches_topic(
        self, mock_send
    ):
        _create_problem_at_work_situation()
        handle_sms_request("+256700000000", "my husband beats me")
        handle_sms_request("+256700000000", "I was fired from my job")
        second_message = mock_send.call_args_list[1][0][1]
        self.assertIn("Identify the workplace issue", second_message)
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.last_situation_slug, "problem-at-work")
        self.assertFalse(context.pending_safety_check)

    @patch("apps.channels.sms.handler.send_sms")
    def test_danger_word_while_checkin_pending_still_gets_safety_reply_and_clears_flag(
        self, mock_send
    ):
        handle_sms_request("+256700000000", "my husband beats me")
        handle_sms_request("+256700000000", "there's a weapon here")
        second_message = mock_send.call_args_list[1][0][1]
        self.assertEqual(second_message, "Your safety matters. Call Sauti 116.")
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertFalse(context.pending_safety_check)
        # A follow-up message must not be mis-interpreted as answering a
        # question that, in effect, was already answered.
        handle_sms_request("+256700000000", "yes")
        third_message = mock_send.call_args_list[2][0][1]
        self.assertNotEqual(third_message, "Your safety matters. Call Sauti 116.")

    @patch("apps.channels.sms.handler.ai_classifier.reword_reply")
    @patch("apps.channels.sms.handler.send_sms")
    def test_normal_mode_reply_uses_reworded_text_when_available(
        self, mock_send, mock_reword
    ):
        mock_reword.return_value = "A warmer version of the same message."
        _create_problem_at_work_situation()
        handle_sms_request("+256700000000", "I was fired from my job")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, "A warmer version of the same message.")

    @patch("apps.channels.sms.handler.ai_classifier.reword_reply")
    @patch("apps.channels.sms.handler.send_sms")
    def test_normal_mode_reply_falls_back_to_template_when_reword_fails(
        self, mock_send, mock_reword
    ):
        mock_reword.return_value = None
        _create_problem_at_work_situation()
        handle_sms_request("+256700000000", "I was fired from my job")
        message = mock_send.call_args[0][1]
        self.assertIn("Identify the workplace issue", message)

    @patch("apps.channels.sms.handler.ai_classifier.reword_reply")
    @patch("apps.channels.sms.handler.send_sms")
    def test_discreet_mode_reply_is_never_reworded(self, mock_send, mock_reword):
        _create_problem_at_work_situation()
        handle_sms_request("+256700000000", "I was fired from my job discreet")
        mock_reword.assert_not_called()

    @patch("apps.channels.sms.handler.send_sms")
    def test_discreet_new_high_risk_topic_sends_neutral_checkin_question(
        self, mock_send
    ):
        handle_sms_request("+256700000000", "home discreet")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.DISCREET_SAFETY_CHECKIN_QUESTION)

    @patch("apps.channels.sms.handler.ai_classifier.reword_reply")
    @patch("apps.channels.sms.handler.send_sms")
    def test_normal_mode_reply_falls_back_to_template_when_reworded_too_long(
        self, mock_send, mock_reword
    ):
        mock_reword.return_value = "x" * (handler.MAX_SMS_LENGTH + 1)
        _create_problem_at_work_situation()
        handle_sms_request("+256700000000", "I was fired from my job")
        message = mock_send.call_args[0][1]
        self.assertIn("Identify the workplace issue", message)

    @patch("apps.channels.sms.handler.ai_classifier.reword_reply")
    @patch("apps.channels.sms.handler.send_sms")
    def test_answering_checkin_by_echoing_safe_does_not_trigger_danger_reply(
        self, mock_send, mock_reword
    ):
        mock_reword.return_value = None
        handle_sms_request("+256700000000", "my husband beats me")
        handle_sms_request("+256700000000", "yes I am safe")
        second_message = mock_send.call_args_list[1][0][1]
        self.assertNotEqual(second_message, "Your safety matters. Call Sauti 116.")

    @patch("apps.channels.sms.handler.ai_classifier.reword_reply")
    @patch("apps.channels.sms.handler.send_sms")
    def test_resolving_checkin_refreshes_followup_window(self, mock_send, mock_reword):
        mock_reword.return_value = None
        handle_sms_request("+256700000000", "my husband beats me")
        # Simulate the check-in question having been sent 9 minutes ago -
        # still within the 10-minute window, but close to expiring.
        context = SmsContext.objects.get(phone_number="+256700000000")
        SmsContext.objects.filter(pk=context.pk).update(
            updated_at=timezone.now() - timedelta(minutes=9)
        )
        handle_sms_request("+256700000000", "yes")
        context.refresh_from_db()
        # If resolving the check-in refreshed updated_at, it should now be
        # recent (within the last few seconds), not still ~9 minutes old.
        self.assertGreater(
            context.updated_at, timezone.now() - timedelta(minutes=1)
        )


class ReferralConsentFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.situation = _create_problem_at_work_situation()

        RightsTopic.objects.filter(slug="workplace-rights").update(
            rights_category="work-employment",
        )

        service = SupportService.objects.create(
            name="Referral Flow Test Partner",
            service_type="Legal Aid",
            verification_status="verified",
            is_active=True,
        )
        self.organisation = PartnerOrganisation.objects.create(
            support_service=service,
            organisation_type="legal_aid",
            is_active=True,
            is_test=False,
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

    @patch("apps.channels.sms.handler.send_sms")
    def test_support_on_standard_situation_sends_consent_prompt(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000", last_situation_slug="problem-at-work"
        )
        handle_sms_request("+256700000000", "SUPPORT")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.REFERRAL_CONSENT_PROMPT)
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.pending_referral_step, "consent")

    @patch("apps.channels.sms.handler.send_sms")
    def test_consent_yes_sends_district_prompt(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000",
            last_situation_slug="problem-at-work",
            pending_referral_step="consent",
        )
        handle_sms_request("+256700000000", "yes")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.REFERRAL_DISTRICT_PROMPT)
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.pending_referral_step, "district")

    @patch("apps.channels.sms.handler.send_sms")
    def test_consent_no_falls_back_to_raw_support_reply(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000",
            last_situation_slug="problem-at-work",
            pending_referral_step="consent",
        )
        handle_sms_request("+256700000000", "no")
        message = mock_send.call_args[0][1]
        self.assertNotEqual(message, templates.REFERRAL_DISTRICT_PROMPT)
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.pending_referral_step, "")

    @patch("apps.channels.sms.handler.send_sms")
    def test_consent_unrecognized_falls_back_to_raw_support_reply(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000",
            last_situation_slug="problem-at-work",
            pending_referral_step="consent",
        )
        handle_sms_request("+256700000000", "maybe later")
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.pending_referral_step, "")

    @patch("apps.channels.sms.handler.send_sms")
    def test_district_match_sends_confirmation_and_creates_referral(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000",
            last_situation_slug="problem-at-work",
            pending_referral_step="district",
            language="en",
        )
        handle_sms_request("+256700000000", "Kampala")
        message = mock_send.call_args[0][1]
        self.assertIn("Referral Flow Test Partner", message)
        self.assertIn("SY-REF-", message)
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.pending_referral_step, "")

        referral = Referral.objects.get(organisation=self.organisation)
        self.assertEqual(referral.contact_phone, "+256700000000")
        self.assertEqual(referral.district, "Kampala")

    @patch("apps.channels.sms.handler.send_sms")
    def test_lowercase_district_still_matches_and_creates_referral(self, mock_send):
        # Citizens type districts freehand over SMS; find_matching_organisations
        # matches districts_served exactly and case-sensitively, so the handler
        # normalises to the canonical Title-Case vocabulary before matching.
        SmsContext.objects.create(
            phone_number="+256700000000",
            last_situation_slug="problem-at-work",
            pending_referral_step="district",
            language="en",
        )
        handle_sms_request("+256700000000", "kampala")
        message = mock_send.call_args[0][1]
        self.assertIn("Referral Flow Test Partner", message)
        self.assertIn("SY-REF-", message)
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.pending_referral_step, "")

        referral = Referral.objects.get(organisation=self.organisation)
        self.assertEqual(referral.contact_phone, "+256700000000")
        self.assertEqual(referral.district, "Kampala")

    @patch("apps.channels.sms.handler.send_sms")
    def test_send_failure_after_referral_creation_still_clears_pending_step(
        self, mock_send
    ):
        # send_sms raises on failure and the webhook view swallows it, so the
        # pending step must already be cleared by the time the confirmation
        # send is attempted - otherwise the citizen's natural retry would
        # re-enter the district branch and create a duplicate Referral.
        mock_send.side_effect = Exception("simulated AT API failure")
        SmsContext.objects.create(
            phone_number="+256700000000",
            last_situation_slug="problem-at-work",
            pending_referral_step="district",
            language="en",
        )

        with self.assertRaises(Exception) as raised:
            handle_sms_request("+256700000000", "Kampala")
        self.assertEqual(str(raised.exception), "simulated AT API failure")

        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.pending_referral_step, "")
        self.assertEqual(Referral.objects.count(), 1)

    @patch("apps.channels.sms.handler.send_sms")
    def test_district_no_match_falls_back_to_raw_support_reply(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000",
            last_situation_slug="problem-at-work",
            pending_referral_step="district",
            language="en",
        )
        handle_sms_request("+256700000000", "Gulu")
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.pending_referral_step, "")
        self.assertEqual(Referral.objects.count(), 0)

    @patch("apps.channels.sms.handler.send_sms")
    def test_high_risk_support_bypasses_consent_flow(self, mock_send):
        _create_home_safety_situation()
        SmsContext.objects.create(
            phone_number="+256700000001", last_situation_slug="home-safety"
        )
        handle_sms_request("+256700000001", "SUPPORT")
        message = mock_send.call_args[0][1]
        self.assertNotEqual(message, templates.REFERRAL_CONSENT_PROMPT)
        context = SmsContext.objects.get(phone_number="+256700000001")
        self.assertEqual(context.pending_referral_step, "")

    @patch("apps.channels.sms.handler.send_sms")
    def test_discreet_support_bypasses_consent_flow(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000002",
            last_situation_slug="problem-at-work",
            discreet=True,
        )
        handle_sms_request("+256700000002", "SUPPORT")
        message = mock_send.call_args[0][1]
        self.assertNotEqual(message, templates.REFERRAL_CONSENT_PROMPT)
        context = SmsContext.objects.get(phone_number="+256700000002")
        self.assertEqual(context.pending_referral_step, "")

    @patch("apps.channels.sms.handler.send_sms")
    def test_danger_word_while_pending_referral_step_clears_it(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000",
            last_situation_slug="problem-at-work",
            pending_referral_step="district",
        )
        handle_sms_request("+256700000000", "there's a weapon here right now")
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.pending_referral_step, "")

    @patch("apps.channels.sms.handler.send_sms")
    def test_expired_context_clears_pending_referral_step(self, mock_send):
        context = SmsContext.objects.create(
            phone_number="+256700000000",
            last_situation_slug="problem-at-work",
            pending_referral_step="district",
        )
        SmsContext.objects.filter(pk=context.pk).update(
            updated_at=timezone.now() - timedelta(minutes=11),
        )
        handle_sms_request("+256700000000", "Kampala")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.build_followup_expired_reply())
        context.refresh_from_db()
        self.assertEqual(context.pending_referral_step, "")

    @patch("apps.channels.sms.handler.ai_classifier.reword_reply")
    @patch("apps.channels.sms.handler.send_sms")
    def test_stale_pending_referral_step_does_not_swallow_next_situation_message(
        self, mock_send, mock_reword
    ):
        # A message that arrives after a pending_referral_step has expired
        # should still be handled by the normal matchers (match_situation
        # here) instead of being preempted by the expired-followup reply -
        # only the terminal unmatched-message fallback should ever send
        # build_followup_expired_reply for a lapsed referral step.
        mock_reword.return_value = None
        context = SmsContext.objects.create(
            phone_number="+256700000000",
            last_situation_slug="problem-at-work",
            pending_referral_step="district",
        )
        SmsContext.objects.filter(pk=context.pk).update(
            updated_at=timezone.now() - timedelta(minutes=11),
        )
        handle_sms_request("+256700000000", "I was fired from my job")
        message = mock_send.call_args[0][1]
        self.assertNotEqual(message, templates.build_followup_expired_reply())
        self.assertIn("Identify the workplace issue", message)
