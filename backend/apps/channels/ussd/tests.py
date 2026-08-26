from django.db import IntegrityError
from django.test import TestCase

from apps.channels.models import UssdSession
from apps.channels.ussd import sessions
from apps.channels.ussd.handler import handle_ussd_request


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


from apps.rights.models import RightsTopic, Situation, SituationRightsTopic


class SituationListTests(TestCase):
    def setUp(self):
        self.situations = [
            Situation.objects.create(slug=f"situation-{i}", title=f"Situation {i}")
            for i in range(7)
        ]

    def test_render_lists_first_page_with_more_option(self):
        session = UssdSession(
            state="situation_list", language="en", context={"page": 0}
        )
        text, ended = menus.render_situation_list(session)
        self.assertIn("1. Situation 0", text)
        self.assertIn("5. Situation 4", text)
        self.assertIn("8.", text)
        self.assertFalse(ended)

    def test_render_last_page_has_no_more_option(self):
        session = UssdSession(
            state="situation_list", language="en", context={"page": 1}
        )
        text, ended = menus.render_situation_list(session)
        self.assertIn("Situation 5", text)
        self.assertNotIn("8.", text)

    def test_render_with_no_situations_shows_empty_message(self):
        Situation.objects.all().delete()
        session = UssdSession(
            state="situation_list", language="en", context={"page": 0}
        )
        text, ended = menus.render_situation_list(session)
        self.assertIn("No situations", text)

    def test_transition_selects_situation_with_single_topic_skips_to_topic(self):
        situation = self.situations[0]
        topic = RightsTopic.objects.create(
            slug="topic-1", title="Topic 1", summary="Summary"
        )
        SituationRightsTopic.objects.create(
            situation=situation, rights_topic=topic
        )

        session = UssdSession(
            state="situation_list", language="en", context={"page": 0}
        )
        next_state, context = menus.transition_situation_list(session, "1")

        self.assertEqual(next_state, "topic_detail")
        self.assertEqual(context["topic_slug"], "topic-1")
        self.assertEqual(context["situation_slug"], "situation-0")

    def test_transition_selects_situation_with_multiple_topics_shows_detail(self):
        situation = self.situations[0]
        for i in range(2):
            topic = RightsTopic.objects.create(
                slug=f"multi-topic-{i}", title=f"Topic {i}", summary="Summary"
            )
            SituationRightsTopic.objects.create(
                situation=situation, rights_topic=topic
            )

        session = UssdSession(
            state="situation_list", language="en", context={"page": 0}
        )
        next_state, context = menus.transition_situation_list(session, "1")

        self.assertEqual(next_state, "situation_detail")
        self.assertEqual(
            context, {"situation_slug": "situation-0", "chunk_index": 0}
        )

    def test_transition_next_page(self):
        session = UssdSession(
            state="situation_list", language="en", context={"page": 0}
        )
        next_state, context = menus.transition_situation_list(session, "8")
        self.assertEqual(next_state, "situation_list")
        self.assertEqual(context, {"page": 1})

    def test_transition_back_to_main_menu(self):
        session = UssdSession(
            state="situation_list", language="en", context={"page": 0}
        )
        next_state, context = menus.transition_situation_list(session, "0")
        self.assertEqual(next_state, "main_menu")

    def test_transition_rejects_invalid_choice(self):
        session = UssdSession(
            state="situation_list", language="en", context={"page": 0}
        )
        self.assertIsNone(menus.transition_situation_list(session, "9"))


