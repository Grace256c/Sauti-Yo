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
from apps.channels.voice.handler import handle_voice_request


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

    def test_recording_with_danger_words_ends_call_with_safety_reply(self):
        handle_voice_request("sess-2", "+256700000000", "1", "", "")
        with self._mock_transcript("he has a weapon right now"):
            xml = handle_voice_request(
                "sess-2", "+256700000000", "1", "", "https://example.com/r.mp3"
            )
        self.assertIn("999", xml)
        self.assertNotIn("<GetDigits", xml)
        session = VoiceSession.objects.get(session_id="sess-2")
        self.assertFalse(session.is_active)

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
        self.assertFalse(session.is_active)

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

    def test_safety_digit_2_ends_call_with_safety_reply(self):
        _create_home_safety_situation()
        VoiceSession.objects.create(
            session_id="sess-5",
            phone_number="+256700000000",
            state="awaiting_safety_digit",
            context={"slug": "home-safety", "discreet": False},
        )
        xml = handle_voice_request("sess-5", "+256700000000", "1", "2", "")
        self.assertIn("Your safety matters. Call Sauti 116.", xml)
        self.assertNotIn("<GetDigits", xml)
        session = VoiceSession.objects.get(session_id="sess-5")
        self.assertFalse(session.is_active)

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
        self.assertFalse(session.is_active)

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
