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

    def test_chunk_text_preserves_newlines_within_budget(self):
        text = "Line one.\nLine two.\nLine three."
        chunks = menus.chunk_text(text, budget=160)
        self.assertEqual(chunks, ["Line one.\nLine two.\nLine three."])

    def test_chunk_text_never_merges_two_original_lines_onto_one_line(self):
        text = "Alice: 0700000001\nBob: 0700000002\nCarol: 0700000003"
        chunks = menus.chunk_text(text, budget=160)
        joined = "\n".join(chunks)
        for original_line in text.split("\n"):
            self.assertIn(original_line, joined.split("\n"))

    def test_chunk_text_hard_splits_a_single_token_longer_than_budget(self):
        long_token = "a" * 50
        chunks = menus.chunk_text(long_token, budget=20)
        self.assertTrue(all(len(chunk) <= 20 for chunk in chunks))
        self.assertEqual("".join(chunks), long_token)

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


class ChunkedScreenTests(TestCase):
    def test_final_chunk_includes_exit_and_uses_nine_for_back(self):
        screen, is_last = menus._chunked_screen(
            "Body text", 0, "1. Continue\n9. Back", "en"
        )
        self.assertTrue(is_last)
        self.assertIn("0. Exit", screen)
        self.assertIn("9. Back", screen)

    def test_intermediate_chunk_includes_more_back_and_exit(self):
        long_text = " ".join(["word"] * 60)
        screen, is_last = menus._chunked_screen(
            long_text, 0, "1. Continue\n9. Back", "en"
        )
        self.assertFalse(is_last)
        self.assertIn("1. More", screen)
        self.assertIn("9. Back", screen)
        self.assertIn("0. Exit", screen)
        self.assertLessEqual(len(screen), 182)


class GetCopyTests(TestCase):
    def test_falls_back_to_default_when_no_channel_content_row(self):
        text = menus.get_copy("ussd.main_menu", "en")
        self.assertEqual(text, menus.DEFAULT_COPY["ussd.main_menu"])

    def test_prefers_channel_content_row_when_present(self):
        ChannelContent.objects.filter(
            content_key="ussd.main_menu",
            language="lg",
            channel="ussd",
        ).delete()

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

    def test_exit_copy_defaults_to_exit_label(self):
        self.assertEqual(menus.get_copy("ussd.exit", "en"), "Exit")

    def test_topic_menu_copy_uses_nine_for_back(self):
        self.assertIn("9. Back", menus.get_copy("ussd.topic_menu", "en"))

    def test_continue_copy_uses_nine_for_back(self):
        self.assertIn("9. Back", menus.get_copy("ussd.continue", "en"))

    def test_safety_continue_copy_uses_nine_for_back(self):
        self.assertIn("9. Back", menus.get_copy("ussd.safety_continue", "en"))


class LanguageSelectTests(TestCase):
    def test_render_shows_welcome_and_language_options(self):
        session = UssdSession(state="language_select", language="", context={})
        text, ended = menus.render_language_select(session)
        self.assertIn("Welcome to Sauti Yo", text)
        self.assertIn("1. English", text)
        self.assertFalse(ended)

    def test_render_shows_unavailable_notice_when_flagged(self):
        session = UssdSession(
            state="language_select",
            language="",
            context={"unavailable_notice": True},
        )
        text, ended = menus.render_language_select(session)
        self.assertIn("not available yet", text)
        self.assertIn("1. English", text)
        self.assertFalse(ended)

    def test_transition_english_sets_language_and_moves_to_main_menu(self):
        session = UssdSession(state="language_select", language="", context={})
        next_state, context = menus.transition_language_select(session, "1")
        self.assertEqual(next_state, "main_menu")
        self.assertEqual(session.language, "en")
        self.assertEqual(context, {})

    def test_transition_supported_languages_move_to_main_menu(self):
        cases = (
            ("2", "lg"),
            ("3", "sw"),
            ("4", "nyn"),
        )

        for digit, expected_language in cases:
            session = UssdSession(
                state="language_select",
                language="",
                context={},
            )

            next_state, context = (
                menus.transition_language_select(
                    session,
                    digit,
                )
            )

            self.assertEqual(
                next_state,
                "main_menu",
            )
            self.assertEqual(
                context,
                {},
            )
            self.assertEqual(
                session.language,
                expected_language,
            )

    def test_transition_rejects_invalid_choice(self):
        session = UssdSession(state="language_select", language="", context={})
        result = menus.transition_language_select(session, "9")
        self.assertIsNone(result)

    def test_render_unavailable_notice_uses_requested_language_for_lookup(self):
        from apps.content.models import ChannelContent

        ChannelContent.objects.create(
            content_key="ussd.language_unavailable",
            language="lg",
            channel="ussd",
            text="Olulimi olwo terukyaali kati.",
            is_active=True,
        )
        session = UssdSession(
            state="language_select",
            language="",
            context={"unavailable_notice": True, "requested_language": "lg"},
        )
        text, ended = menus.render_language_select(session)
        self.assertIn("Olulimi olwo terukyaali kati.", text)
        self.assertFalse(ended)


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
        next_state, context = menus.transition_state("main_menu", session, "0")
        self.assertEqual(next_state, "goodbye")
        self.assertEqual(context, {})

    def test_transition_rejects_invalid_choice(self):
        session = UssdSession(state="main_menu", language="en", context={})
        self.assertIsNone(menus.transition_main_menu(session, "9"))


