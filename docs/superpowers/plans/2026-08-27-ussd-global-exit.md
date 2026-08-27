# USSD Global Exit Option Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a USSD user press "0" to exit the session immediately from any screen, not just the main menu.

**Architecture:** `menus.transition_state` — the single function `handler.py` calls to advance state — intercepts `user_input == "0"` for any state except `"goodbye"` and routes straight to `("goodbye", {})`, before dispatching to the per-screen handler. Every screen's existing "Back" digit moves from "0" to "9" (unused everywhere today), and every screen's rendered text gains a trailing "0. Exit" line, baked into each screen's existing trailing-text/budget construction (not appended after the fact, since screen text is capped at a 160-char budget that's already reserved per screen before wrapping).

**Tech Stack:** Django 4.x test framework (`manage.py test`), plain Python — no new dependencies.

## Global Constraints

- Screen text budget: `SCREEN_BUDGET = 160` in `menus.py`; the AT screen-cap tests in `tests.py` assert `len(text) <= 182`. Neither cap changes.
- Back digit everywhere it currently appears: "0" → "9".
- New copy key `ussd.exit` = `"Exit"` (English), assembled at each call site as `f"0. {get_copy('ussd.exit', language)}"` — matches how `ussd.back`/`ussd.more`/`ussd.next` are already stored as bare labels, per the approved spec.
- `ussd.main_menu`, `ussd.topic_menu`, `ussd.safety_continue`, `ussd.continue` are stored as complete pre-formatted menu blocks; only their embedded back digit changes (`ussd.main_menu` needs no change — it already ends in "0. Exit").
- Test command: `python manage.py test apps.channels.ussd.tests --noinput` (run from `backend/`). Baseline: 106 tests, all passing.
- Full file under change: `backend/apps/channels/ussd/menus.py`. Tests: `backend/apps/channels/ussd/tests.py`. New data migration: `backend/apps/channels/migrations/`.

---

## Task 1: Central Exit dispatch + retire main menu's redundant Exit branch

**Files:**
- Modify: `backend/apps/channels/ussd/menus.py` (`transition_state` at the bottom of the file, `transition_main_menu` around line 152)
- Modify: `backend/apps/channels/ussd/tests.py` (`MainMenuTests.test_transition_exit_goes_to_goodbye` at line 261, `HandleUssdRequestTests` around line 897)

**Interfaces:**
- Consumes: nothing new — uses the existing `TRANSITION_HANDLERS` dict and `UssdSession`.
- Produces: `menus.transition_state(state, session, user_input)` now returns `("goodbye", {})` for `user_input == "0"` on any state other than `"goodbye"`, before ever calling the per-state handler. Later tasks (per-screen Back-digit changes) rely on this being in place first, since it's what makes each screen's own `"0"`-branch unreachable and safe to repurpose as `"9"`.

- [ ] **Step 1: Update/add the failing tests**

Replace `test_transition_exit_goes_to_goodbye` in `MainMenuTests` (it currently calls `transition_main_menu` directly with `"0"`; after this task that branch is removed, so the test must exercise the real dispatch path, `transition_state`):

```python
    def test_transition_exit_goes_to_goodbye(self):
        session = UssdSession(state="main_menu", language="en", context={})
        next_state, context = menus.transition_state("main_menu", session, "0")
        self.assertEqual(next_state, "goodbye")
        self.assertEqual(context, {})
```

Add a new test class after `GoodbyeTests` (around line 277), before the `SituationListTests` import block:

```python
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
```

These use `transition_state` directly, so they intentionally don't need any database fixtures — the exit intercept fires before any per-screen lookup happens.

Add one full-stack test to `HandleUssdRequestTests` (after `test_exit_ends_session`, around line 934), reusing that class's existing `self.situation`/`self.topic` fixtures:

```python
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
```

- [ ] **Step 2: Run tests to verify the new/changed ones fail**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: `GlobalExitTests` fails (situation_list/topic_detail/action_steps/language_select transitions don't yet special-case "0" centrally — situation_list and language_select currently return `None` or a different target for "0", so these assertions fail). `test_exit_from_mid_flow_ends_session` fails because "0" at `situation_list` currently means nothing (invalid) rather than ending the session. `test_transition_exit_goes_to_goodbye` still passes at this point (it's calling `transition_state`, whose default dispatch to `transition_main_menu` already handles "0" the old way) — that's fine, it'll stay green through this step.

- [ ] **Step 3: Implement the central dispatch and remove the redundant branch**

In `menus.py`, find:

```python
def transition_state(state, session, user_input):
    return TRANSITION_HANDLERS[state](session, user_input)
```

Replace with:

```python
def transition_state(state, session, user_input):
    if user_input == "0" and state != "goodbye":
        return "goodbye", {}
    return TRANSITION_HANDLERS[state](session, user_input)
```

Find `transition_main_menu`:

```python
def transition_main_menu(session, user_input):
    if user_input == "1":
        return "situation_list", {"page": 0}
    if user_input == "2":
        return "emergency_list", {"chunk_index": 0}
    if user_input == "0":
        return "goodbye", {}
    return None
```

Remove the now-unreachable branch:

```python
def transition_main_menu(session, user_input):
    if user_input == "1":
        return "situation_list", {"page": 0}
    if user_input == "2":
        return "emergency_list", {"chunk_index": 0}
    return None
```

