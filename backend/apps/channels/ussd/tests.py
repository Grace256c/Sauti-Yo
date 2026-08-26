from django.db import IntegrityError
from django.test import TestCase

from apps.channels.models import UssdSession
from apps.channels.ussd import sessions


class UssdSessionModelTests(TestCase):
    def test_create_session_with_defaults(self):
        session = UssdSession.objects.create(
            session_id="abc123", phone_number="+256700000000"
        )
        self.assertEqual(session.state, "language_select")
        self.assertEqual(session.context, {})
        self.assertTrue(session.is_active)
        self.assertEqual(session.language, "")

    def test_session_id_is_unique(self):
        UssdSession.objects.create(
            session_id="dup", phone_number="+256700000000"
        )
        with self.assertRaises(IntegrityError):
            UssdSession.objects.create(
                session_id="dup", phone_number="+256711111111"
            )


class SessionHelperTests(TestCase):
    def test_get_or_create_session_creates_new_session(self):
        session, created = sessions.get_or_create_session(
            "new-session", "+256700000000"
        )
        self.assertTrue(created)
        self.assertEqual(session.state, "language_select")

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
        sessions.update_session(session, state="main_menu", language="en")

        session.refresh_from_db()
        self.assertEqual(session.state, "main_menu")
        self.assertEqual(session.language, "en")

    def test_end_session_marks_inactive(self):
        session, _ = sessions.get_or_create_session(
            "end-me", "+256700000000"
        )
        sessions.end_session(session)

        session.refresh_from_db()
        self.assertFalse(session.is_active)


from apps.channels.ussd import menus
from apps.content.models import ChannelContent


class TextHelperTests(TestCase):
    def test_truncate_returns_original_when_short(self):
        self.assertEqual(menus.truncate("hello", 10), "hello")

    def test_truncate_shortens_long_text_with_ellipsis(self):
        result = menus.truncate("a" * 20, 10)
        self.assertEqual(result, "a" * 7 + "...")
        self.assertEqual(len(result), 10)

    def test_chunk_text_splits_on_word_boundaries_within_budget(self):
        text = " ".join(["word"] * 10)
        chunks = menus.chunk_text(text, budget=14)
        self.assertTrue(all(len(chunk) <= 14 for chunk in chunks))
        self.assertEqual(" ".join(chunks), text)

    def test_chunk_text_returns_single_chunk_for_short_text(self):
        self.assertEqual(
            menus.chunk_text("short text", budget=160), ["short text"]
        )

    def test_chunk_text_of_empty_string_returns_single_empty_chunk(self):
        self.assertEqual(menus.chunk_text("", budget=160), [""])

    def test_paginate_items_returns_page_and_has_more_flag(self):
        items = list(range(12))
        page_items, has_more = menus.paginate_items(items, page=0, page_size=5)
        self.assertEqual(page_items, [0, 1, 2, 3, 4])
        self.assertTrue(has_more)

    def test_paginate_items_last_page_has_no_more(self):
        items = list(range(12))
        page_items, has_more = menus.paginate_items(items, page=2, page_size=5)
        self.assertEqual(page_items, [10, 11])
        self.assertFalse(has_more)


class GetCopyTests(TestCase):
    def test_falls_back_to_default_when_no_channel_content_row(self):
        text = menus.get_copy("ussd.main_menu", "en")
        self.assertEqual(text, menus.DEFAULT_COPY["ussd.main_menu"])

    def test_prefers_channel_content_row_when_present(self):
        ChannelContent.objects.create(
            content_key="ussd.main_menu",
            language="lg",
            channel="ussd",
            text="Ekika ky'obuyambi",
            is_active=True,
        )
        text = menus.get_copy("ussd.main_menu", "lg")
        self.assertEqual(text, "Ekika ky'obuyambi")

    def test_ignores_inactive_channel_content_row(self):
        ChannelContent.objects.create(
            content_key="ussd.main_menu",
            language="en",
            channel="ussd",
            text="Should not be used",
            is_active=False,
        )
        text = menus.get_copy("ussd.main_menu", "en")
        self.assertEqual(text, menus.DEFAULT_COPY["ussd.main_menu"])


class LanguageSelectTests(TestCase):
    def test_render_shows_welcome_and_language_options(self):
        session = UssdSession(state="language_select", language="", context={})
        text, ended = menus.render_language_select(session)
        self.assertIn("Welcome to Sauti Yo", text)
        self.assertIn("1. English", text)
        self.assertFalse(ended)

    def test_transition_sets_language_and_moves_to_main_menu(self):
        session = UssdSession(state="language_select", language="", context={})
        next_state, context = menus.transition_language_select(session, "2")
        self.assertEqual(next_state, "main_menu")
        self.assertEqual(session.language, "lg")
        self.assertEqual(context, {})

    def test_transition_rejects_invalid_choice(self):
        session = UssdSession(state="language_select", language="", context={})
        result = menus.transition_language_select(session, "9")
        self.assertIsNone(result)


class MainMenuTests(TestCase):
    def test_render_shows_menu_options(self):
        session = UssdSession(state="main_menu", language="en", context={})
        text, ended = menus.render_main_menu(session)
        self.assertIn("1. Find my rights", text)
        self.assertFalse(ended)

    def test_transition_to_situation_list(self):
        session = UssdSession(state="main_menu", language="en", context={})
        next_state, context = menus.transition_main_menu(session, "1")
        self.assertEqual(next_state, "situation_list")
        self.assertEqual(context, {"page": 0})

    def test_transition_to_emergency_list(self):
        session = UssdSession(state="main_menu", language="en", context={})
        next_state, context = menus.transition_main_menu(session, "2")
        self.assertEqual(next_state, "emergency_list")
        self.assertEqual(context, {"chunk_index": 0})

    def test_transition_exit_goes_to_goodbye(self):
        session = UssdSession(state="main_menu", language="en", context={})
        next_state, context = menus.transition_main_menu(session, "0")
        self.assertEqual(next_state, "goodbye")

    def test_transition_rejects_invalid_choice(self):
        session = UssdSession(state="main_menu", language="en", context={})
        self.assertIsNone(menus.transition_main_menu(session, "9"))


class GoodbyeTests(TestCase):
    def test_render_ends_session(self):
        session = UssdSession(state="goodbye", language="en", context={})
        text, ended = menus.render_goodbye(session)
        self.assertIn("Thank you", text)
        self.assertTrue(ended)