class GoodbyeTests(TestCase):
    def test_render_ends_session(self):
        session = UssdSession(state="goodbye", language="en", context={})
        text, ended = menus.render_goodbye(session)
        self.assertIn("Thank you", text)
        self.assertTrue(ended)


class GlobalExitTests(TestCase):
    def test_exit_from_situation_list_ends_session(self):
        session = UssdSession(
            state="situation_list", language="en", context={"page": 0}
        )
        next_state, context = menus.transition_state("situation_list", session, "0")
        self.assertEqual(next_state, "goodbye")
        self.assertEqual(context, {})

    def test_exit_from_topic_detail_ends_session(self):
        session = UssdSession(
            state="topic_detail",
            language="en",
            context={
                "situation_slug": "eviction",
                "topic_slug": "topic-a",
                "chunk_index": 0,
            },
        )
        next_state, context = menus.transition_state("topic_detail", session, "0")
        self.assertEqual(next_state, "goodbye")

    def test_exit_from_action_steps_ends_session(self):
        session = UssdSession(
            state="action_steps",
            language="en",
            context={
                "situation_slug": "eviction",
                "topic_slug": "topic-a",
                "step_index": 0,
                "chunk_index": 0,
            },
        )
        next_state, context = menus.transition_state("action_steps", session, "0")
        self.assertEqual(next_state, "goodbye")

    def test_exit_from_language_select_ends_session(self):
        session = UssdSession(state="language_select", language="", context={})
        next_state, context = menus.transition_state(
            "language_select", session, "0"
        )
        self.assertEqual(next_state, "goodbye")


from apps.rights.models import RightsTopic, Situation, SituationRightsTopic