- [ ] **Step 4: Run tests to verify everything passes**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: all tests pass, including `GlobalExitTests`, `test_exit_from_mid_flow_ends_session`, and the updated `test_transition_exit_goes_to_goodbye`.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/ussd/menus.py backend/apps/channels/ussd/tests.py
git commit -m "feat: intercept '0' as a global USSD exit before per-screen dispatch"
```

---

## Task 2: Shared chunked-screen infra + copy updates

**Files:**
- Modify: `backend/apps/channels/ussd/menus.py` (`DEFAULT_COPY` at the top, `_chunked_screen` around line 191)
- Modify: `backend/apps/channels/ussd/tests.py` (`GetCopyTests`, new `ChunkedScreenTests` class)

**Interfaces:**
- Consumes: `get_copy(content_key, language)` (existing).
- Produces: `DEFAULT_COPY["ussd.exit"] == "Exit"`; `DEFAULT_COPY["ussd.topic_menu"]`/`["ussd.safety_continue"]`/`["ussd.continue"]` now end in `"9. Back"` instead of `"0. Back"`. `_chunked_screen(text, chunk_index, trailing_options, language)` — same signature, but every screen it renders (final chunk or not) now includes a "0. Exit" line, and its internal "More"/"Back" pagination footer uses "9. Back". This is consumed by Tasks 3–7 (`situation_detail`, `topic_detail`, `safety_gate`, `action_steps`, `support_contacts`, `emergency_list` all call it).

- [ ] **Step 1: Write the failing tests**

Add a new test class to `tests.py`, right after `TextHelperTests` (before `GetCopyTests`, around line 122):

```python
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
```

Add to `GetCopyTests` (after `test_ignores_inactive_channel_content_row`, around line 154):

```python
    def test_exit_copy_defaults_to_exit_label(self):
        self.assertEqual(menus.get_copy("ussd.exit", "en"), "Exit")

    def test_topic_menu_copy_uses_nine_for_back(self):
        self.assertIn("9. Back", menus.get_copy("ussd.topic_menu", "en"))

    def test_continue_copy_uses_nine_for_back(self):
        self.assertIn("9. Back", menus.get_copy("ussd.continue", "en"))

    def test_safety_continue_copy_uses_nine_for_back(self):
        self.assertIn("9. Back", menus.get_copy("ussd.safety_continue", "en"))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: FAIL — `ussd.exit` isn't in `DEFAULT_COPY` yet, and `topic_menu`/`continue`/`safety_continue` still say "0. Back"; `_chunked_screen` doesn't append an exit line yet.

- [ ] **Step 3: Implement the copy and `_chunked_screen` changes**

In `DEFAULT_COPY`, keep the existing key order; change the three back-digit values and add the new `ussd.exit` key. The block from `ussd.topic_menu` through `ussd.unreviewed_notice` becomes:

```python
    "ussd.topic_menu": "1. Action steps\n2. Support contacts\n9. Back",
    "ussd.invalid_choice": "Invalid choice.",
    "ussd.too_many_invalid": (
        "Too many invalid attempts. Please dial again."
    ),
    "ussd.goodbye": "Thank you for using Sauti Yo.",
    "ussd.not_found": (
        "Sorry, that information is no longer available."
    ),
    "ussd.no_situations": "No situations are available right now.",
    "ussd.choose_situation": "Choose a situation:",
    "ussd.related_rights": "Related rights:",
    "ussd.safety_continue": "1. Continue\n9. Back",
    "ussd.continue": "1. Continue\n9. Back",
    "ussd.no_action_steps": (
        "No action steps are available for this topic."
    ),
    "ussd.no_support_contacts": "No support contacts are available.",
    "ussd.no_emergency_contacts": (
        "No emergency contacts are available right now."
    ),
    "ussd.more": "More",
    "ussd.back": "Back",
    "ussd.next": "Next",
    "ussd.exit": "Exit",
    "ussd.unreviewed_notice": "Note: not yet reviewed.",
```

(`ussd.main_menu` and everything before `ussd.topic_menu` stays unchanged.)

Now find `_chunked_screen`:

```python
def _chunked_screen(text, chunk_index, trailing_options, language):
    more = get_copy("ussd.more", language)
    back = get_copy("ussd.back", language)
    more_back = f"1. {more}\n0. {back}"
    reserved = max(len(trailing_options), len(more_back))
    body_budget = max(SCREEN_BUDGET - reserved - 2, 20)

    chunks = chunk_text(text, budget=body_budget) if text else [""]
    chunk_index = max(0, min(chunk_index, len(chunks) - 1))
    body = chunks[chunk_index]
    is_last = chunk_index == len(chunks) - 1
    if is_last:
        screen = f"{body}\n\n{trailing_options}" if trailing_options else body
    else:
        screen = f"{body}\n\n{more_back}"
    return screen, is_last
```

Replace with:

```python
def _chunked_screen(text, chunk_index, trailing_options, language):
    more = get_copy("ussd.more", language)
    back = get_copy("ussd.back", language)
    exit_line = f"0. {get_copy('ussd.exit', language)}"
    more_back = f"1. {more}\n9. {back}\n{exit_line}"
    final_trailing = (
        f"{trailing_options}\n{exit_line}" if trailing_options else exit_line
    )
    reserved = max(len(final_trailing), len(more_back))
    body_budget = max(SCREEN_BUDGET - reserved - 2, 20)

    chunks = chunk_text(text, budget=body_budget) if text else [""]
    chunk_index = max(0, min(chunk_index, len(chunks) - 1))
    body = chunks[chunk_index]
    is_last = chunk_index == len(chunks) - 1
    if is_last:
        screen = f"{body}\n\n{final_trailing}"
    else:
        screen = f"{body}\n\n{more_back}"
    return screen, is_last
```

Note `trailing_options` passed in by callers still needs to say "9. Back" for the digit to be accurate — that's what Tasks 3–7 fix at each call site (situation_detail's hand-built fallback, action_steps', support_contacts', emergency_list's). `topic_menu`/`safety_continue`/`continue` are already correct as of this task's `DEFAULT_COPY` change.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: `ChunkedScreenTests` and the new `GetCopyTests` pass. Some *other* existing tests will now start failing (e.g. `TopicDetailTests.test_render_last_chunk_shows_topic_menu`'s screen now contains "9. Back"/"0. Exit" where callers still build fallback trailing text with "0."), which is expected — Tasks 3–7 fix those call sites and their tests. Confirm at minimum that `ChunkedScreenTests` and the four new `GetCopyTests` methods pass; a full green suite isn't expected until Task 8 completes.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/ussd/menus.py backend/apps/channels/ussd/tests.py
git commit -m "feat: bake a global Exit option and Back-on-9 into the shared USSD screen budget"
```

---

## Task 3: situation_detail (including the topics-stage sub-screen)

**Files:**
- Modify: `backend/apps/channels/ussd/menus.py` (`render_situation_detail`, `transition_situation_detail`, `_situation_topics_page`, `_render_situation_topics`, `_transition_situation_topics` — lines 283–397)
- Modify: `backend/apps/channels/ussd/tests.py` (`SituationDetailTests`, lines 377–636)

**Interfaces:**
- Consumes: `_chunked_screen` from Task 2.
- Produces: no new public interface; `transition_situation_detail`'s Back digit is now `"9"` in both the not-is_last and is_last cases; `_transition_situation_topics`'s Back digit is now `"9"`.

- [ ] **Step 1: Update the failing tests**

In `SituationDetailTests`, change `test_transition_back_returns_to_situation_list` (line 468):

```python
    def test_transition_back_returns_to_situation_list(self):
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "chunk_index": 9999},
        )
        next_state, context = menus.transition_situation_detail(session, "9")
        self.assertEqual(next_state, "situation_list")
        self.assertEqual(context, {"page": 0})