class SituationDetailTests(TestCase):
    def setUp(self):
        self.situation = Situation.objects.create(
            slug="eviction",
            title="Eviction",
            description="Long description. " * 20,
        )
        self.topic_a = RightsTopic.objects.create(
            slug="topic-a", title="Topic A", summary="Summary A"
        )
        self.topic_b = RightsTopic.objects.create(
            slug="topic-b", title="Topic B", summary="Summary B"
        )
        SituationRightsTopic.objects.create(
            situation=self.situation, rights_topic=self.topic_a
        )
        SituationRightsTopic.objects.create(
            situation=self.situation, rights_topic=self.topic_b
        )

    def test_render_shows_description_chunk_and_more_option(self):
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "chunk_index": 0},
        )
        text, ended = menus.render_situation_detail(session)
        self.assertIn("1. More", text)
        self.assertFalse(ended)

    def test_render_last_chunk_lists_topics(self):
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "chunk_index": 9999},
        )
        text, ended = menus.render_situation_detail(session)
        self.assertIn("1. Topic A", text)
        self.assertIn("2. Topic B", text)

    def test_render_last_chunk_does_not_end_session(self):
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "chunk_index": 9999},
        )
        text, ended = menus.render_situation_detail(session)
        self.assertFalse(ended)

    def test_transition_more_advances_chunk(self):
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "chunk_index": 0},
        )
        next_state, context = menus.transition_situation_detail(session, "1")
        self.assertEqual(next_state, "situation_detail")
        self.assertEqual(context["chunk_index"], 1)

    def test_transition_selects_topic_on_last_chunk(self):
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "chunk_index": 9999},
        )
        next_state, context = menus.transition_situation_detail(session, "1")
        self.assertEqual(next_state, "topic_detail")
        self.assertEqual(context["topic_slug"], "topic-a")

    def test_transition_back_returns_to_situation_list(self):
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "chunk_index": 9999},
        )
        next_state, context = menus.transition_situation_detail(session, "0")
        self.assertEqual(next_state, "situation_list")
        self.assertEqual(context, {"page": 0})

    def test_transition_selects_high_risk_topic_routes_to_safety_gate(self):
        from apps.rights.models import SafetyResponse

        self.topic_a.risk_level = "high_risk"
        self.topic_a.save()
        SafetyResponse.objects.create(
            rights_topic=self.topic_a,
            trigger_key="default",
            message="Call the emergency line immediately.",
            is_active=True,
        )

        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "chunk_index": 9999},
        )
        next_state, context = menus.transition_situation_detail(session, "1")

        self.assertEqual(next_state, "safety_gate")
        self.assertEqual(context["topic_slug"], "topic-a")


from apps.rights.models import ActionStep, SafetyResponse


class TopicDetailTests(TestCase):
    def setUp(self):
        self.topic = RightsTopic.objects.create(
            slug="topic-a", title="Topic A", summary="Summary text. " * 20
        )

    def _session(self, chunk_index=0, situation_slug="eviction"):
        return UssdSession(
            state="topic_detail",
            language="en",
            context={
                "situation_slug": situation_slug,
                "topic_slug": "topic-a",
                "chunk_index": chunk_index,
            },
        )

    def test_render_shows_summary_chunk_with_more(self):
        text, ended = menus.render_topic_detail(self._session(0))
        self.assertIn("1. More", text)
        self.assertFalse(ended)

    def test_render_last_chunk_shows_topic_menu(self):
        text, ended = menus.render_topic_detail(self._session(9999))
        self.assertIn("1. Action steps", text)
        self.assertIn("2. Support contacts", text)

    def test_transition_selects_action_steps(self):
        next_state, context = menus.transition_topic_detail(
            self._session(9999), "1"
        )
        self.assertEqual(next_state, "action_steps")
        self.assertEqual(context["step_index"], 0)
        self.assertEqual(context["chunk_index"], 0)

    def test_transition_selects_support_contacts(self):
        next_state, context = menus.transition_topic_detail(
            self._session(9999), "2"
        )
        self.assertEqual(next_state, "support_contacts")

    def test_transition_back_with_no_situation_returns_situation_list(self):
        next_state, context = menus.transition_topic_detail(
            self._session(9999), "0"
        )
        self.assertEqual(next_state, "situation_list")

    def test_render_last_chunk_does_not_end_session(self):
        text, ended = menus.render_topic_detail(self._session(9999))
        self.assertIn("1. Action steps", text)
        self.assertFalse(ended)


