from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.db import IntegrityError
from django.test import TestCase, override_settings
from requests.exceptions import ConnectionError as RequestsConnectionError

from apps.channels.models import VoiceSession
from apps.channels.sms.tests import (
    _create_home_safety_situation,
    _create_land_situation_without_safety_response,
)
from apps.channels.voice import sessions, transcription, ivr
from apps.channels.voice.handler import (
    _crisis_support_phone_number,
    _primary_support_phone_number,
    handle_voice_request,
)
from apps.rights.models import RightsTopic, Situation, SituationRightsTopic
from apps.support.models import SupportService


class VoiceSessionModelTests(TestCase):
    def test_create_session_with_defaults(self):
        session = VoiceSession.objects.create(
            session_id="abc123", phone_number="+256700000000"
        )
        self.assertEqual(session.state, "awaiting_recording")
        self.assertEqual(session.context, {})
        self.assertTrue(session.is_active)

    def test_session_id_is_unique(self):
        VoiceSession.objects.create(
            session_id="dup", phone_number="+256700000000"
        )
        with self.assertRaises(IntegrityError):
            VoiceSession.objects.create(
                session_id="dup", phone_number="+256711111111"
            )


class SessionHelperTests(TestCase):
    def test_get_or_create_session_creates_new_session(self):
        session, created = sessions.get_or_create_session(
            "new-session", "+256700000000"
        )
        self.assertTrue(created)
        self.assertEqual(session.state, "awaiting_recording")

    def test_get_or_create_session_returns_existing_session(self):
        sessions.get_or_create_session("existing", "+256700000000")
        session, created = sessions.get_or_create_session(
            "existing", "+256711111111"
        )
        self.assertFalse(created)
        self.assertEqual(session.phone_number, "+256700000000")

    def test_update_session_persists_fields(self):
        session, _ = sessions.get_or_create_session(
            "update-me", "+256700000000"
        )
        sessions.update_session(
            session, state="post_reply_menu", context={"slug": "home-safety"}
        )

        session.refresh_from_db()
        self.assertEqual(session.state, "post_reply_menu")
        self.assertEqual(session.context, {"slug": "home-safety"})

    def test_end_session_marks_inactive_and_ended(self):
        session, _ = sessions.get_or_create_session(
            "end-me", "+256700000000"
        )
        sessions.end_session(session)

        session.refresh_from_db()
        self.assertFalse(session.is_active)
        self.assertEqual(session.state, "ended")