```

Add a new test right after it:

```python
    def test_transition_back_returns_to_situation_list_before_last_chunk(self):
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "chunk_index": 0},
        )
        next_state, context = menus.transition_situation_detail(session, "9")
        self.assertEqual(next_state, "situation_list")
        self.assertEqual(context, {"page": 0})
```

Update the docstring/comment in `test_description_with_many_linked_topics_does_not_fragment` (line 566-568) to match the new wording:

```python
        # The description body chunk (everything before the blank-line separator
        # and the short "1. Continue\n9. Back\n0. Exit" trailing) should be a
        # substantial fraction of the screen budget, not a ~16-character fragment.
```

Update `test_token_longer_than_body_budget_is_split_and_stays_within_cap` (lines 598–623) — its docstring and assertion both reference the old digit:

```python
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
```

Extend `test_render_topics_stage_lists_topics` (line 417) to also check the new options:

```python
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
```

Add a new test for the topics-stage Back digit, after `test_transition_selects_topic_in_topics_stage` (line 458):

```python
    def test_transition_topics_stage_back_returns_to_situation_list(self):
        session = UssdSession(
            state="situation_detail",
            language="en",
            context={"situation_slug": "eviction", "stage": "topics", "page": 0},
        )
        next_state, context = menus.transition_situation_detail(session, "9")
        self.assertEqual(next_state, "situation_list")
        self.assertEqual(context, {"page": 0})
```

Add a test covering the no-topics fallback trailing text, at the end of the class (after `test_back_from_topic_with_single_topic_returns_to_situation_list`, line 631-635):

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: FAIL on all the tests changed/added above — the code still uses "0" for Back and doesn't add an exit line to the topics-stage list or the no-topics fallback.

- [ ] **Step 3: Implement**

In `render_situation_detail`, change:

```python
    back = get_copy("ussd.back", session.language)
    trailing = get_copy("ussd.continue", session.language) if topics else f"0. {back}"
```

to:

```python
    back = get_copy("ussd.back", session.language)
    trailing = get_copy("ussd.continue", session.language) if topics else f"9. {back}"
```

In `transition_situation_detail`, apply the same `f"0. {back}"` → `f"9. {back}"` change, then change both Back-digit checks:

```python
    if not is_last:
        if user_input == "1":
            return (
                "situation_detail",
                {**session.context, "chunk_index": chunk_index + 1},
            )
        if user_input == "9":
            return "situation_list", {"page": 0}
        return None

    if user_input == "9":
        return "situation_list", {"page": 0}
    if topics and user_input == "1":
        return (
            "situation_detail",
            {
                "situation_slug": situation.slug,
                "stage": "topics",
                "page": 0,
            },
        )
    return None
```

In `_situation_topics_page`, change:

```python
def _situation_topics_page(session, topics):
    start_index = session.context.get("page", 0)
    back = get_copy("ussd.back", session.language)
    header = get_copy("ussd.related_rights", session.language)
    more_label = get_copy("ussd.more", session.language)

    reserved = len(header) + 1 + len(f"8. {more_label}") + 1 + len(f"0. {back}") + 2
    budget = max(SCREEN_BUDGET - reserved, 20)
```

to:

```python
def _situation_topics_page(session, topics):
    start_index = session.context.get("page", 0)
    back = get_copy("ussd.back", session.language)
    header = get_copy("ussd.related_rights", session.language)
    more_label = get_copy("ussd.more", session.language)
    exit_label = get_copy("ussd.exit", session.language)

    reserved = (
        len(header) + 1
        + len(f"8. {more_label}") + 1
        + len(f"9. {back}") + 1
        + len(f"0. {exit_label}") + 2
    )
    budget = max(SCREEN_BUDGET - reserved, 20)
```

In `_render_situation_topics`, change:

```python
    screen_lines = [header] + lines
    if has_more:
        screen_lines.append(f"8. {more_label}")
    screen_lines.append(f"0. {back}")
    return "\n".join(screen_lines), False
```

to:

```python
    screen_lines = [header] + lines
    if has_more:
        screen_lines.append(f"8. {more_label}")
    screen_lines.append(f"9. {back}")
    screen_lines.append(f"0. {get_copy('ussd.exit', session.language)}")
    return "\n".join(screen_lines), False
```

In `_transition_situation_topics`, change:

```python
    if user_input == "0":
        return "situation_list", {"page": 0}
```

to:

```python
    if user_input == "9":
        return "situation_list", {"page": 0}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: all `SituationDetailTests` pass.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/ussd/menus.py backend/apps/channels/ussd/tests.py
git commit -m "feat: move situation_detail Back to 9 and show Exit on every situation screen"
```

---

## Task 4: topic_detail

**Files:**
- Modify: `backend/apps/channels/ussd/menus.py` (`transition_topic_detail`, lines 445–489)
- Modify: `backend/apps/channels/ussd/tests.py` (`TopicDetailTests`, lines 641–691)

**Interfaces:**
- Consumes: `_chunked_screen` (Task 2) and `DEFAULT_COPY["ussd.topic_menu"]` (Task 2) — no render-code change needed in this task, since Task 2 already fixed the copy string and `_chunked_screen` already appends the exit line.
- Produces: `transition_topic_detail`'s Back digit is now `"9"`.

- [ ] **Step 1: Update the failing tests**

Change `test_transition_back_with_no_situation_returns_situation_list` (line 682):

```python
    def test_transition_back_with_no_situation_returns_situation_list(self):
        next_state, context = menus.transition_topic_detail(
            self._session(9999), "9"
        )
        self.assertEqual(next_state, "situation_list")