class SafetyGateTests(TestCase):
    def setUp(self):
        self.topic = RightsTopic.objects.create(
            slug="high-risk-topic",
            title="High Risk Topic",
            summary="Summary",
            risk_level="high_risk",
        )
        self.safety = SafetyResponse.objects.create(
            rights_topic=self.topic,
            trigger_key="default",
            message="Call the emergency line immediately. " * 10,
        )

    def _session(self, chunk_index=0):
        return UssdSession(
            state="safety_gate",
            language="en",
            context={
                "situation_slug": "eviction",
                "topic_slug": "high-risk-topic",
                "chunk_index": chunk_index,
            },
        )

    def test_render_shows_safety_message(self):
        text, ended = menus.render_safety_gate(self._session(0))
        self.assertIn("Call the emergency line", text)
        self.assertFalse(ended)

    def test_transition_continue_on_last_chunk_moves_to_topic_detail(self):
        next_state, context = menus.transition_safety_gate(
            self._session(9999), "1"
        )
        self.assertEqual(next_state, "topic_detail")
        self.assertEqual(context["chunk_index"], 0)

    def test_transition_rejects_invalid_choice_on_last_chunk(self):
        self.assertIsNone(menus.transition_safety_gate(self._session(9999), "9"))

    def test_render_last_chunk_does_not_end_session(self):
        text, ended = menus.render_safety_gate(self._session(9999))
        self.assertIn("1. Continue", text)
        self.assertFalse(ended)

    def test_render_falls_back_to_summary_when_no_safety_response(self):
        self.safety.delete()
        text, ended = menus.render_safety_gate(self._session(0))
        self.assertIn("Summary", text)
        self.assertFalse(ended)


class ActionStepsTests(TestCase):
    def setUp(self):
        self.topic = RightsTopic.objects.create(
            slug="topic-a", title="Topic A", summary="S"
        )
        self.step1 = ActionStep.objects.create(
            rights_topic=self.topic,
            order=1,
            title="Step One",
            description="Do this first.",
        )
        self.step2 = ActionStep.objects.create(
            rights_topic=self.topic,
            order=2,
            title="Step Two",
            description="Do this second.",
        )

    def _session(self, step_index=0, chunk_index=0):
        return UssdSession(
            state="action_steps",
            language="en",
            context={
                "situation_slug": "eviction",
                "topic_slug": "topic-a",
                "step_index": step_index,
                "chunk_index": chunk_index,
            },
        )

    def test_render_shows_first_step_with_next_option(self):
        text, ended = menus.render_action_steps(self._session())
        self.assertIn("Step 1/2", text)
        self.assertIn("1.", text)
        self.assertFalse(ended)

    def test_render_last_step_has_no_next_option(self):
        text, ended = menus.render_action_steps(self._session(step_index=1))
        self.assertIn("Step 2/2", text)
        self.assertNotIn("1.", text)

    def test_transition_next_moves_to_second_step(self):
        next_state, context = menus.transition_action_steps(self._session(), "1")
        self.assertEqual(next_state, "action_steps")
        self.assertEqual(context["step_index"], 1)
        self.assertEqual(context["chunk_index"], 0)

    def test_transition_back_returns_to_topic_detail(self):
        next_state, context = menus.transition_action_steps(self._session(), "0")
        self.assertEqual(next_state, "topic_detail")
        self.assertEqual(context["chunk_index"], 9999)

    def test_render_with_no_steps_shows_empty_message(self):
        ActionStep.objects.all().delete()
        text, ended = menus.render_action_steps(self._session())
        self.assertIn("No action steps", text)


from apps.support.models import SupportService


class SupportContactsTests(TestCase):
    def setUp(self):
        self.topic = RightsTopic.objects.create(
            slug="topic-a", title="Topic A", summary="S"
        )
        self.service = SupportService.objects.create(
            name="Legal Aid Clinic", phone_number="0800111222"
        )
        self.topic.support_services.add(self.service)

    def _session(self, chunk_index=0):
        return UssdSession(
            state="support_contacts",
            language="en",
            context={
                "situation_slug": "eviction",
                "topic_slug": "topic-a",
                "chunk_index": chunk_index,
            },
        )

    def test_render_lists_contact_name_and_phone(self):
        text, ended = menus.render_support_contacts(self._session())
        self.assertIn("Legal Aid Clinic", text)
        self.assertIn("0800111222", text)
        self.assertFalse(ended)

    def test_render_with_no_contacts_shows_empty_message(self):
        self.topic.support_services.clear()
        text, ended = menus.render_support_contacts(self._session())
        self.assertIn("No support contacts", text)

    def test_transition_back_returns_to_topic_detail(self):
        next_state, context = menus.transition_support_contacts(
            self._session(), "0"
        )
        self.assertEqual(next_state, "topic_detail")
        self.assertEqual(context["chunk_index"], 9999)

    def test_render_last_chunk_does_not_end_session(self):
        text, ended = menus.render_support_contacts(self._session(9999))
        self.assertFalse(ended)