@override_settings(OPENAI_API_KEY="test-key")
class TranscribeRecordingTests(TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        transcription._client = self.mock_client

    def tearDown(self):
        transcription._client = None

    @patch("apps.channels.voice.transcription.requests.get")
    def test_returns_transcript_text(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, content=b"audio-bytes")
        self.mock_client.audio.transcriptions.create.return_value = MagicMock(
            text="My husband beats me"
        )

        result = transcription.transcribe_recording("https://example.com/rec.mp3")

        self.assertEqual(result, "My husband beats me")
        mock_get.assert_called_once_with("https://example.com/rec.mp3", timeout=10)

    @patch("apps.channels.voice.transcription.requests.get")
    def test_strips_whitespace(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, content=b"audio-bytes")
        self.mock_client.audio.transcriptions.create.return_value = MagicMock(
            text="  hello  "
        )

        result = transcription.transcribe_recording("https://example.com/rec.mp3")

        self.assertEqual(result, "hello")

    @patch("apps.channels.voice.transcription.requests.get")
    def test_empty_transcript_returns_none(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, content=b"audio-bytes")
        self.mock_client.audio.transcriptions.create.return_value = MagicMock(text="")

        result = transcription.transcribe_recording("https://example.com/rec.mp3")

        self.assertIsNone(result)

    @patch("apps.channels.voice.transcription.requests.get")
    def test_download_failure_returns_none(self, mock_get):
        mock_get.side_effect = RequestsConnectionError("boom")

        result = transcription.transcribe_recording("https://example.com/rec.mp3")

        self.assertIsNone(result)
        self.mock_client.audio.transcriptions.create.assert_not_called()

    @patch("apps.channels.voice.transcription.requests.get")
    def test_api_failure_returns_none(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, content=b"audio-bytes")
        self.mock_client.audio.transcriptions.create.side_effect = RuntimeError("boom")

        result = transcription.transcribe_recording("https://example.com/rec.mp3")

        self.assertIsNone(result)

    def test_no_recording_url_returns_none(self):
        self.assertIsNone(transcription.transcribe_recording(""))
        self.mock_client.audio.transcriptions.create.assert_not_called()

    @override_settings(OPENAI_API_KEY="")
    def test_missing_api_key_returns_none(self):
        result = transcription.transcribe_recording("https://example.com/rec.mp3")
        self.assertIsNone(result)


class IvrXmlTests(TestCase):
    def test_greeting_includes_say_and_record(self):
        xml = ivr.build_greeting_xml()
        self.assertIn("<Response>", xml)
        self.assertIn("<Say>", xml)
        self.assertIn("<Record", xml)

    def test_safety_checkin_normal_asks_are_you_safe(self):
        xml = ivr.build_safety_checkin_xml(discreet=False)
        self.assertIn("Are you safe", xml)
        self.assertIn("<GetDigits", xml)
        self.assertIn('numDigits="1"', xml)

    def test_safety_checkin_discreet_omits_are_you_safe(self):
        xml = ivr.build_safety_checkin_xml(discreet=True)
        self.assertNotIn("Are you safe", xml)
        self.assertIn("<GetDigits", xml)

    def test_reply_xml_includes_spoken_text_and_menu(self):
        xml = ivr.build_reply_xml("Move to a safer location if you can.")
        self.assertIn("Move to a safer location if you can.", xml)
        self.assertIn("<GetDigits", xml)
        self.assertIn("press 1", xml.lower())

    def test_reply_xml_escapes_special_characters(self):
        xml = ivr.build_reply_xml("Rights & Action < 5 steps")
        self.assertIn("Rights &amp; Action &lt; 5 steps", xml)
        self.assertNotIn("Rights & Action < 5 steps", xml)

    def test_unmatched_retry_includes_record(self):
        xml = ivr.build_unmatched_xml(retry=True)
        self.assertIn("<Record", xml)

    def test_unmatched_give_up_has_no_record_or_digits(self):
        xml = ivr.build_unmatched_xml(retry=False)
        self.assertNotIn("<Record", xml)
        self.assertNotIn("<GetDigits", xml)

    def test_final_message_says_given_text_with_no_further_action(self):
        xml = ivr.build_final_message_xml("Your safety matters. Call Sauti 116.")
        self.assertIn("Your safety matters. Call Sauti 116.", xml)
        self.assertNotIn("<Record", xml)
        self.assertNotIn("<GetDigits", xml)

    def test_closing_says_thank_you(self):
        xml = ivr.build_closing_xml()
        self.assertIn("Thank you", xml)

    def test_safety_reply_with_connect_offers_press_1(self):
        xml = ivr.build_safety_reply_with_connect_xml(
            "Your safety matters. Call Sauti 116."
        )
        self.assertIn("Your safety matters. Call Sauti 116.", xml)
        self.assertIn("<GetDigits", xml)
        self.assertIn("press 1", xml.lower())

    def test_dial_xml_includes_dial_verb_with_no_recording(self):
        xml = ivr.build_dial_xml("+256700000000")
        self.assertIn('<Dial phoneNumbers="+256700000000"', xml)
        self.assertIn('record="false"', xml)
        self.assertNotIn("<GetDigits", xml)
        self.assertNotIn("<Record ", xml)

    def test_dial_xml_fallback_mentions_the_number(self):
        xml = ivr.build_dial_xml("+256700000000")
        # The fallback <Say> (only reached if the dial isn't answered)
        # must repeat the number so a caller who couldn't be connected
        # still has it, matching what they'd have heard without this
        # feature.
        say_count = xml.count("<Say>")
        self.assertEqual(say_count, 1)
        self.assertIn("+256700000000", xml)

    def test_post_reply_menu_prompt_mentions_connect_option(self):
        xml = ivr.build_reply_xml("some reply text")
        self.assertIn("press 3", xml.lower())

    def test_dial_xml_escapes_quote_in_phone_number(self):
        xml = ivr.build_dial_xml('+1" onmouseover="evil')
        # The payload should not break out of the attribute - verify the
        # injection attempt is safely contained within quotes
        self.assertNotIn('phoneNumbers="+1" onmouseover="evil"', xml)
        # quoteattr chooses appropriate quotes to safely escape the value
        self.assertIn("phoneNumbers='+1\" onmouseover=\"evil'", xml)


@override_settings(LLM_API_KEY="", OPENAI_API_KEY="test-key")
class HandleVoiceRequestTests(TestCase):
    def setUp(self):
        cache.clear()

    def _mock_transcript(self, text):
        return patch(
            "apps.channels.voice.handler.transcription.transcribe_recording",
            return_value=text,
        )

    def test_call_start_returns_greeting(self):
        xml = handle_voice_request("sess-1", "+256700000000", "1", "", "")
        self.assertIn("<Record", xml)
        session = VoiceSession.objects.get(session_id="sess-1")
        self.assertEqual(session.state, "awaiting_recording")

    def test_recording_with_danger_words_speaks_safety_reply_with_connect_offer(self):
        SupportService.objects.create(
            name="Uganda Police GBV Helpline",
            service_type="helpline",
            phone_number="0800199195",
            is_emergency_service=True,
        )
        handle_voice_request("sess-2", "+256700000000", "1", "", "")
        with self._mock_transcript("he has a weapon right now"):
            xml = handle_voice_request(
                "sess-2", "+256700000000", "1", "", "https://example.com/r.mp3"
            )
        self.assertIn("999", xml)
        self.assertIn("<GetDigits", xml)
        session = VoiceSession.objects.get(session_id="sess-2")
        self.assertTrue(session.is_active)
        self.assertEqual(session.state, "awaiting_crisis_connect_digit")

    def test_danger_words_short_circuit_before_situation_classification(self):
        _create_home_safety_situation()
        handle_voice_request("sess-2b", "+256700000000", "1", "", "")
        with self._mock_transcript(
            "my husband beats me and he has a weapon right now"
        ):
            with patch(
                "apps.channels.voice.handler.ai_classifier.classify_situation"
            ) as mock_classify:
                xml = handle_voice_request(
                    "sess-2b",
                    "+256700000000",
                    "1",
                    "",
                    "https://example.com/r.mp3",
                )
        mock_classify.assert_not_called()
        self.assertIn("999", xml)
        session = VoiceSession.objects.get(session_id="sess-2b")
        self.assertTrue(session.is_active)
        self.assertEqual(session.state, "awaiting_crisis_connect_digit")

    def test_non_high_risk_situation_speaks_reply_and_offers_menu(self):
        _create_land_situation_without_safety_response()
        handle_voice_request("sess-3", "+256700000000", "1", "", "")
        with self._mock_transcript("I have a problem with my land and plot"):
            xml = handle_voice_request(
                "sess-3", "+256700000000", "1", "", "https://example.com/r.mp3"
            )
        # No ChannelContent/description is seeded for this fixture, so
        # build_situation_reply falls back to the situation's title.
        self.assertIn("Land or property problem", xml)
        self.assertIn("<GetDigits", xml)
        session = VoiceSession.objects.get(session_id="sess-3")
        self.assertEqual(session.state, "post_reply_menu")
        self.assertEqual(session.context["slug"], "land-property")

    def test_high_risk_situation_triggers_safety_checkin(self):
        _create_home_safety_situation()
        handle_voice_request("sess-4", "+256700000000", "1", "", "")
        with self._mock_transcript("my husband beats me"):
            xml = handle_voice_request(
                "sess-4", "+256700000000", "1", "", "https://example.com/r.mp3"
            )
        self.assertIn("Are you safe", xml)
        session = VoiceSession.objects.get(session_id="sess-4")
        self.assertEqual(session.state, "awaiting_safety_digit")
        self.assertEqual(session.context["slug"], "home-safety")

    def test_safety_digit_2_speaks_safety_reply_with_connect_offer(self):
        _create_home_safety_situation()
        VoiceSession.objects.create(
            session_id="sess-5",
            phone_number="+256700000000",
            state="awaiting_safety_digit",
            context={"slug": "home-safety", "discreet": False},
        )
        xml = handle_voice_request("sess-5", "+256700000000", "1", "2", "")
        self.assertIn("Your safety matters. Call Sauti 116.", xml)
        self.assertIn("<GetDigits", xml)
        session = VoiceSession.objects.get(session_id="sess-5")
        self.assertTrue(session.is_active)
        self.assertEqual(session.state, "awaiting_crisis_connect_digit")

    def test_safety_digit_1_continues_to_situation_reply(self):
        _create_home_safety_situation()
        VoiceSession.objects.create(
            session_id="sess-6",
            phone_number="+256700000000",
            state="awaiting_safety_digit",
            context={"slug": "home-safety", "discreet": False},
        )
        xml = handle_voice_request("sess-6", "+256700000000", "1", "1", "")
        self.assertIn("Move to a safer location", xml)
        self.assertIn("<GetDigits", xml)
        session = VoiceSession.objects.get(session_id="sess-6")
        self.assertEqual(session.state, "post_reply_menu")

    def test_safety_digit_off_menu_reprompts_once(self):
        _create_home_safety_situation()
        VoiceSession.objects.create(
            session_id="sess-6b",
            phone_number="+256700000000",
            state="awaiting_safety_digit",
            context={"slug": "home-safety", "discreet": False},
        )
        xml = handle_voice_request("sess-6b", "+256700000000", "1", "5", "")
        self.assertIn("Are you safe", xml)
        session = VoiceSession.objects.get(session_id="sess-6b")
        self.assertEqual(session.state, "awaiting_safety_digit")
        self.assertEqual(session.context["safety_check_attempts"], 1)
        self.assertEqual(session.context["slug"], "home-safety")

    def test_safety_digit_off_menu_twice_fails_closed_to_safety_reply(self):
        _create_home_safety_situation()
        VoiceSession.objects.create(
            session_id="sess-6c",
            phone_number="+256700000000",
            state="awaiting_safety_digit",
            context={
                "slug": "home-safety",
                "discreet": False,
                "safety_check_attempts": 1,
            },
        )
        xml = handle_voice_request("sess-6c", "+256700000000", "1", "9", "")
        self.assertIn("Your safety matters. Call Sauti 116.", xml)
        session = VoiceSession.objects.get(session_id="sess-6c")
        self.assertTrue(session.is_active)
        self.assertEqual(session.state, "awaiting_crisis_connect_digit")

    def test_safety_digit_1_after_reprompt_still_reaches_situation_reply(self):
        _create_home_safety_situation()
        VoiceSession.objects.create(
            session_id="sess-6d",
            phone_number="+256700000000",
            state="awaiting_safety_digit",
            context={
                "slug": "home-safety",
                "discreet": False,
                "safety_check_attempts": 1,
            },
        )
        xml = handle_voice_request("sess-6d", "+256700000000", "1", "1", "")
        self.assertIn("Move to a safer location", xml)
        session = VoiceSession.objects.get(session_id="sess-6d")
        self.assertEqual(session.state, "post_reply_menu")

    def test_getdigits_timeout_during_safety_checkin_reprompts_not_greets(self):
        _create_home_safety_situation()
        VoiceSession.objects.create(
            session_id="sess-6e",
            phone_number="+256700000000",
            state="awaiting_safety_digit",
            context={"slug": "home-safety", "discreet": False},
        )
        xml = handle_voice_request("sess-6e", "+256700000000", "1", "", "")
        self.assertIn("Are you safe", xml)
        self.assertNotIn("Welcome to Sauti Yo", xml)
        session = VoiceSession.objects.get(session_id="sess-6e")
        self.assertEqual(session.state, "awaiting_safety_digit")
        self.assertEqual(session.context["safety_check_attempts"], 1)

    def test_getdigits_timeout_during_post_reply_menu_ends_call(self):
        _create_home_safety_situation()
        VoiceSession.objects.create(
            session_id="sess-6f",
            phone_number="+256700000000",
            state="post_reply_menu",
            context={"slug": "home-safety", "discreet": False},
        )
        xml = handle_voice_request("sess-6f", "+256700000000", "1", "", "")
        self.assertIn("Thank you", xml)
        session = VoiceSession.objects.get(session_id="sess-6f")
        self.assertFalse(session.is_active)

    def test_no_existing_session_with_empty_digits_still_gets_greeting(self):
        xml = handle_voice_request("sess-6g", "+256700000000", "1", "", "")
        self.assertIn("<Record", xml)
        session = VoiceSession.objects.get(session_id="sess-6g")
        self.assertEqual(session.state, "awaiting_recording")

    def test_empty_recording_url_on_existing_recording_session_retries_not_greets(
        self,
    ):
        handle_voice_request("sess-empty-rec", "+256700000000", "1", "", "")
        xml = handle_voice_request(
            "sess-empty-rec", "+256700000000", "1", "", ""
        )
        self.assertIn("<Record", xml)
        self.assertNotIn("Welcome to Sauti Yo", xml)
        self.assertIn("Sorry, I didn't catch that", xml)
        session = VoiceSession.objects.get(session_id="sess-empty-rec")
        self.assertEqual(session.state, "awaiting_recording")
        self.assertEqual(session.context.get("attempts"), 1)

    def test_discreet_keyword_omits_service_name_from_reply(self):
        _create_home_safety_situation()
        handle_voice_request("sess-7", "+256700000000", "1", "", "")
        with self._mock_transcript("my husband beats me, please be discreet"):
            xml = handle_voice_request(
                "sess-7", "+256700000000", "1", "", "https://example.com/r.mp3"
            )
        session = VoiceSession.objects.get(session_id="sess-7")
        self.assertTrue(session.context["discreet"])
        self.assertEqual(session.state, "awaiting_safety_digit")
        xml = handle_voice_request("sess-7", "+256700000000", "1", "1", "")
        self.assertNotIn("Sauti 116 - Child", xml)
        self.assertIn("116", xml)

    def test_discreet_mode_does_not_call_reword_reply(self):
        _create_land_situation_without_safety_response()
        handle_voice_request("sess-7b", "+256700000000", "1", "", "")
        with self._mock_transcript("land and plot problem, please be discreet"):
            with patch(
                "apps.channels.voice.handler.ai_classifier.reword_reply"
            ) as mock_reword:
                handle_voice_request(
                    "sess-7b",
                    "+256700000000",
                    "1",
                    "",
                    "https://example.com/r.mp3",
                )
        mock_reword.assert_not_called()

    def test_normal_mode_calls_reword_reply(self):
        _create_land_situation_without_safety_response()
        handle_voice_request("sess-7c", "+256700000000", "1", "", "")
        with self._mock_transcript("I have a problem with my land and plot"):
            with patch(
                "apps.channels.voice.handler.ai_classifier.reword_reply"
            ) as mock_reword:
                mock_reword.return_value = None
                handle_voice_request(
                    "sess-7c",
                    "+256700000000",
                    "1",
                    "",
                    "https://example.com/r.mp3",
                )
        mock_reword.assert_called_once()

    def test_post_reply_menu_digit_1_speaks_support_contacts(self):
        _create_home_safety_situation()
        VoiceSession.objects.create(
            session_id="sess-8",
            phone_number="+256700000000",
            state="post_reply_menu",
            context={"slug": "home-safety", "discreet": False},
        )
        xml = handle_voice_request("sess-8", "+256700000000", "1", "1", "")
        self.assertIn("116", xml)
        self.assertIn("<GetDigits", xml)

    def test_post_reply_menu_digit_2_repeats_reply(self):
        _create_home_safety_situation()
        VoiceSession.objects.create(
            session_id="sess-9",
            phone_number="+256700000000",
            state="post_reply_menu",
            context={"slug": "home-safety", "discreet": False},
        )
        xml = handle_voice_request("sess-9", "+256700000000", "1", "2", "")
        self.assertIn("Move to a safer location", xml)

    def test_post_reply_menu_digit_0_ends_call(self):
        _create_home_safety_situation()
        VoiceSession.objects.create(
            session_id="sess-10",
            phone_number="+256700000000",
            state="post_reply_menu",
            context={"slug": "home-safety", "discreet": False},
        )
        xml = handle_voice_request("sess-10", "+256700000000", "1", "0", "")
        self.assertIn("Thank you", xml)
        session = VoiceSession.objects.get(session_id="sess-10")
        self.assertFalse(session.is_active)

    def test_empty_transcript_offers_one_retry_then_gives_up(self):
        handle_voice_request("sess-11", "+256700000000", "1", "", "")
        with self._mock_transcript(None):
            first = handle_voice_request(
                "sess-11", "+256700000000", "1", "", "https://example.com/r.mp3"
            )
            second = handle_voice_request(
                "sess-11", "+256700000000", "1", "", "https://example.com/r2.mp3"
            )
        self.assertIn("<Record", first)
        self.assertNotIn("<Record", second)
        session = VoiceSession.objects.get(session_id="sess-11")
        self.assertFalse(session.is_active)

    def test_hangup_marks_session_inactive_and_returns_empty(self):
        handle_voice_request("sess-12", "+256700000000", "1", "", "")
        xml = handle_voice_request("sess-12", "+256700000000", "0", "", "")
        self.assertEqual(xml, "")
        session = VoiceSession.objects.get(session_id="sess-12")
        self.assertFalse(session.is_active)

    def test_sixth_call_from_same_number_in_one_minute_is_rate_limited(self):
        for i in range(5):
            handle_voice_request(f"sess-rl-{i}", "+256799999999", "1", "", "")
        xml = handle_voice_request("sess-rl-5", "+256799999999", "1", "", "")
        self.assertIn("Thank you", xml)
        self.assertFalse(
            VoiceSession.objects.filter(session_id="sess-rl-5").exists()
        )


class VoiceCallbackViewTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_call_start_returns_xml_response(self):
        response = self.client.post(
            "/api/channels/voice/",
            {
                "sessionId": "view-sess-1",
                "phoneNumber": "+256700000000",
                "isActive": "1",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/xml")
        self.assertIn(b"<Response>", response.content)

    def test_get_is_not_allowed(self):
        response = self.client.get("/api/channels/voice/")
        self.assertEqual(response.status_code, 405)

    @patch("apps.channels.voice.views.handle_voice_request")
    def test_unhandled_error_returns_graceful_xml(self, mock_handle):
        mock_handle.side_effect = RuntimeError("boom")
        response = self.client.post(
            "/api/channels/voice/",
            {
                "sessionId": "view-sess-2",
                "phoneNumber": "+256700000000",
                "isActive": "1",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<Say>", response.content)
        self.assertNotIn(b"<Record", response.content)
        self.assertNotIn(b"<GetDigits", response.content)


def _create_high_risk_situation_without_support_service():
    """
    A high-risk situation whose linked rights topic has no support_services
    at all - used to exercise _crisis_support_phone_number's fallback to
    the general emergency-services list when the situation-specific lookup
    comes up empty.
    """
    situation = Situation.objects.create(
        slug="high-risk-no-number",
        title="High risk situation with no linked support number",
        risk_level="high_risk",
    )
    topic = RightsTopic.objects.create(
        slug="high-risk-no-number-rights",
        title="High Risk Rights",
        summary="Placeholder rights summary.",
        risk_level="high_risk",
    )
    SituationRightsTopic.objects.create(situation=situation, rights_topic=topic)
    return situation


@override_settings(LLM_API_KEY="", OPENAI_API_KEY="test-key")
class DirectConnectTests(TestCase):
    def setUp(self):
        cache.clear()

    def _mock_transcript(self, text):
        return patch(
            "apps.channels.voice.handler.transcription.transcribe_recording",
            return_value=text,
        )

    def test_primary_support_phone_number_from_situation_detail(self):
        situation = _create_home_safety_situation()
        from apps.rights.services import get_situation_detail

        detail = get_situation_detail(situation.slug)
        self.assertEqual(_primary_support_phone_number(detail), "116")

    def test_primary_support_phone_number_general_emergency_when_no_detail(self):
        SupportService.objects.create(
            name="Uganda Police GBV Helpline",
            service_type="helpline",
            phone_number="0800199195",
            is_emergency_service=True,
        )
        self.assertEqual(
            _primary_support_phone_number(None), "0800199195"
        )

    def test_primary_support_phone_number_none_when_nothing_available(self):
        self.assertIsNone(_primary_support_phone_number(None))

    def test_primary_support_phone_number_none_when_situation_has_none_linked(self):
        # _primary_support_phone_number is the post-reply-menu ("connect
        # me") lookup, and it must never silently misdirect a non-crisis
        # caller toward the general emergency/GBV line just because their
        # situation happens to have no linked support number - it should
        # return None here, same as apps.channels.sms.templates'
        # _first_support_service/build_support_reply do for this exact case.
        situation = _create_land_situation_without_safety_response()
        from apps.rights.services import get_situation_detail

        SupportService.objects.create(
            name="Uganda Police GBV Helpline",
            service_type="helpline",
            phone_number="0800199195",
            is_emergency_service=True,
        )
        detail = get_situation_detail(situation.slug)
        self.assertIsNone(_primary_support_phone_number(detail))

    def test_crisis_support_phone_number_falls_back_to_general_when_situation_has_none(
        self,
    ):
        situation = _create_land_situation_without_safety_response()
        from apps.rights.services import get_situation_detail

        SupportService.objects.create(
            name="Uganda Police GBV Helpline",
            service_type="helpline",
            phone_number="0800199195",
            is_emergency_service=True,
        )
        detail = get_situation_detail(situation.slug)
        self.assertEqual(_crisis_support_phone_number(detail), "0800199195")

    def test_danger_words_offer_connect_instead_of_ending_immediately(self):
        SupportService.objects.create(
            name="Uganda Police GBV Helpline",
            service_type="helpline",
            phone_number="0800199195",
            is_emergency_service=True,
        )
        handle_voice_request("sess-dc-1", "+256700000000", "1", "", "")
        with self._mock_transcript("he has a weapon right now"):
            xml = handle_voice_request(
                "sess-dc-1", "+256700000000", "1", "", "https://example.com/r.mp3"
            )
        self.assertIn("<GetDigits", xml)
        self.assertIn("999", xml)
        session = VoiceSession.objects.get(session_id="sess-dc-1")
        self.assertTrue(session.is_active)
        self.assertEqual(session.state, "awaiting_crisis_connect_digit")

    def test_pressing_1_after_danger_words_dials_general_emergency_number(self):
        SupportService.objects.create(
            name="Uganda Police GBV Helpline",
            service_type="helpline",
            phone_number="0800199195",
            is_emergency_service=True,
        )
        handle_voice_request("sess-dc-2", "+256700000000", "1", "", "")
        with self._mock_transcript("he has a weapon right now"):
            handle_voice_request(
                "sess-dc-2", "+256700000000", "1", "", "https://example.com/r.mp3"
            )
        xml = handle_voice_request("sess-dc-2", "+256700000000", "1", "1", "")
        self.assertIn('<Dial phoneNumbers="0800199195"', xml)
        session = VoiceSession.objects.get(session_id="sess-dc-2")
        self.assertFalse(session.is_active)

    def test_pressing_other_digit_after_danger_words_just_ends_call(self):
        SupportService.objects.create(
            name="Uganda Police GBV Helpline",
            service_type="helpline",
            phone_number="0800199195",
            is_emergency_service=True,
        )
        handle_voice_request("sess-dc-3", "+256700000000", "1", "", "")
        with self._mock_transcript("he has a weapon right now"):
            handle_voice_request(
                "sess-dc-3", "+256700000000", "1", "", "https://example.com/r.mp3"
            )
        xml = handle_voice_request("sess-dc-3", "+256700000000", "1", "5", "")
        self.assertNotIn("<Dial", xml)
        session = VoiceSession.objects.get(session_id="sess-dc-3")
        self.assertFalse(session.is_active)

    def test_no_digit_after_danger_words_ends_call_not_regreets(self):
        SupportService.objects.create(
            name="Uganda Police GBV Helpline",
            service_type="helpline",
            phone_number="0800199195",
            is_emergency_service=True,
        )
        handle_voice_request("sess-dc-4", "+256700000000", "1", "", "")
        with self._mock_transcript("he has a weapon right now"):
            handle_voice_request(
                "sess-dc-4", "+256700000000", "1", "", "https://example.com/r.mp3"
            )
        xml = handle_voice_request("sess-dc-4", "+256700000000", "1", "", "")
        self.assertNotIn("Welcome to Sauti Yo", xml)
        self.assertNotIn("<Dial", xml)
        session = VoiceSession.objects.get(session_id="sess-dc-4")
        self.assertFalse(session.is_active)

    def test_safety_digit_2_offers_connect_instead_of_ending_immediately(self):
        situation = _create_home_safety_situation()
        VoiceSession.objects.create(
            session_id="sess-dc-5",
            phone_number="+256700000000",
            state="awaiting_safety_digit",
            context={"slug": situation.slug, "discreet": False},
        )
        xml = handle_voice_request("sess-dc-5", "+256700000000", "1", "2", "")
        self.assertIn("<GetDigits", xml)
        self.assertIn("Your safety matters. Call Sauti 116.", xml)
        session = VoiceSession.objects.get(session_id="sess-dc-5")
        self.assertTrue(session.is_active)
        self.assertEqual(session.state, "awaiting_crisis_connect_digit")

    def test_pressing_1_after_safety_digit_2_dials_situation_support_number(self):
        situation = _create_home_safety_situation()
        VoiceSession.objects.create(
            session_id="sess-dc-6",
            phone_number="+256700000000",
            state="awaiting_safety_digit",
            context={"slug": situation.slug, "discreet": False},
        )
        handle_voice_request("sess-dc-6", "+256700000000", "1", "2", "")
        xml = handle_voice_request("sess-dc-6", "+256700000000", "1", "1", "")
        self.assertIn('<Dial phoneNumbers="116"', xml)

    def test_safety_checkin_failed_closed_offers_connect(self):
        situation = _create_home_safety_situation()
        VoiceSession.objects.create(
            session_id="sess-dc-7",
            phone_number="+256700000000",
            state="awaiting_safety_digit",
            context={
                "slug": situation.slug,
                "discreet": False,
                "safety_check_attempts": 1,
            },
        )
        xml = handle_voice_request("sess-dc-7", "+256700000000", "1", "9", "")
        self.assertIn("<GetDigits", xml)
        self.assertIn("Your safety matters. Call Sauti 116.", xml)
        session = VoiceSession.objects.get(session_id="sess-dc-7")
        self.assertEqual(session.state, "awaiting_crisis_connect_digit")

    def test_post_reply_menu_digit_3_dials_support_number(self):
        situation = _create_home_safety_situation()
        VoiceSession.objects.create(
            session_id="sess-dc-8",
            phone_number="+256700000000",
            state="post_reply_menu",
            context={"slug": situation.slug, "discreet": False},
        )
        xml = handle_voice_request("sess-dc-8", "+256700000000", "1", "3", "")
        self.assertIn('<Dial phoneNumbers="116"', xml)
        session = VoiceSession.objects.get(session_id="sess-dc-8")
        self.assertFalse(session.is_active)

    def test_post_reply_menu_digit_3_falls_back_to_speaking_when_no_number(self):
        situation = _create_land_situation_without_safety_response()
        VoiceSession.objects.create(
            session_id="sess-dc-9",
            phone_number="+256700000000",
            state="post_reply_menu",
            context={"slug": situation.slug, "discreet": False},
        )
        xml = handle_voice_request("sess-dc-9", "+256700000000", "1", "3", "")
        self.assertNotIn("<Dial", xml)
        self.assertIn("<GetDigits", xml)

    def test_post_reply_menu_digit_3_does_not_fall_back_to_general_emergency_number(
        self,
    ):
        # Regression test: a standard-risk situation (e.g. a land dispute)
        # with no linked support service must NOT be silently connected to
        # the general emergency/GBV line just because one happens to be
        # configured - that would misdirect a non-crisis caller. Unlike the
        # crisis-connect path, "press 3" on the post-reply menu should only
        # ever use a number actually linked to this situation.
        situation = _create_land_situation_without_safety_response()
        SupportService.objects.create(
            name="Uganda Police GBV Helpline",
            service_type="helpline",
            phone_number="0800199195",
            is_emergency_service=True,
        )
        VoiceSession.objects.create(
            session_id="sess-dc-13",
            phone_number="+256700000000",
            state="post_reply_menu",
            context={"slug": situation.slug, "discreet": False},
        )
        xml = handle_voice_request("sess-dc-13", "+256700000000", "1", "3", "")
        self.assertNotIn("<Dial", xml)
        self.assertIn("<GetDigits", xml)
        session = VoiceSession.objects.get(session_id="sess-dc-13")
        self.assertTrue(session.is_active)

    def test_getdigits_timeout_during_crisis_connect_ends_call_not_regreets(self):
        situation = _create_home_safety_situation()
        VoiceSession.objects.create(
            session_id="sess-dc-10",
            phone_number="+256700000000",
            state="awaiting_crisis_connect_digit",
            context={"slug": situation.slug},
        )
        xml = handle_voice_request("sess-dc-10", "+256700000000", "1", "", "")
        self.assertNotIn("Welcome to Sauti Yo", xml)
        self.assertNotIn("<Dial", xml)
        session = VoiceSession.objects.get(session_id="sess-dc-10")
        self.assertFalse(session.is_active)

    def test_safety_digit_2_then_1_falls_back_to_general_number_when_situation_has_none(
        self,
    ):
        situation = _create_high_risk_situation_without_support_service()
        SupportService.objects.create(
            name="Uganda Police GBV Helpline",
            service_type="helpline",
            phone_number="0800199195",
            is_emergency_service=True,
        )
        VoiceSession.objects.create(
            session_id="sess-dc-11",
            phone_number="+256700000000",
            state="awaiting_safety_digit",
            context={"slug": situation.slug, "discreet": False},
        )
        handle_voice_request("sess-dc-11", "+256700000000", "1", "2", "")
        xml = handle_voice_request("sess-dc-11", "+256700000000", "1", "1", "")
        self.assertIn('<Dial phoneNumbers="0800199195"', xml)

    def test_offer_crisis_connect_skips_offer_when_nothing_dialable_anywhere(self):
        handle_voice_request("sess-dc-12", "+256700000000", "1", "", "")
        with self._mock_transcript("he has a weapon right now"):
            xml = handle_voice_request(
                "sess-dc-12", "+256700000000", "1", "", "https://example.com/r.mp3"
            )
        self.assertIn("999", xml)
        self.assertNotIn("<GetDigits", xml)
        session = VoiceSession.objects.get(session_id="sess-dc-12")
        self.assertFalse(session.is_active)