```

Add a new test right after it, covering the not-is_last Back branch (not currently exercised):

```python
    def test_transition_back_before_last_chunk_returns_situation_list(self):
        next_state, context = menus.transition_topic_detail(
            self._session(0), "9"
        )
        self.assertEqual(next_state, "situation_list")
```

Extend `test_render_last_chunk_shows_topic_menu` (line 663) to check the new options:

```python
    def test_render_last_chunk_shows_topic_menu(self):
        text, ended = menus.render_topic_detail(self._session(9999))
        self.assertIn("1. Action steps", text)
        self.assertIn("2. Support contacts", text)
        self.assertIn("9. Back", text)
        self.assertIn("0. Exit", text)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: FAIL — `transition_topic_detail` still only recognizes "0" for Back.

- [ ] **Step 3: Implement**

In `transition_topic_detail`, change both occurrences:

```python
    if not is_last:
        if user_input == "1":
            return (
                "topic_detail",
                {**session.context, "chunk_index": chunk_index + 1},
            )
        if user_input == "9":
            return _back_from_topic(situation_slug, topic_slug)
        return None

    if user_input == "1":
        return (
            "action_steps",
            {
                "situation_slug": situation_slug,
                "topic_slug": topic_slug,
                "step_index": 0,
                "chunk_index": 0,
            },
        )
    if user_input == "2":
        return (
            "support_contacts",
            {
                "situation_slug": situation_slug,
                "topic_slug": topic_slug,
                "chunk_index": 0,
            },
        )
    if user_input == "9":
        return _back_from_topic(situation_slug, topic_slug)
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: all `TopicDetailTests` pass.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/ussd/menus.py backend/apps/channels/ussd/tests.py
git commit -m "feat: move topic_detail Back to 9"
```

---

## Task 5: safety_gate

**Files:**
- Modify: `backend/apps/channels/ussd/menus.py` (`transition_safety_gate`, lines 510–547)
- Modify: `backend/apps/channels/ussd/tests.py` (`SafetyGateTests`, lines 694–755)

**Interfaces:**
- Consumes: `_chunked_screen` (Task 2) and `DEFAULT_COPY["ussd.safety_continue"]` (Task 2) — no render-code change needed.
- Produces: `transition_safety_gate`'s Back digit is now `"9"`.

- [ ] **Step 1: Update the failing tests**

Change `test_transition_rejects_invalid_choice_on_last_chunk` (line 732) — its probe digit, "9", is about to become a *valid* input, so it needs to test with a value that's still genuinely invalid:

```python
    def test_transition_rejects_invalid_choice_on_last_chunk(self):
        self.assertIsNone(menus.transition_safety_gate(self._session(9999), "5"))
```

Add two new tests after it, covering the (previously untested) Back digit in both chunk positions:

```python
    def test_transition_back_on_last_chunk_returns_via_back_from_topic(self):
        next_state, context = menus.transition_safety_gate(self._session(9999), "9")
        self.assertEqual(next_state, "situation_list")
        self.assertEqual(context, {"page": 0})

    def test_transition_back_before_last_chunk_returns_via_back_from_topic(self):
        next_state, context = menus.transition_safety_gate(self._session(0), "9")
        self.assertEqual(next_state, "situation_list")
        self.assertEqual(context, {"page": 0})
```

(Both resolve to `situation_list` because `SafetyGateTests.setUp` never creates a `Situation` row for `"eviction"`, so `_back_from_topic` takes its "situation not found" branch — matching the existing pattern already used by `TopicDetailTests`.)

Extend `test_render_last_chunk_does_not_end_session` (line 735) to also check the new options:

```python
    def test_render_last_chunk_does_not_end_session(self):
        text, ended = menus.render_safety_gate(self._session(9999))
        self.assertIn("1. Continue", text)
        self.assertIn("9. Back", text)
        self.assertIn("0. Exit", text)
        self.assertFalse(ended)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: FAIL — `"9"` isn't yet a valid Back input in `transition_safety_gate`, so the new Back tests get `None` instead of `"situation_list"`; the old invalid-choice test at digit `"9"` would now pass for the wrong reason (it's mid-fix), which is exactly why the probe was moved to `"5"`.

- [ ] **Step 3: Implement**

In `transition_safety_gate`, change both occurrences:

```python
    if not is_last:
        if user_input == "1":
            return (
                "safety_gate",
                {**session.context, "chunk_index": chunk_index + 1},
            )
        if user_input == "9":
            return _back_from_topic(situation_slug, topic_slug)
        return None

    if user_input == "1":
        return (
            "topic_detail",
            {
                "situation_slug": situation_slug,
                "topic_slug": topic_slug,
                "chunk_index": 0,
            },
        )
    if user_input == "9":
        return _back_from_topic(situation_slug, topic_slug)
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: all `SafetyGateTests` pass.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/ussd/menus.py backend/apps/channels/ussd/tests.py
git commit -m "feat: move safety_gate Back to 9"
```

---

## Task 6: action_steps

**Files:**
- Modify: `backend/apps/channels/ussd/menus.py` (`render_action_steps`, `transition_action_steps`, lines 550–631)
- Modify: `backend/apps/channels/ussd/tests.py` (`ActionStepsTests`, lines 757–812)

**Interfaces:**
- Consumes: `_chunked_screen` (Task 2).
- Produces: no new public interface; Back digit is `"9"`; the no-steps fallback screen (which bypasses `_chunked_screen` via an early return) now shows both "9. Back" and "0. Exit" explicitly.

- [ ] **Step 1: Update the failing tests**

Change `test_transition_back_returns_to_topic_detail` (line 804):

```python
    def test_transition_back_returns_to_topic_detail(self):
        next_state, context = menus.transition_action_steps(self._session(), "9")
        self.assertEqual(next_state, "topic_detail")
        self.assertEqual(context["chunk_index"], 9999)
```

Extend `test_render_with_no_steps_shows_empty_message` (line 809) and add a matching transition test after it:

```python
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
```

Extend `test_render_shows_first_step_with_next_option` (line 787) to check the exit line:

```python
    def test_render_shows_first_step_with_next_option(self):
        text, ended = menus.render_action_steps(self._session())
        self.assertIn("Step 1/2", text)
        self.assertIn("1.", text)
        self.assertIn("0. Exit", text)
        self.assertFalse(ended)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: FAIL — Back digit is still "0", and the no-steps fallback doesn't show an exit line.