class EmergencyListTests(TestCase):
    def setUp(self):
        self.emergency_service = SupportService.objects.create(
            name="Police Hotline", phone_number="999", is_emergency_service=True
        )
        SupportService.objects.create(
            name="Regular Clinic",
            phone_number="0800000000",
            is_emergency_service=False,
        )

    def _session(self, chunk_index=0):
        return UssdSession(
            state="emergency_list", language="en", context={"chunk_index": chunk_index}
        )

    def test_render_only_lists_emergency_services(self):
        text, ended = menus.render_emergency_list(self._session())
        self.assertIn("Police Hotline", text)
        self.assertNotIn("Regular Clinic", text)

    def test_transition_back_returns_to_main_menu(self):
        next_state, context = menus.transition_emergency_list(self._session(), "0")
        self.assertEqual(next_state, "main_menu")

    def test_render_with_no_emergency_contacts_shows_empty_message(self):
        SupportService.objects.all().delete()
        text, ended = menus.render_emergency_list(self._session())
        self.assertIn("No emergency contacts", text)

    def test_render_last_chunk_does_not_end_session(self):
        text, ended = menus.render_emergency_list(self._session(9999))
        self.assertFalse(ended)


class HandleUssdRequestTests(TestCase):
    def setUp(self):
        self.situation = Situation.objects.create(slug="eviction", title="Eviction")
        self.topic = RightsTopic.objects.create(
            slug="topic-a", title="Topic A", summary="Short summary"
        )
        SituationRightsTopic.objects.create(
            situation=self.situation, rights_topic=self.topic
        )

    def test_new_session_shows_language_picker(self):
        response = handle_ussd_request("sess-1", "+256700000000", "")
        self.assertTrue(response.startswith("CON "))
        self.assertIn("1. English", response)

        session = UssdSession.objects.get(session_id="sess-1")
        self.assertEqual(session.state, "language_select")
        self.assertTrue(session.is_active)

    def test_full_flow_reaches_topic_detail(self):
        handle_ussd_request("sess-2", "+256700000000", "")
        handle_ussd_request("sess-2", "+256700000000", "1")
        handle_ussd_request("sess-2", "+256700000000", "1*1")
        response = handle_ussd_request("sess-2", "+256700000000", "1*1*1")

        self.assertIn("Short summary", response)
        session = UssdSession.objects.get(session_id="sess-2")
        self.assertEqual(session.state, "topic_detail")
        self.assertEqual(session.language, "en")

    def test_exit_ends_session(self):
        handle_ussd_request("sess-3", "+256700000000", "")
        handle_ussd_request("sess-3", "+256700000000", "1")
        response = handle_ussd_request("sess-3", "+256700000000", "1*0")

        self.assertTrue(response.startswith("END "))
        session = UssdSession.objects.get(session_id="sess-3")
        self.assertFalse(session.is_active)

    def test_invalid_input_redisplays_screen_with_prefix(self):
        handle_ussd_request("sess-4", "+256700000000", "")
        response = handle_ussd_request("sess-4", "+256700000000", "9")
        self.assertTrue(response.startswith("CON Invalid choice."))

        session = UssdSession.objects.get(session_id="sess-4")
        self.assertEqual(session.context.get("attempts"), 1)

    def test_three_invalid_attempts_ends_session(self):
        handle_ussd_request("sess-5", "+256700000000", "")
        handle_ussd_request("sess-5", "+256700000000", "9")
        handle_ussd_request("sess-5", "+256700000000", "9*9")
        response = handle_ussd_request("sess-5", "+256700000000", "9*9*9")

        self.assertTrue(response.startswith("END "))
        self.assertIn("Too many invalid attempts", response)
        session = UssdSession.objects.get(session_id="sess-5")
        self.assertFalse(session.is_active)

    def test_stale_session_id_restarts_at_language_picker(self):
        response = handle_ussd_request("unknown-session", "+256700000000", "1*1*1")
        self.assertIn("1. English", response)
        session = UssdSession.objects.get(session_id="unknown-session")
        self.assertEqual(session.state, "language_select")