class SituationListTests(TestCase):
    def setUp(self):
        self.situations = [
            Situation.objects.create(
                slug=f"situation-{i}",
                title=f"Realistic long situation title number {i} about a legal issue",
            )
            for i in range(7)
        ]

    def test_render_screen_never_exceeds_africas_talking_screen_cap(self):
        session = UssdSession(
            state="situation_list", language="en", context={"page": 0}
        )
        text, ended = menus.render_situation_list(session)
        self.assertLessEqual(len(text), 182)
        self.assertFalse(ended)

    def test_render_first_page_shows_more_option_when_not_all_fit(self):
        session = UssdSession(
            state="situation_list", language="en", context={"page": 0}
        )
        text, ended = menus.render_situation_list(session)
        self.assertIn("1. ", text)
        self.assertIn("8.", text)

    def test_transition_next_page_advances_past_shown_items(self):
        session = UssdSession(
            state="situation_list", language="en", context={"page": 0}
        )
        next_state, context = menus.transition_situation_list(session, "8")
        self.assertEqual(next_state, "situation_list")
        self.assertGreater(context["page"], 0)
        self.assertLess(context["page"], len(self.situations))

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

    def test_render_last_chunk_offers_continue_to_topics(self):
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "chunk_index": 9999},
        )
        text, ended = menus.render_situation_detail(session)
        self.assertIn("1. Continue", text)
        self.assertFalse(ended)

    def test_render_topics_stage_lists_topics(self):
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "stage": "topics", "page": 0},
        )
        text, ended = menus.render_situation_detail(session)
        self.assertIn("1. Topic A", text)
        self.assertIn("2. Topic B", text)
        self.assertIn("9. Back", text)
        self.assertIn("0. Exit", text)
        self.assertFalse(ended)

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

    def test_transition_continue_on_last_chunk_enters_topics_stage(self):
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "chunk_index": 9999},
        )
        next_state, context = menus.transition_situation_detail(session, "1")
        self.assertEqual(next_state, "situation_detail")
        self.assertEqual(context["stage"], "topics")
        self.assertEqual(context["page"], 0)

    def test_transition_selects_topic_in_topics_stage(self):
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "stage": "topics", "page": 0},
        )
        next_state, context = menus.transition_situation_detail(session, "1")
        self.assertEqual(next_state, "topic_detail")
        self.assertEqual(context["topic_slug"], "topic-a")

    def test_transition_topics_stage_back_returns_to_situation_list(self):
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "stage": "topics", "page": 0},
        )
        next_state, context = menus.transition_situation_detail(session, "9")
        self.assertEqual(next_state, "situation_list")
        self.assertEqual(context, {"page": 0})

    def test_transition_back_returns_to_situation_list(self):
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "chunk_index": 9999},
        )
        next_state, context = menus.transition_situation_detail(session, "9")
        self.assertEqual(next_state, "situation_list")
        self.assertEqual(context, {"page": 0})

    def test_transition_back_returns_to_situation_list_before_last_chunk(self):
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "chunk_index": 0},
        )
        next_state, context = menus.transition_situation_detail(session, "9")
        self.assertEqual(next_state, "situation_list")
        self.assertEqual(context, {"page": 0})

    def test_render_topics_stage_never_exceeds_screen_cap_with_many_topics(self):
        for i in range(7):
            topic = RightsTopic.objects.create(
                slug=f"budget-topic-{i}",
                title=f"A reasonably long rights topic title number {i}",
                summary="Summary",
            )
            SituationRightsTopic.objects.create(
                situation=self.situation, rights_topic=topic
            )
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "stage": "topics", "page": 0},
        )
        text, ended = menus.render_situation_detail(session)
        self.assertLessEqual(len(text), 182)

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
        _, context = menus.transition_situation_detail(session, "1")
        session.context = context
        next_state, context = menus.transition_situation_detail(session, "1")

        self.assertEqual(next_state, "safety_gate")
        self.assertEqual(context["topic_slug"], "topic-a")

    def test_many_topics_are_reachable_via_more_not_silently_dropped(self):
        for i in range(7):
            topic = RightsTopic.objects.create(
                slug=f"reachable-topic-{i}",
                title=f"A reasonably long rights topic title number {i}",
                summary="Summary",
            )
            SituationRightsTopic.objects.create(
                situation=self.situation, rights_topic=topic
            )
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "stage": "topics", "page": 0},
        )
        text, ended = menus.render_situation_detail(session)
        self.assertIn("8.", text)
        self.assertLessEqual(len(text), 182)

        next_state, context = menus.transition_situation_detail(session, "8")
        self.assertEqual(next_state, "situation_detail")
        self.assertEqual(context["stage"], "topics")
        self.assertGreater(context["page"], 0)

        session2 = UssdSession(
            state="situation_detail", language="en", context=context
        )
        text2, _ = menus.render_situation_detail(session2)
        self.assertLessEqual(len(text2), 182)

    def test_description_with_many_linked_topics_does_not_fragment(self):
        for i in range(3):
            topic = RightsTopic.objects.create(
                slug=f"frag-topic-{i}",
                title=f"A reasonably long rights topic title number {i}",
                summary="Summary",
            )
            SituationRightsTopic.objects.create(
                situation=self.situation, rights_topic=topic
            )
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "chunk_index": 0},
        )
        text, ended = menus.render_situation_detail(session)
        # The description body chunk (everything before the blank-line separator
        # and the short "1. Continue\n9. Back\n0. Exit" trailing) should be a
        # substantial fraction of the screen budget, not a ~16-character fragment.
        body = text.split("\n\n")[0]
        self.assertGreater(len(body), 100)

    def test_long_unbreakable_token_never_exceeds_screen_cap(self):
        self.situation.description = (
            "See this resource: "
            "https://example.org/a/very/long/url/that/does/not/contain/any/spaces/at/all/whatsoever/for/testing"
        )
        self.situation.save()
        for i in range(3):
            topic = RightsTopic.objects.create(
                slug=f"url-topic-{i}",
                title=f"A reasonably long rights topic title number {i}",
                summary="Summary",
            )
            SituationRightsTopic.objects.create(
                situation=self.situation, rights_topic=topic
            )
        for chunk_index in range(6):
            session = UssdSession(
                state="situation_detail",
                language="en",
                context={"situation_slug": "eviction", "chunk_index": chunk_index},
            )
            text, ended = menus.render_situation_detail(session)
            self.assertLessEqual(
                len(text), 182, f"chunk_index={chunk_index} produced {len(text)} chars"
            )

    def test_token_longer_than_body_budget_is_split_and_stays_within_cap(self):
        """
        The description body budget for situation_detail is 139 chars, so the
        98-char URL above never exercises the hard-split path. Use a token that
        genuinely exceeds the budget: without _wrap_words' hard split this
        renders a single ~321-char screen and loses the "9. Back" option.
        """
        self.situation.description = "See this resource: https://example.org/" + (
            "z" * 280
        )
        self.situation.save()

        seen_chunks = 0
        for chunk_index in range(12):
            session = UssdSession(
                state="situation_detail",
                language="en",
                context={"situation_slug": "eviction", "chunk_index": chunk_index},
            )
            text, _ = menus.render_situation_detail(session)
            self.assertLessEqual(
                len(text), 182, f"chunk_index={chunk_index} produced {len(text)} chars"
            )
            self.assertIn("9. Back", text)
            seen_chunks += 1
        self.assertGreater(seen_chunks, 0)

    def test_back_from_topic_with_multiple_topics_returns_to_topics_stage(self):
        next_state, context = menus._back_from_topic("eviction", "topic-a")
        self.assertEqual(next_state, "situation_detail")
        self.assertEqual(context["stage"], "topics")
        self.assertEqual(context["page"], 0)

    def test_back_from_topic_with_single_topic_returns_to_situation_list(self):
        SituationRightsTopic.objects.filter(rights_topic=self.topic_b).delete()
        next_state, context = menus._back_from_topic("eviction", "topic-a")
        self.assertEqual(next_state, "situation_list")
        self.assertEqual(context, {"page": 0})

    def test_render_with_no_linked_topics_shows_back_and_exit(self):
        Situation.objects.create(slug="no-topics-situation", title="No Topics")
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "no-topics-situation", "chunk_index": 9999},
        )
        text, ended = menus.render_situation_detail(session)
        self.assertIn("9. Back", text)
        self.assertIn("0. Exit", text)
        self.assertFalse(ended)


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
        self.assertIn("9. Back", text)
        self.assertIn("0. Exit", text)

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
            self._session(9999), "9"
        )
        self.assertEqual(next_state, "situation_list")

    def test_transition_back_before_last_chunk_returns_situation_list(self):
        next_state, context = menus.transition_topic_detail(
            self._session(0), "9"
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
            verification_status="verified",
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
        self.assertIsNone(menus.transition_safety_gate(self._session(9999), "5"))

    def test_transition_back_on_last_chunk_returns_via_back_from_topic(self):
        next_state, context = menus.transition_safety_gate(self._session(9999), "9")
        self.assertEqual(next_state, "situation_list")
        self.assertEqual(context, {"page": 0})

    def test_transition_back_before_last_chunk_returns_via_back_from_topic(self):
        next_state, context = menus.transition_safety_gate(self._session(0), "9")
        self.assertEqual(next_state, "situation_list")
        self.assertEqual(context, {"page": 0})

    def test_render_last_chunk_does_not_end_session(self):
        text, ended = menus.render_safety_gate(self._session(9999))
        self.assertIn("1. Continue", text)
        self.assertIn("9. Back", text)
        self.assertIn("0. Exit", text)
        self.assertFalse(ended)

    def test_render_falls_back_to_summary_when_no_safety_response(self):
        self.safety.delete()
        text, ended = menus.render_safety_gate(self._session(0))
        self.assertIn("Summary", text)
        self.assertFalse(ended)

    def test_high_risk_topic_with_no_safety_response_still_gates(self):
        topic = RightsTopic.objects.create(
            slug="no-response-topic",
            title="No Response Topic",
            summary="Fallback summary text",
            risk_level="high_risk",
        )
        next_state, context = menus._enter_topic("some-situation", topic)
        self.assertEqual(next_state, "safety_gate")


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
        self.assertIn("0. Exit", text)
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
        next_state, context = menus.transition_action_steps(self._session(), "9")
        self.assertEqual(next_state, "topic_detail")
        self.assertEqual(context["chunk_index"], 9999)

    def test_render_with_no_steps_shows_empty_message(self):
        ActionStep.objects.all().delete()
        text, ended = menus.render_action_steps(self._session())
        self.assertIn("No action steps", text)
        self.assertIn("9. Back", text)
        self.assertIn("0. Exit", text)

    def test_transition_back_with_no_steps_returns_to_topic_detail(self):
        ActionStep.objects.all().delete()
        next_state, context = menus.transition_action_steps(self._session(), "9")
        self.assertEqual(next_state, "topic_detail")
        self.assertEqual(context["chunk_index"], 9999)


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
        self.assertIn("9. Back", text)
        self.assertIn("0. Exit", text)

    def test_transition_back_with_no_contacts_returns_to_topic_detail(self):
        self.topic.support_services.clear()
        next_state, context = menus.transition_support_contacts(
            self._session(), "9"
        )
        self.assertEqual(next_state, "topic_detail")

    def test_transition_back_returns_to_topic_detail(self):
        next_state, context = menus.transition_support_contacts(
            self._session(), "9"
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
        next_state, context = menus.transition_emergency_list(self._session(), "9")
        self.assertEqual(next_state, "main_menu")

    def test_render_with_no_emergency_contacts_shows_empty_message(self):
        SupportService.objects.all().delete()
        text, ended = menus.render_emergency_list(self._session())
        self.assertIn("No emergency contacts", text)
        self.assertIn("9. Back", text)
        self.assertIn("0. Exit", text)

    def test_transition_back_with_no_contacts_returns_to_main_menu(self):
        SupportService.objects.all().delete()
        next_state, context = menus.transition_emergency_list(self._session(), "9")
        self.assertEqual(next_state, "main_menu")

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

    def test_exit_from_mid_flow_ends_session(self):
        handle_ussd_request("sess-exit-midflow", "+256700000000", "")
        handle_ussd_request("sess-exit-midflow", "+256700000000", "1")
        handle_ussd_request("sess-exit-midflow", "+256700000000", "1*1")
        response = handle_ussd_request(
            "sess-exit-midflow", "+256700000000", "1*1*0"
        )

        self.assertTrue(response.startswith("END "))
        session = UssdSession.objects.get(session_id="sess-exit-midflow")
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

    def test_replayed_request_returns_cached_response_without_double_advancing(self):
        handle_ussd_request("sess-replay", "+256700000000", "")
        first_response = handle_ussd_request("sess-replay", "+256700000000", "1")
        replayed_response = handle_ussd_request("sess-replay", "+256700000000", "1")
        self.assertEqual(first_response, replayed_response)

        session = UssdSession.objects.get(session_id="sess-replay")
        self.assertEqual(session.state, "main_menu")

    def test_request_after_goodbye_restarts_instead_of_crashing(self):
        handle_ussd_request("sess-restart", "+256700000000", "")
        handle_ussd_request("sess-restart", "+256700000000", "1")
        handle_ussd_request("sess-restart", "+256700000000", "1*0")

        response = handle_ussd_request("sess-restart", "+256700000000", "1*0*1")
        self.assertIn("1. English", response)

    def test_stale_session_id_restarts_at_language_picker(self):
        response = handle_ussd_request("unknown-session", "+256700000000", "1*1*1")
        self.assertIn("1. English", response)
        session = UssdSession.objects.get(session_id="unknown-session")
        self.assertEqual(session.state, "language_select")

    def test_non_consecutive_invalid_attempts_do_not_end_session(self):
        """
        Regression test for Task 8 finding: verify that valid transitions
        strip the "attempts" counter from context, so that non-consecutive
        invalid attempts do not accumulate.

        Scenario:
        1. One invalid attempt in situation_detail (attempts=1)
        2. Valid chunk-advance navigation (this spreads context including attempts)
        3. Fix should strip attempts; without fix, it would persist
        4. Another invalid attempt should reset to 1, not increment to 2
        """
        # Update situation to have a long description (multiple chunks)
        self.situation.description = "Long description. " * 20
        self.situation.save()

        # Create a second topic so we navigate through situation_detail
        # (not auto-skip to topic_detail)
        long_topic = RightsTopic.objects.create(
            slug="topic-long", title="Topic Long", summary="Long summary. " * 20
        )
        SituationRightsTopic.objects.create(
            situation=self.situation, rights_topic=long_topic
        )

        # Navigate: language -> main menu -> situation_list -> situation_detail
        handle_ussd_request("sess-attempts", "+256700000000", "")
        handle_ussd_request("sess-attempts", "+256700000000", "1")  # English
        handle_ussd_request("sess-attempts", "+256700000000", "1*1")  # Find my rights
        handle_ussd_request("sess-attempts", "+256700000000", "1*1*1")  # Select first situation

        # Now in situation_detail at chunk_index=0
        session = UssdSession.objects.get(session_id="sess-attempts")
        self.assertEqual(session.state, "situation_detail")
        self.assertEqual(session.context.get("chunk_index"), 0)

        # Invalid attempt in situation_detail (only "1" for More and "9" for
        # Back are valid on a non-last chunk; use "7" as the invalid digit
        # since Task 3 made "9" a valid Back input on this screen)
        handle_ussd_request("sess-attempts", "+256700000000", "1*1*1*7")
        session.refresh_from_db()
        self.assertEqual(session.context.get("attempts"), 1)
        self.assertEqual(session.state, "situation_detail")
        self.assertEqual(session.context.get("chunk_index"), 0)

        # Valid navigation: "1" for More (this spreads context including attempts)
        # The fix should strip the attempts key from next_context before persisting
        handle_ussd_request("sess-attempts", "+256700000000", "1*1*1*7*1")
        session.refresh_from_db()
        self.assertNotIn("attempts", session.context)
        self.assertEqual(session.state, "situation_detail")
        self.assertEqual(session.context.get("chunk_index"), 1)
        self.assertTrue(session.is_active)

        # Another invalid attempt should count as 1, not 2
        # (because attempts was stripped from context on the previous valid transition)
        handle_ussd_request("sess-attempts", "+256700000000", "1*1*1*7*1*7")
        session.refresh_from_db()
        self.assertEqual(session.context.get("attempts"), 1)
        self.assertTrue(session.is_active)

    def test_luganda_language_pick_enters_translated_main_menu(self):
        handle_ussd_request(
            "sess-lang-lg",
            "+256700000000",
            "",
        )

        response = handle_ussd_request(
            "sess-lang-lg",
            "+256700000000",
            "2",
        )

        session = UssdSession.objects.get(
            session_id="sess-lang-lg",
        )

        self.assertEqual(
            session.language,
            "lg",
        )
        self.assertEqual(
            session.state,
            "main_menu",
        )
        self.assertIn(
            "Noonya eddembe lyange",
            response,
        )

    def test_kiswahili_language_pick_enters_translated_main_menu(self):
        handle_ussd_request(
            "sess-lang-sw",
            "+256700000000",
            "",
        )

        response = handle_ussd_request(
            "sess-lang-sw",
            "+256700000000",
            "3",
        )

        session = UssdSession.objects.get(
            session_id="sess-lang-sw",
        )

        self.assertEqual(
            session.language,
            "sw",
        )
        self.assertEqual(
            session.state,
            "main_menu",
        )
        self.assertIn(
            "Tafuta haki zangu",
            response,
        )

    def test_replayed_supported_language_pick_returns_cached_response(self):
        handle_ussd_request(
            "sess-lang-replay",
            "+256700000000",
            "",
        )

        first_response = handle_ussd_request(
            "sess-lang-replay",
            "+256700000000",
            "4",
        )

        replayed_response = handle_ussd_request(
            "sess-lang-replay",
            "+256700000000",
            "4",
        )

        self.assertEqual(
            first_response,
            replayed_response,
        )

        session = UssdSession.objects.get(
            session_id="sess-lang-replay",
        )

        self.assertEqual(
            session.state,
            "main_menu",
        )
        self.assertEqual(
            session.language,
            "nyn",
        )
        self.assertIn(
            "Ronda obugabe bwangye",
            first_response,
        )

from django.urls import reverse


class UssdCallbackViewTests(TestCase):
    def test_post_returns_plain_text_response(self):
        response = self.client.post(
            reverse("ussd-callback"),
            data={
                "sessionId": "view-sess-1",
                "phoneNumber": "+256700000000",
                "text": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertTrue(response.content.decode().startswith("CON "))

    def test_get_not_allowed(self):
        response = self.client.get(reverse("ussd-callback"))
        self.assertEqual(response.status_code, 405)


class UnreviewedNoticeTests(TestCase):
    def test_prepend_notice_leaves_verified_text_unchanged(self):
        text = menus._prepend_unreviewed_notice("Some text.", "verified", "en")
        self.assertEqual(text, "Some text.")

    def test_prepend_notice_adds_notice_for_review_required(self):
        text = menus._prepend_unreviewed_notice(
            "Some text.", "review_required", "en"
        )
        self.assertTrue(text.startswith("Note: not yet reviewed. "))
        self.assertIn("Some text.", text)

    def test_prepend_notice_adds_notice_for_expired_and_archived(self):
        for status in ("expired", "archived"):
            text = menus._prepend_unreviewed_notice("Some text.", status, "en")
            self.assertTrue(text.startswith("Note: not yet reviewed. "))

    def test_prepend_notice_on_empty_text_returns_just_the_notice(self):
        text = menus._prepend_unreviewed_notice("", "review_required", "en")
        self.assertEqual(text, "Note: not yet reviewed.")

    def test_render_topic_detail_shows_notice_for_review_required_topic(self):
        RightsTopic.objects.create(
            slug="unreviewed-topic",
            title="Unreviewed Topic",
            summary="Short summary.",
            verification_status="review_required",
        )
        session = UssdSession(
            state="topic_detail",
            language="en",
            context={
                "situation_slug": "s",
                "topic_slug": "unreviewed-topic",
                "chunk_index": 0,
            },
        )
        text, ended = menus.render_topic_detail(session)
        self.assertIn("Note: not yet reviewed.", text)
        self.assertIn("Short summary.", text)
        self.assertFalse(ended)

    def test_render_topic_detail_shows_no_notice_for_verified_topic(self):
        RightsTopic.objects.create(
            slug="verified-topic",
            title="Verified Topic",
            summary="Short summary.",
            verification_status="verified",
        )
        session = UssdSession(
            state="topic_detail",
            language="en",
            context={
                "situation_slug": "s",
                "topic_slug": "verified-topic",
                "chunk_index": 0,
            },
        )
        text, ended = menus.render_topic_detail(session)
        self.assertNotIn("Note: not yet reviewed.", text)
        self.assertIn("Short summary.", text)

    def test_transition_topic_detail_still_advances_chunks_for_review_required_topic(self):
        RightsTopic.objects.create(
            slug="long-unreviewed-topic",
            title="Long Unreviewed Topic",
            summary="Long summary sentence here. " * 20,
            verification_status="review_required",
        )
        session = UssdSession(
            state="topic_detail",
            language="en",
            context={
                "situation_slug": "s",
                "topic_slug": "long-unreviewed-topic",
                "chunk_index": 0,
            },
        )
        next_state, context = menus.transition_topic_detail(session, "1")
        self.assertEqual(next_state, "topic_detail")
        self.assertEqual(context["chunk_index"], 1)

    def test_render_safety_gate_shows_notice_for_review_required_topic(self):
        RightsTopic.objects.create(
            slug="unreviewed-safety-topic",
            title="Unreviewed Safety Topic",
            summary="Fallback summary.",
            risk_level="high_risk",
            verification_status="review_required",
        )
        session = UssdSession(
            state="safety_gate",
            language="en",
            context={
                "situation_slug": "s",
                "topic_slug": "unreviewed-safety-topic",
                "chunk_index": 0,
            },
        )
        text, ended = menus.render_safety_gate(session)
        self.assertIn("Note: not yet reviewed.", text)
        self.assertFalse(ended)

    def test_render_safety_gate_long_message_shares_first_chunk_with_notice(self):
        topic = RightsTopic.objects.create(
            slug="long-unreviewed-safety-topic",
            title="Long Unreviewed Safety Topic",
            summary="Fallback summary.",
            risk_level="high_risk",
            verification_status="review_required",
        )
        SafetyResponse.objects.create(
            rights_topic=topic,
            trigger_key="default",
            message="Call the emergency line immediately. " * 10,
        )
        session = UssdSession(
            state="safety_gate",
            language="en",
            context={
                "situation_slug": "s",
                "topic_slug": "long-unreviewed-safety-topic",
                "chunk_index": 0,
            },
        )
        text, ended = menus.render_safety_gate(session)
        # The notice and the safety message are now joined with a single
        # space rather than a blank-line paragraph break, so they flow
        # through word-wrapping as one continuous text stream. Even for
        # this very long (380-char) message, the notice and the start of
        # the real message share the first chunk.
        self.assertIn("Note: not yet reviewed.", text)
        self.assertIn("Call the emergency line", text)
        self.assertLessEqual(len(text), 182)
        self.assertFalse(ended)

        # The message is long enough that it still spans multiple chunks.
        session.context["chunk_index"] = 1
        text_chunk_1, _ = menus.render_safety_gate(session)
        self.assertIn("Call the emergency line", text_chunk_1)
        self.assertNotIn("Note: not yet reviewed.", text_chunk_1)

    def test_transition_safety_gate_stays_in_sync_with_render_for_review_required_topic(self):
        topic = RightsTopic.objects.create(
            slug="sync-check-topic",
            title="Sync Check Topic",
            summary="Fallback summary.",
            risk_level="high_risk",
            verification_status="review_required",
        )
        SafetyResponse.objects.create(
            rights_topic=topic,
            trigger_key="default",
            message="Call the emergency line immediately. " * 10,
        )
        session = UssdSession(
            state="safety_gate",
            language="en",
            context={
                "situation_slug": "s",
                "topic_slug": "sync-check-topic",
                "chunk_index": 0,
            },
        )
        next_state, context = menus.transition_safety_gate(session, "1")
        self.assertEqual(next_state, "safety_gate")
        self.assertEqual(context["chunk_index"], 1)

    def test_render_topic_detail_shares_first_chunk_with_realistic_length_summary(self):
        RightsTopic.objects.create(
            slug="realistic-length-topic",
            title="Realistic Length Topic",
            summary=(
                "Sauti Yo can help you understand the issue, review "
                "relevant rights information, and identify possible "
                "next steps."
            ),
            verification_status="review_required",
        )
        session = UssdSession(
            state="topic_detail",
            language="en",
            context={
                "situation_slug": "s",
                "topic_slug": "realistic-length-topic",
                "chunk_index": 0,
            },
        )
        text, ended = menus.render_topic_detail(session)
        self.assertIn("Note: not yet reviewed.", text)
        self.assertIn("Sauti Yo can help you understand the issue", text)

    def test_render_safety_gate_shows_notice_and_fallback_summary_together_when_no_safety_response(self):
        RightsTopic.objects.create(
            slug="no-response-realistic-topic",
            title="No Response Realistic Topic",
            summary=(
                "Sauti Yo can help you understand the issue, review "
                "relevant rights information, and identify possible "
                "next steps."
            ),
            risk_level="high_risk",
            verification_status="review_required",
        )
        session = UssdSession(
            state="safety_gate",
            language="en",
            context={
                "situation_slug": "s",
                "topic_slug": "no-response-realistic-topic",
                "chunk_index": 0,
            },
        )
        text, ended = menus.render_safety_gate(session)
        self.assertIn("Note: not yet reviewed.", text)
        self.assertIn("Sauti Yo can help you understand the issue", text)