- [ ] **Step 3: Implement**

In `render_action_steps`, change:

```python
    back_label = get_copy("ussd.back", session.language)
    if not steps:
        body = get_copy("ussd.no_action_steps", session.language)
        return f"{body}\n\n0. {back_label}", False
```

to:

```python
    back_label = get_copy("ussd.back", session.language)
    if not steps:
        body = get_copy("ussd.no_action_steps", session.language)
        exit_label = get_copy("ussd.exit", session.language)
        return f"{body}\n\n9. {back_label}\n0. {exit_label}", False
```

Further down in the same function, change:

```python
    has_next = step_index + 1 < len(steps)
    if has_next:
        next_label = get_copy("ussd.next", session.language)
        trailing = f"1. {next_label}\n0. {back_label}"
    else:
        trailing = f"0. {back_label}"
```

to:

```python
    has_next = step_index + 1 < len(steps)
    if has_next:
        next_label = get_copy("ussd.next", session.language)
        trailing = f"1. {next_label}\n9. {back_label}"
    else:
        trailing = f"9. {back_label}"
```

In `transition_action_steps`, change the no-steps branch:

```python
    if not steps:
        if user_input == "0":
            return _back_to_topic_detail(situation_slug, topic_slug)
        return None
```

to:

```python
    if not steps:
        if user_input == "9":
            return _back_to_topic_detail(situation_slug, topic_slug)
        return None
```

Change the trailing-text construction (mirroring the render function):

```python
    if has_next:
        next_label = get_copy("ussd.next", session.language)
        trailing = f"1. {next_label}\n9. {back_label}"
    else:
        trailing = f"9. {back_label}"
```

Change both remaining Back checks:

```python
    if not is_last:
        if user_input == "1":
            return (
                "action_steps",
                {**session.context, "chunk_index": chunk_index + 1},
            )
        if user_input == "9":
            return _back_to_topic_detail(situation_slug, topic_slug)
        return None

    if has_next and user_input == "1":
        return (
            "action_steps",
            {
                "situation_slug": situation_slug,
                "topic_slug": topic_slug,
                "step_index": step_index + 1,
                "chunk_index": 0,
            },
        )
    if user_input == "9":
        return _back_to_topic_detail(situation_slug, topic_slug)
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: all `ActionStepsTests` pass.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/ussd/menus.py backend/apps/channels/ussd/tests.py
git commit -m "feat: move action_steps Back to 9 and show Exit on the no-steps screen"
```

---

## Task 7: support_contacts & emergency_list

**Files:**
- Modify: `backend/apps/channels/ussd/menus.py` (`render_support_contacts`, `transition_support_contacts`, `render_emergency_list`, `transition_emergency_list`, lines 645–748)
- Modify: `backend/apps/channels/ussd/tests.py` (`SupportContactsTests` lines 818–860, `EmergencyListTests` lines 862–894)

**Interfaces:**
- Consumes: `_chunked_screen` (Task 2).
- Produces: no new public interface; Back digit is `"9"` for both screens; their no-items fallback screens (early returns that bypass `_chunked_screen`) now show "9. Back" and "0. Exit" explicitly.

- [ ] **Step 1: Update the failing tests**

In `SupportContactsTests`, change `test_transition_back_returns_to_topic_detail` (line 850):

```python
    def test_transition_back_returns_to_topic_detail(self):
        next_state, context = menus.transition_support_contacts(
            self._session(), "9"
        )
        self.assertEqual(next_state, "topic_detail")
        self.assertEqual(context["chunk_index"], 9999)
```

Extend `test_render_with_no_contacts_shows_empty_message` (line 845) and add a matching transition test:

```python
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
```

In `EmergencyListTests`, change `test_transition_back_returns_to_main_menu` (line 883):

```python
    def test_transition_back_returns_to_main_menu(self):
        next_state, context = menus.transition_emergency_list(self._session(), "9")
        self.assertEqual(next_state, "main_menu")
```

Extend `test_render_with_no_emergency_contacts_shows_empty_message` (line 887) and add a matching transition test:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: FAIL — both screens still use "0" for Back and don't show an exit line on the no-items fallback.

- [ ] **Step 3: Implement**

In `render_support_contacts`, change:

```python
    services = list(topic.support_services.filter(is_active=True).order_by("name"))
    chunk_index = session.context.get("chunk_index", 0)
    back = f"0. {get_copy('ussd.back', session.language)}"

    if not services:
        body = get_copy("ussd.no_support_contacts", session.language)
        return f"{body}\n\n{back}", False
```

to:

```python
    services = list(topic.support_services.filter(is_active=True).order_by("name"))
    chunk_index = session.context.get("chunk_index", 0)
    back = f"9. {get_copy('ussd.back', session.language)}"

    if not services:
        body = get_copy("ussd.no_support_contacts", session.language)
        exit_label = get_copy("ussd.exit", session.language)
        return f"{body}\n\n{back}\n0. {exit_label}", False
```

In `transition_support_contacts`, change all three occurrences (no-services branch, `back` assignment, not-is_last branch, is_last branch):

```python
def transition_support_contacts(session, user_input):
    situation_slug = session.context.get("situation_slug")
    topic_slug = session.context.get("topic_slug")
    topic = RightsTopic.objects.filter(slug=topic_slug, is_active=True).first()
    if topic is None:
        return "situation_list", {"page": 0}

    services = list(topic.support_services.filter(is_active=True).order_by("name"))
    if not services:
        if user_input == "9":
            return _back_to_topic_detail(situation_slug, topic_slug)
        return None

    chunk_index = session.context.get("chunk_index", 0)
    back = f"9. {get_copy('ussd.back', session.language)}"
    _, is_last = _chunked_screen(
        _format_contacts(services), chunk_index, back, session.language
    )

    if not is_last:
        if user_input == "1":
            return (
                "support_contacts",
                {**session.context, "chunk_index": chunk_index + 1},
            )
        if user_input == "9":
            return _back_to_topic_detail(situation_slug, topic_slug)
        return None

    if user_input == "9":
        return _back_to_topic_detail(situation_slug, topic_slug)
    return None
```

In `render_emergency_list`, apply the equivalent change:

