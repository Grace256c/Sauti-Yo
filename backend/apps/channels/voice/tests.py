from django.db import IntegrityError
from django.test import TestCase

from apps.channels.models import VoiceSession
from apps.channels.voice import sessions


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
