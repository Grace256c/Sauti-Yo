from unittest.mock import MagicMock, patch

from django.db import IntegrityError
from django.test import TestCase, override_settings
from requests.exceptions import ConnectionError as RequestsConnectionError

from apps.channels.models import VoiceSession
from apps.channels.voice import sessions, transcription


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