```python
    services = list(
        SupportService.objects.filter(
            is_emergency_service=True, is_active=True
        ).order_by("name")
    )
    chunk_index = session.context.get("chunk_index", 0)
    back = f"9. {get_copy('ussd.back', session.language)}"

    if not services:
        body = get_copy("ussd.no_emergency_contacts", session.language)
        exit_label = get_copy("ussd.exit", session.language)
        return f"{body}\n\n{back}\n0. {exit_label}", False
```

In `transition_emergency_list`, apply the equivalent change:

```python
def transition_emergency_list(session, user_input):
    services = list(
        SupportService.objects.filter(
            is_emergency_service=True, is_active=True
        ).order_by("name")
    )
    if not services:
        if user_input == "9":
            return "main_menu", {}
        return None

    chunk_index = session.context.get("chunk_index", 0)
    back = f"9. {get_copy('ussd.back', session.language)}"
    _, is_last = _chunked_screen(
        _format_contacts(services), chunk_index, back, session.language
    )

    if not is_last:
        if user_input == "1":
            return (
                "emergency_list",
                {**session.context, "chunk_index": chunk_index + 1},
            )
        if user_input == "9":
            return "main_menu", {}
        return None

    if user_input == "9":
        return "main_menu", {}
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: all `SupportContactsTests` and `EmergencyListTests` pass.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/ussd/menus.py backend/apps/channels/ussd/tests.py
git commit -m "feat: move support_contacts and emergency_list Back to 9"
```

---

## Task 8: situation_list

**Files:**
- Modify: `backend/apps/channels/ussd/menus.py` (`_situation_list_page`, `render_situation_list`, `transition_situation_list`, lines 224–280)
- Modify: `backend/apps/channels/ussd/tests.py` (`SituationListTests`, lines 282–374)

**Interfaces:**
- Consumes: nothing new.
- Produces: no new public interface; Back digit is `"9"`; the list screen and its no-situations fallback both show "0. Exit".

- [ ] **Step 1: Update the failing tests**

Change `test_transition_back_to_main_menu` (line 363):

```python
    def test_transition_back_to_main_menu(self):
        session = UssdSession(
            state="situation_list", language="en", context={"page": 0}
        )
        next_state, context = menus.transition_situation_list(session, "9")
        self.assertEqual(next_state, "main_menu")
```

Change `test_transition_rejects_invalid_choice` (line 370) — its probe digit, "9", is about to become valid, so use an out-of-range value instead:

```python
    def test_transition_rejects_invalid_choice(self):
        session = UssdSession(
            state="situation_list", language="en", context={"page": 0}
        )
        self.assertIsNone(menus.transition_situation_list(session, "20"))
```

Extend `test_render_with_no_situations_shows_empty_message` (line 317):

```python
    def test_render_with_no_situations_shows_empty_message(self):
        Situation.objects.all().delete()
        session = UssdSession(
            state="situation_list", language="en", context={"page": 0}
        )
        text, ended = menus.render_situation_list(session)
        self.assertIn("No situations", text)
        self.assertIn("9. Back", text)
        self.assertIn("0. Exit", text)
```

Add a new test after `test_render_first_page_shows_more_option_when_not_all_fit` (line 300):

```python
    def test_render_shows_exit_and_back_options(self):
        session = UssdSession(
            state="situation_list", language="en", context={"page": 0}
        )
        text, ended = menus.render_situation_list(session)
        self.assertIn("9. Back", text)
        self.assertIn("0. Exit", text)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: FAIL — Back digit is still "0" and no exit line is shown.

- [ ] **Step 3: Implement**

In `_situation_list_page`, change:

```python
def _situation_list_page(session):
    situations = list(Situation.objects.filter(is_active=True).order_by("title"))
    start_index = session.context.get("page", 0)
    back = get_copy("ussd.back", session.language)
    header = get_copy("ussd.choose_situation", session.language)
    more_label = get_copy("ussd.more", session.language)

    reserved = len(header) + 1 + len(f"8. {more_label}") + 1 + len(f"0. {back}") + 2
    budget = max(SCREEN_BUDGET - reserved, 20)
```

to:

```python
def _situation_list_page(session):
    situations = list(Situation.objects.filter(is_active=True).order_by("title"))
    start_index = session.context.get("page", 0)
    back = get_copy("ussd.back", session.language)
    header = get_copy("ussd.choose_situation", session.language)
    more_label = get_copy("ussd.more", session.language)
    exit_label = get_copy("ussd.exit", session.language)

    reserved = (
        len(header) + 1
        + len(f"8. {more_label}") + 1
        + len(f"9. {back}") + 1
        + len(f"0. {exit_label}") + 2
    )
    budget = max(SCREEN_BUDGET - reserved, 20)
```

In `render_situation_list`, change:

```python
def render_situation_list(session):
    situations, header, lines, shown, next_index, has_more, back, more_label = (
        _situation_list_page(session)
    )

    if not situations:
        body = get_copy("ussd.no_situations", session.language)
        return f"{body}\n\n0. {back}", False

    screen_lines = [header] + lines
    if has_more:
        screen_lines.append(f"8. {more_label}")
    screen_lines.append(f"0. {back}")
    return "\n".join(screen_lines), False
```

to:

```python
def render_situation_list(session):
    situations, header, lines, shown, next_index, has_more, back, more_label = (
        _situation_list_page(session)
    )
    exit_label = get_copy("ussd.exit", session.language)

    if not situations:
        body = get_copy("ussd.no_situations", session.language)
        return f"{body}\n\n9. {back}\n0. {exit_label}", False

    screen_lines = [header] + lines
    if has_more:
        screen_lines.append(f"8. {more_label}")
    screen_lines.append(f"9. {back}")
    screen_lines.append(f"0. {exit_label}")
    return "\n".join(screen_lines), False
```

In `transition_situation_list`, change:

```python
    if user_input == "0":
        return "main_menu", {}
```

to:

```python
    if user_input == "9":
        return "main_menu", {}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: all `SituationListTests` pass, and the *entire* `apps.channels.ussd.tests` module should now be green (Tasks 3–7 already fixed the other screens).

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/ussd/menus.py backend/apps/channels/ussd/tests.py
git commit -m "feat: move situation_list Back to 9 and show Exit on every list screen"
```

---

## Task 9: language_select

**Files:**
- Modify: `backend/apps/channels/ussd/menus.py` (`render_language_select`, lines 120–127)
- Modify: `backend/apps/channels/ussd/tests.py` (`LanguageSelectTests`, lines 157–239)

**Interfaces:**
- Consumes: nothing new.
- Produces: `render_language_select` now includes a trailing "0. Exit" line on both its normal and unavailable-notice paths. No transition change — `transition_language_select` already returns `None` for "0" (its mapping only covers "1"–"4"), and `transition_state`'s central intercept (Task 1) handles "0" before this function is ever called with it.

- [ ] **Step 1: Update the failing tests**

Extend `test_render_shows_welcome_and_language_options` (line 158):

```python
    def test_render_shows_welcome_and_language_options(self):
        session = UssdSession(state="language_select", language="", context={})
        text, ended = menus.render_language_select(session)
        self.assertIn("Welcome to Sauti Yo", text)
        self.assertIn("1. English", text)
        self.assertIn("0. Exit", text)
        self.assertFalse(ended)
```

Extend `test_render_shows_unavailable_notice_when_flagged` (line 165):

```python
    def test_render_shows_unavailable_notice_when_flagged(self):
        session = UssdSession(
            state="language_select",
            language="",
            context={"unavailable_notice": True},
        )
        text, ended = menus.render_language_select(session)
        self.assertIn("not available yet", text)
        self.assertIn("1. English", text)
        self.assertIn("0. Exit", text)
        self.assertFalse(ended)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: FAIL — neither branch currently includes "0. Exit".

- [ ] **Step 3: Implement**

In `render_language_select`, change:

```python
def render_language_select(session):
    body = get_copy("ussd.welcome", session.language)
    prompt = get_copy("ussd.language_prompt", session.language)
    if session.context.get("unavailable_notice"):
        requested = session.context.get("requested_language", session.language)
        notice = get_copy("ussd.language_unavailable", requested)
        return f"{notice}\n\n{body}\n{prompt}", False
    return f"{body}\n{prompt}", False
```

to:

```python
def render_language_select(session):
    body = get_copy("ussd.welcome", session.language)
    prompt = get_copy("ussd.language_prompt", session.language)
    exit_line = f"0. {get_copy('ussd.exit', session.language)}"
    if session.context.get("unavailable_notice"):
        requested = session.context.get("requested_language", session.language)
        notice = get_copy("ussd.language_unavailable", requested)
        return f"{notice}\n\n{body}\n{prompt}\n{exit_line}", False
    return f"{body}\n{prompt}\n{exit_line}", False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: all `LanguageSelectTests` pass.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/ussd/menus.py backend/apps/channels/ussd/tests.py
git commit -m "feat: show Exit option on the USSD language-select screen"
```

---

## Task 10: Data migration for lg/sw/nyn seeded copy

**Files:**
- Create: `backend/apps/channels/migrations/0013_update_ussd_back_and_exit_copy.py`
- Modify: `backend/apps/channels/ussd/tests.py` (new `SeededTranslationCopyTests` class)

**Interfaces:**
- Consumes: `ChannelContent` model (via `apps.get_model`, standard Django data-migration pattern already used in `0007_seed_multilingual_ussd_copy.py`).
- Produces: for `language in ("lg", "sw", "nyn")`, `ChannelContent` rows for `ussd.topic_menu`/`ussd.safety_continue`/`ussd.continue` have their embedded back digit updated from "0." to "9.", and a new `ussd.exit` row is created per language.

- [ ] **Step 1: Write the failing tests**

Add to `tests.py`, after `UssdCallbackViewTests` (around line 1158, before `UnreviewedNoticeTests`):

```python
class SeededTranslationCopyTests(TestCase):
    def test_luganda_topic_menu_uses_nine_for_back(self):
        self.assertIn("9. Ddayo", menus.get_copy("ussd.topic_menu", "lg"))

    def test_luganda_exit_copy_is_seeded(self):
        self.assertEqual(menus.get_copy("ussd.exit", "lg"), "Fuluma")

    def test_kiswahili_continue_uses_nine_for_back(self):
        self.assertIn("9. Rudi", menus.get_copy("ussd.continue", "sw"))

    def test_kiswahili_exit_copy_is_seeded(self):
        self.assertEqual(menus.get_copy("ussd.exit", "sw"), "Toka")

    def test_runyankole_safety_continue_uses_nine_for_back(self):
        self.assertIn("9. Garuka", menus.get_copy("ussd.safety_continue", "nyn"))

    def test_runyankole_exit_copy_is_seeded(self):
        self.assertEqual(menus.get_copy("ussd.exit", "nyn"), "Rugamu")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: FAIL — the seeded rows from migration `0007` still say "0. Ddayo"/"0. Rudi"/"0. Garuka", and no `ussd.exit` row exists for any of the three languages, so `get_copy` falls back to `DEFAULT_COPY["ussd.exit"]` ("Exit") instead of the language-specific label.

- [ ] **Step 3: Write the migration**

```python
from django.db import migrations


UPDATED_BACK_COPY = {
    "lg": {
        "ussd.topic_menu": (
            "1. Emitendera gy'okukola\n"
            "2. Enkola z'obuyambi\n"
            "9. Ddayo"
        ),
        "ussd.safety_continue": "1. Weyongereyo\n9. Ddayo",
        "ussd.continue": "1. Weyongereyo\n9. Ddayo",
    },
    "sw": {
        "ussd.topic_menu": (
            "1. Hatua za kuchukua\n"
            "2. Mawasiliano ya msaada\n"
            "9. Rudi"
        ),
        "ussd.safety_continue": "1. Endelea\n9. Rudi",
        "ussd.continue": "1. Endelea\n9. Rudi",
    },
    "nyn": {
        "ussd.topic_menu": (
            "1. Emitendera y'okukora\n"
            "2. Ahu orikubaasa kushanga obuhwezi\n"
            "9. Garuka"
        ),
        "ussd.safety_continue": "1. Gumizamu\n9. Garuka",
        "ussd.continue": "1. Gumizamu\n9. Garuka",
    },
}

PREVIOUS_BACK_COPY = {
    "lg": {
        "ussd.topic_menu": (
            "1. Emitendera gy'okukola\n"
            "2. Enkola z'obuyambi\n"
            "0. Ddayo"
        ),
        "ussd.safety_continue": "1. Weyongereyo\n0. Ddayo",
        "ussd.continue": "1. Weyongereyo\n0. Ddayo",
    },
    "sw": {
        "ussd.topic_menu": (
            "1. Hatua za kuchukua\n"
            "2. Mawasiliano ya msaada\n"
            "0. Rudi"
        ),
        "ussd.safety_continue": "1. Endelea\n0. Rudi",
        "ussd.continue": "1. Endelea\n0. Rudi",
    },
    "nyn": {
        "ussd.topic_menu": (
            "1. Emitendera y'okukora\n"
            "2. Ahu orikubaasa kushanga obuhwezi\n"
            "0. Garuka"
        ),
        "ussd.safety_continue": "1. Gumizamu\n0. Garuka",
        "ussd.continue": "1. Gumizamu\n0. Garuka",
    },
}

NEW_EXIT_COPY = {
    "lg": "Fuluma",
    "sw": "Toka",
    "nyn": "Rugamu",
}


def update_back_digit_and_add_exit(apps, schema_editor):
    ChannelContent = apps.get_model("content", "ChannelContent")

    for language, entries in UPDATED_BACK_COPY.items():
        for content_key, text in entries.items():
            ChannelContent.objects.filter(
                content_key=content_key,
                language=language,
                channel="ussd",
            ).update(text=text)

    for language, exit_label in NEW_EXIT_COPY.items():
        ChannelContent.objects.get_or_create(
            content_key="ussd.exit",
            language=language,
            channel="ussd",
            defaults={
                "text": exit_label,
                "is_verified": False,
                "reviewed_by": "",
                "last_reviewed": None,
                "is_active": True,
            },
        )


def revert_back_digit_and_remove_exit(apps, schema_editor):
    ChannelContent = apps.get_model("content", "ChannelContent")

    for language, entries in PREVIOUS_BACK_COPY.items():
        for content_key, text in entries.items():
            ChannelContent.objects.filter(
                content_key=content_key,
                language=language,
                channel="ussd",
            ).update(text=text)

    for language in NEW_EXIT_COPY:
        ChannelContent.objects.filter(
            content_key="ussd.exit",
            language=language,
            channel="ussd",
        ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("channels", "0012_smscontext_pending_referral_step"),
        ("content", "0002_alter_channelcontent_unique_together_and_more"),
    ]

    operations = [
        migrations.RunPython(
            update_back_digit_and_add_exit,
            revert_back_digit_and_remove_exit,
        ),
    ]
```

Save this as `backend/apps/channels/migrations/0013_update_ussd_back_and_exit_copy.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.channels.ussd.tests --noinput`
Expected: all `SeededTranslationCopyTests` pass (Django's test runner applies all migrations, including this new one, to the test database before running tests). Also run `python manage.py migrate channels --check` (from `backend/`) to confirm the migration is recognized with no missing dependencies.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/migrations/0013_update_ussd_back_and_exit_copy.py backend/apps/channels/ussd/tests.py
git commit -m "data: update seeded lg/sw/nyn USSD copy for Back-on-9 and add ussd.exit"
```

---

## Task 11: Full regression pass

**Files:** none (verification only — fixes here are corrective, applied to whichever file needs it)

**Interfaces:**
- Consumes: the complete feature from Tasks 1–10.
- Produces: a fully green `apps.channels.ussd.tests` suite with no leftover budget/text regressions in the tests that weren't explicitly touched above (`test_render_topics_stage_never_exceeds_screen_cap_with_many_topics`, `test_many_topics_are_reachable_via_more_not_silently_dropped`, `test_long_unbreakable_token_never_exceeds_screen_cap`, `test_render_first_page_shows_more_option_when_not_all_fit`) — these only assert screen length (`<= 182`) or the presence of "8."/pagination markers, neither of which this feature changes, but they exercise the same reserved-budget math that grew by one line per screen, so they need an explicit passing run to confirm.

- [ ] **Step 1: Run the full USSD test suite**

Run: `python manage.py test apps.channels.ussd.tests --noinput -v 2`
Expected: all tests pass (the suite grew from 106 tests at baseline to roughly 106 + ~25 new/modified assertions added across Tasks 1–10).

- [ ] **Step 2: If any budget-cap test fails, diagnose and fix**

If a `self.assertLessEqual(len(text), 182)` assertion fails, it means the extra reserved line ("0. Exit") pushed some already-tight screen over budget. Read the failing test's `chunk_index`/fixture to find which render function is involved, and inspect the actual returned `text` (print it in a one-off `python manage.py shell` session or a temporary `print()` in the test) to see which line is too long. The fix is almost always in `_fit_numbered_lines`' caller (`_situation_list_page` or `_situation_topics_page`) reducing `max_items` further, or in `_chunked_screen`'s `body_budget` calculation — do not raise `SCREEN_BUDGET` or the 182 cap itself, since those are fixed by the AT gateway's real limit, not something this feature can change.

- [ ] **Step 3: Run the broader backend test suite to confirm no cross-app breakage**

Run: `python manage.py test --noinput`
Expected: all tests pass — this feature only touches `apps.channels.ussd` and one new `apps.channels` migration, so no other app's tests should be affected, but this confirms the migration graph is consistent and nothing elsewhere reads USSD copy strings.

- [ ] **Step 4: Manual smoke check of the spec's core promise**

In `python manage.py shell` (from `backend/`), confirm exit works from a screen several levels deep:

```python
from apps.channels.ussd.handler import handle_ussd_request
handle_ussd_request("smoke-1", "+256700000001", "")       # language_select
handle_ussd_request("smoke-1", "+256700000001", "1")       # main_menu
handle_ussd_request("smoke-1", "+256700000001", "1*1")     # situation_list
response = handle_ussd_request("smoke-1", "+256700000001", "1*1*0")  # exit from situation_list
assert response.startswith("END "), response
print("OK:", response)
```

Expected: prints `OK: END Thank you for using Sauti Yo.` — confirming a real exit from a non-main-menu screen end-to-end.

- [ ] **Step 5: Commit (only if Step 2 required a fix)**

```bash
git add backend/apps/channels/ussd/menus.py backend/apps/channels/ussd/tests.py
git commit -m "fix: keep USSD screens under the AT screen cap after adding the global Exit line"
```

If Step 2 required no fix, skip this commit — there's nothing to commit.
