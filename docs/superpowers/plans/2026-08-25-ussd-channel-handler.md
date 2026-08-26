# USSD Channel Handler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working USSD channel for Sauti Yo — a citizen dials a service code, picks a language, browses Situations → Rights Topics → Action Steps / Support Contacts, with a mandatory safety-warning gate for sensitive/high-risk topics and a direct emergency-contacts shortcut, all served over Africa's Talking's synchronous USSD webhook contract.

**Architecture:** A DB-backed `UssdSession` (state + JSON context) tracks each session between requests. `menus.py` holds a small state machine: one `render_<state>` function (pure, produces the screen text for a state) and one `transition_<state>` function (pure, decides the next state from the current state + user input) per screen. `handler.py` is the orchestrator that loads the session, applies a transition, renders the resulting state, and persists it — including centralized invalid-input handling (redisplay + 3-strikes session termination). `views.py` is a thin Django view translating Africa's Talking's form-POST/plain-text contract to/from the handler.

**Tech Stack:** Django 6.1, Django's built-in `TestCase` / `manage.py test` (no pytest, no DRF for this endpoint — Africa's Talking expects `text/plain`, not JSON), PostgreSQL (existing `apps.channels` app, no new infra).

## Global Constraints

- Test runner is Django's built-in one: `cd backend && python manage.py test <label>`. This project does not use pytest.
- The USSD webhook view is a plain Django view, not a DRF `APIView` — Africa's Talking POSTs form-encoded data and requires a `text/plain` body starting with `CON ` (continue) or `END ` (terminate).
- Screen character budget: 160 characters (conservative margin under Africa's Talking's ~182-char USSD screen cap), defined as `SCREEN_BUDGET` in `menus.py`.
- No Redis/Celery are available — `UssdSession` is a plain Postgres-backed Django model, no cache layer.
- `UssdSession` lives in `apps/channels/models.py` (not under `ussd/`) so Django's migration discovery for the `apps.channels` app picks it up.
- Rights content (`Situation.description`, `RightsTopic.summary`, `ActionStep.description`, `SafetyResponse.message`) is served in English regardless of the selected language — only USSD chrome (menu labels, prompts) is looked up per-language via `ChannelContent(channel="ussd")`, falling back to hardcoded English `DEFAULT_COPY` when no row exists. See spec section "Language handling".
- Spec: `docs/superpowers/specs/2026-08-25-ussd-channel-handler-design.md` — this plan implements that spec in full; consult it for the "why" behind any decision below.
- **Amendment (found during Task 5 implementation):** the plan originally assumed `RightsTopic` already had a `risk_level` field (it doesn't — only `Situation` does). Task 5 adds `risk_level` to `RightsTopic` (`apps/rights/models.py`, choices `standard`/`sensitive`/`high_risk`, default `"standard"`, matching `Situation.RISK_LEVEL_CHOICES`) plus its migration, so that `_enter_topic()`'s `topic.risk_level` check (Task 5) and the safety-gate tests (Task 6) work as originally written. This is the only place this plan modifies a model outside `apps.channels`.
- **Amendment (found during Task 6 review):** `_chunked_screen(text, chunk_index, trailing_options, language)` returns `(screen_text, is_last)`, where `is_last` means "this is the final chunk of body text, so show `trailing_options` instead of More/Back" — it does **not** mean "the USSD session should terminate." Every screen using it (`situation_detail`, `topic_detail`, `safety_gate`, `support_contacts`, `emergency_list`) must discard that second value and hardcode `ended=False`, e.g. `screen, _ = _chunked_screen(...); return screen, False`, never `return _chunked_screen(...)` directly — otherwise the very act of reaching the last chunk of a topic's summary or the safety warning (which happens on the *first* render whenever the text is short enough to fit one screen — the common case) would send Africa's Talking an `END`-prefixed response while a "1. Continue"/"1. Action steps" menu is still showing, killing the session before the user can respond. Only `render_goodbye` should ever return `ended=True`. Every `render_*` function's tests must include a last-chunk (or single-chunk) assertion that `ended is False`, not just a non-last-chunk case.

---

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `backend/apps/channels/models.py` | Modify | Add `UssdSession` model |
| `backend/apps/rights/models.py` | Modify (Task 5 amendment) | Add `risk_level` to `RightsTopic` |
| `backend/apps/rights/migrations/000X_risktopic_risk_level.py` | Generate (Task 5 amendment) | Migration for the new field |
| `backend/apps/channels/migrations/000X_ussdsession.py` | Generate | Migration for `UssdSession` |
| `backend/apps/channels/ussd/sessions.py` | Create | CRUD helpers over `UssdSession` |
| `backend/apps/channels/ussd/menus.py` | Create | Copy/pagination helpers + one render/transition function pair per screen state + dispatch tables |
| `backend/apps/channels/ussd/handler.py` | Create | `handle_ussd_request()` orchestrator |
| `backend/apps/channels/ussd/views.py` | Create | Django view for the Africa's Talking webhook |
| `backend/apps/channels/ussd/tests.py` | Create | All tests for this feature (grows across tasks) |
| `backend/apps/channels/urls.py` | Create | Routes `ussd/` to the view |
| `backend/config/urls.py` | Modify | Mount `apps.channels.urls` at `api/channels/` |

---

### Task 1: `UssdSession` model

**Files:**
- Modify: `backend/apps/channels/models.py`
- Test: `backend/apps/channels/ussd/tests.py`

**Interfaces:**
- Produces: `apps.channels.models.UssdSession` with fields `session_id` (unique str), `phone_number` (str), `language` (str, blank-able, one of `""`, `"en"`, `"lg"`, `"sw"`, `"nyn"`), `state` (str, default `"language_select"`), `context` (dict, default `{}`), `is_active` (bool, default `True`), `created_at`, `updated_at`.

- [ ] **Step 1: Write the failing test**

Create `backend/apps/channels/ussd/tests.py`:

```python
from django.db import IntegrityError
from django.test import TestCase

from apps.channels.models import UssdSession


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.channels.ussd.tests.UssdSessionModelTests -v 2`
Expected: FAIL — `ImportError: cannot import name 'UssdSession' from 'apps.channels.models'`

- [ ] **Step 3: Write minimal implementation**

Replace the contents of `backend/apps/channels/models.py`:

```python
from django.db import models


class UssdSession(models.Model):
    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("lg", "Luganda"),
        ("sw", "Kiswahili"),
        ("nyn", "Runyankole"),
    ]

    session_id = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=50)

    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        blank=True,
    )

    state = models.CharField(max_length=50, default="language_select")

    context = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.session_id} ({self.state})"
```

- [ ] **Step 4: Generate and run the migration**

Run: `cd backend && python manage.py makemigrations apps.channels`
Expected: creates `backend/apps/channels/migrations/0001_ussdsession.py` (or next number) with a `CreateModel` for `UssdSession`.

Run: `cd backend && python manage.py migrate apps.channels`
Expected: `Applying apps.channels.0001_ussdsession... OK`

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && python manage.py test apps.channels.ussd.tests.UssdSessionModelTests -v 2`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/apps/channels/models.py backend/apps/channels/migrations backend/apps/channels/ussd/tests.py
git commit -m "feat: add UssdSession model for USSD channel state"
```

---

### Task 2: Session CRUD helpers

**Files:**
- Create: `backend/apps/channels/ussd/sessions.py`
- Test: `backend/apps/channels/ussd/tests.py`

**Interfaces:**
- Consumes: `apps.channels.models.UssdSession` (Task 1)
- Produces: `sessions.get_or_create_session(session_id: str, phone_number: str) -> (UssdSession, bool)` (same return shape as Django's `get_or_create`), `sessions.update_session(session: UssdSession, **fields) -> UssdSession`, `sessions.end_session(session: UssdSession) -> UssdSession`

- [ ] **Step 1: Write the failing test**

Append to `backend/apps/channels/ussd/tests.py`:

```python
from apps.channels.ussd import sessions


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.channels.ussd.tests.SessionHelperTests -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.channels.ussd.sessions'`

- [ ] **Step 3: Write minimal implementation**

Create `backend/apps/channels/ussd/sessions.py`:

```python
from apps.channels.models import UssdSession


def get_or_create_session(session_id, phone_number):
    return UssdSession.objects.get_or_create(
        session_id=session_id,
        defaults={
            "phone_number": phone_number,
            "state": "language_select",
        },
    )


def update_session(session, **fields):
    for field, value in fields.items():
        setattr(session, field, value)
    session.save()
    return session


def end_session(session):
    return update_session(session, is_active=False)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python manage.py test apps.channels.ussd.tests.SessionHelperTests -v 2`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/ussd/sessions.py backend/apps/channels/ussd/tests.py
git commit -m "feat: add USSD session CRUD helpers"
```

---

### Task 3: Copy lookup + pagination/chunking helpers

**Files:**
- Create: `backend/apps/channels/ussd/menus.py`
- Test: `backend/apps/channels/ussd/tests.py`

**Interfaces:**
- Consumes: `apps.content.models.ChannelContent`
- Produces: `menus.SCREEN_BUDGET` (int, 160), `menus.PAGE_SIZE` (int, 5), `menus.TITLE_TRUNCATE_LENGTH` (int, 40), `menus.DEFAULT_COPY` (dict[str, str]), `menus.get_copy(content_key: str, language: str) -> str`, `menus.truncate(text: str, limit: int) -> str`, `menus.chunk_text(text: str, budget: int = SCREEN_BUDGET) -> list[str]`, `menus.paginate_items(items: list, page: int, page_size: int = PAGE_SIZE) -> (list, bool)`

- [ ] **Step 1: Write the failing test**

Append to `backend/apps/channels/ussd/tests.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.channels.ussd.tests.TextHelperTests apps.channels.ussd.tests.GetCopyTests -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.channels.ussd.menus'`

- [ ] **Step 3: Write minimal implementation**

Create `backend/apps/channels/ussd/menus.py`:

```python
from apps.content.models import ChannelContent

SCREEN_BUDGET = 160
PAGE_SIZE = 5
TITLE_TRUNCATE_LENGTH = 40

DEFAULT_COPY = {
    "ussd.welcome": "Welcome to Sauti Yo",
    "ussd.language_prompt": (
        "1. English\n2. Luganda\n3. Kiswahili\n4. Runyankole"
    ),
    "ussd.main_menu": "1. Find my rights\n2. Get help now\n0. Exit",
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
    "ussd.topic_menu": "1. Action steps\n2. Support contacts\n0. Back",
    "ussd.safety_continue": "1. Continue\n0. Back",
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
}


def get_copy(content_key, language):
    content = ChannelContent.objects.filter(
        content_key=content_key,
        language=language,
        channel="ussd",
        is_active=True,
    ).first()
    if content:
        return content.text
    return DEFAULT_COPY.get(content_key, "")


def truncate(text, limit):
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def chunk_text(text, budget=SCREEN_BUDGET):
    words = text.split()
    chunks = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > budget:
            if current:
                chunks.append(current)
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks or [""]


def paginate_items(items, page, page_size=PAGE_SIZE):
    start = page * page_size
    end = start + page_size
    page_items = items[start:end]
    has_more = end < len(items)
    return page_items, has_more
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python manage.py test apps.channels.ussd.tests.TextHelperTests apps.channels.ussd.tests.GetCopyTests -v 2`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/ussd/menus.py backend/apps/channels/ussd/tests.py
git commit -m "feat: add USSD copy lookup and pagination/chunking helpers"
```

---

### Task 4: Language picker, main menu, goodbye screens

**Files:**
- Modify: `backend/apps/channels/ussd/menus.py`
- Test: `backend/apps/channels/ussd/tests.py`

**Interfaces:**
- Consumes: `apps.channels.models.UssdSession` (Task 1), `get_copy` (Task 3)
- Produces: `menus.render_language_select(session) -> (str, bool)`, `menus.transition_language_select(session, user_input: str) -> (str, dict) | None`, `menus.render_main_menu(session) -> (str, bool)`, `menus.transition_main_menu(session, user_input: str) -> (str, dict) | None`, `menus.render_goodbye(session) -> (str, bool)`

  A `transition_*` function returns `None` to signal invalid input (handled centrally by `handler.py` in Task 8), or a `(next_state, next_context)` tuple on success. A `render_*` function always returns `(screen_text, ended)`.

- [ ] **Step 1: Write the failing test**

Append to `backend/apps/channels/ussd/tests.py`:

```python
from apps.channels.models import UssdSession


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.channels.ussd.tests.LanguageSelectTests apps.channels.ussd.tests.MainMenuTests apps.channels.ussd.tests.GoodbyeTests -v 2`
Expected: FAIL — `AttributeError: module 'apps.channels.ussd.menus' has no attribute 'render_language_select'`

- [ ] **Step 3: Write minimal implementation**

Append to `backend/apps/channels/ussd/menus.py`:

```python
def render_language_select(session):
    body = get_copy("ussd.welcome", session.language)
    prompt = get_copy("ussd.language_prompt", session.language)
    return f"{body}\n{prompt}", False


def transition_language_select(session, user_input):
    mapping = {"1": "en", "2": "lg", "3": "sw", "4": "nyn"}
    language = mapping.get(user_input)
    if language is None:
        return None
    session.language = language
    return "main_menu", {}


def render_main_menu(session):
    return get_copy("ussd.main_menu", session.language), False


def transition_main_menu(session, user_input):
    if user_input == "1":
        return "situation_list", {"page": 0}
    if user_input == "2":
        return "emergency_list", {"chunk_index": 0}
    if user_input == "0":
        return "goodbye", {}
    return None


def render_goodbye(session):
    return get_copy("ussd.goodbye", session.language), True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python manage.py test apps.channels.ussd.tests.LanguageSelectTests apps.channels.ussd.tests.MainMenuTests apps.channels.ussd.tests.GoodbyeTests -v 2`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/ussd/menus.py backend/apps/channels/ussd/tests.py
git commit -m "feat: add USSD language picker, main menu, and goodbye screens"
```

---

### Task 5: Situation list and situation detail screens

**Files:**
- Modify: `backend/apps/channels/ussd/menus.py`
- Test: `backend/apps/channels/ussd/tests.py`

**Interfaces:**
- Consumes: `apps.rights.models.{Situation, RightsTopic, SituationRightsTopic}`, `truncate`/`paginate_items`/`get_copy`/`chunk_text` (Task 3)
- Produces: `menus.render_situation_list(session) -> (str, bool)`, `menus.transition_situation_list(session, user_input) -> (str, dict) | None`, `menus.render_situation_detail(session) -> (str, bool)`, `menus.transition_situation_detail(session, user_input) -> (str, dict) | None`, and the internal helpers `menus._topics_for_situation(situation) -> QuerySet[RightsTopic]`, `menus._enter_topic(situation_slug: str, topic: RightsTopic) -> (str, dict)` — `_enter_topic` is also consumed directly by Task 6's safety-gate logic and by Task 8's dispatch wiring context.

- [ ] **Step 1: Write the failing test**

Append to `backend/apps/channels/ussd/tests.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.channels.ussd.tests.SituationListTests apps.channels.ussd.tests.SituationDetailTests -v 2`
Expected: FAIL — `AttributeError: module 'apps.channels.ussd.menus' has no attribute 'render_situation_list'`

- [ ] **Step 3: Write minimal implementation**

Append to `backend/apps/channels/ussd/menus.py`:

```python
from apps.rights.models import RightsTopic, Situation


def _topics_for_situation(situation):
    return (
        RightsTopic.objects.filter(
            situation_links__situation=situation,
            is_active=True,
        )
        .order_by("title")
        .distinct()
    )


def _enter_topic(situation_slug, topic):
    context = {
        "situation_slug": situation_slug,
        "topic_slug": topic.slug,
        "chunk_index": 0,
    }
    if topic.risk_level in ("sensitive", "high_risk"):
        safety = topic.safety_responses.filter(
            trigger_key="default", is_active=True
        ).first()
        if safety is not None:
            return "safety_gate", context
    return "topic_detail", context


def render_situation_list(session):
    situations = list(
        Situation.objects.filter(is_active=True).order_by("title")
    )
    page = session.context.get("page", 0)
    page_items, has_more = paginate_items(situations, page, PAGE_SIZE)
    back = get_copy("ussd.back", session.language)

    if not page_items:
        body = get_copy("ussd.no_situations", session.language)
        return f"{body}\n\n0. {back}", False

    lines = [get_copy("ussd.choose_situation", session.language)]
    for index, situation in enumerate(page_items, start=1):
        lines.append(f"{index}. {truncate(situation.title, TITLE_TRUNCATE_LENGTH)}")
    if has_more:
        lines.append(f"8. {get_copy('ussd.more', session.language)}")
    lines.append(f"0. {back}")
    return "\n".join(lines), False


def transition_situation_list(session, user_input):
    situations = list(
        Situation.objects.filter(is_active=True).order_by("title")
    )
    page = session.context.get("page", 0)
    page_items, has_more = paginate_items(situations, page, PAGE_SIZE)

    if user_input == "0":
        return "main_menu", {}
    if user_input == "8" and has_more:
        return "situation_list", {"page": page + 1}
    if user_input.isdigit():
        choice = int(user_input)
        if 1 <= choice <= len(page_items):
            situation = page_items[choice - 1]
            topics = list(_topics_for_situation(situation)[:9])
            if len(topics) == 1:
                return _enter_topic(situation.slug, topics[0])
            return (
                "situation_detail",
                {"situation_slug": situation.slug, "chunk_index": 0},
            )
    return None


def render_situation_detail(session):
    situation = Situation.objects.filter(
        slug=session.context.get("situation_slug"), is_active=True
    ).first()
    if situation is None:
        return get_copy("ussd.not_found", session.language), False

    topics = list(_topics_for_situation(situation)[:9])
    chunk_index = session.context.get("chunk_index", 0)
    back = get_copy("ussd.back", session.language)

    if topics:
        lines = [get_copy("ussd.related_rights", session.language)]
        for index, topic in enumerate(topics, start=1):
            lines.append(f"{index}. {truncate(topic.title, TITLE_TRUNCATE_LENGTH)}")
        lines.append(f"0. {back}")
        trailing = "\n".join(lines)
    else:
        trailing = f"0. {back}"

    text = situation.description or situation.title
    screen, _ = _chunked_screen(text, chunk_index, trailing, session.language)
    return screen, False


def transition_situation_detail(session, user_input):
    situation = Situation.objects.filter(
        slug=session.context.get("situation_slug"), is_active=True
    ).first()
    if situation is None:
        return "situation_list", {"page": 0}

    topics = list(_topics_for_situation(situation)[:9])
    chunk_index = session.context.get("chunk_index", 0)
    text = situation.description or situation.title
    is_last = _is_last_chunk(text, chunk_index)

    if not is_last:
        if user_input == "1":
            return (
                "situation_detail",
                {**session.context, "chunk_index": chunk_index + 1},
            )
        if user_input == "0":
            return "situation_list", {"page": 0}
        return None

    if user_input == "0":
        return "situation_list", {"page": 0}
    if topics and user_input.isdigit():
        choice = int(user_input)
        if 1 <= choice <= len(topics):
            return _enter_topic(situation.slug, topics[choice - 1])
    return None
```

Also add the shared chunking helpers just above `render_situation_list` in the same file (these are used by this task and by Tasks 6-7):

```python
def _chunked_screen(text, chunk_index, trailing_options, language):
    chunks = chunk_text(text) if text else [""]
    chunk_index = max(0, min(chunk_index, len(chunks) - 1))
    body = chunks[chunk_index]
    is_last = chunk_index == len(chunks) - 1
    if is_last:
        screen = f"{body}\n\n{trailing_options}" if trailing_options else body
    else:
        more = get_copy("ussd.more", language)
        back = get_copy("ussd.back", language)
        screen = f"{body}\n\n1. {more}\n0. {back}"
    return screen, is_last


def _is_last_chunk(text, chunk_index):
    chunks = chunk_text(text) if text else [""]
    return max(0, min(chunk_index, len(chunks) - 1)) == len(chunks) - 1
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python manage.py test apps.channels.ussd.tests.SituationListTests apps.channels.ussd.tests.SituationDetailTests -v 2`
Expected: PASS (12 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/ussd/menus.py backend/apps/channels/ussd/tests.py
git commit -m "feat: add USSD situation list and situation detail screens"
```

---

### Task 6: Topic detail, safety gate, and action steps screens

**Files:**
- Modify: `backend/apps/channels/ussd/menus.py`
- Test: `backend/apps/channels/ussd/tests.py`

**Interfaces:**
- Consumes: `apps.rights.models.{RightsTopic, ActionStep, SafetyResponse}`, `_chunked_screen`/`_is_last_chunk`/`_topics_for_situation` (Task 5), `get_copy` (Task 3)
- Produces: `menus.render_topic_detail`, `menus.transition_topic_detail`, `menus.render_safety_gate`, `menus.transition_safety_gate`, `menus.render_action_steps`, `menus.transition_action_steps` (all `(session) -> (str, bool)` for render, `(session, user_input) -> (str, dict) | None` for transition), plus internal helpers `menus._back_from_topic(situation_slug, topic_slug) -> (str, dict)` and `menus._back_to_topic_detail(situation_slug, topic_slug) -> (str, dict)`, consumed by Task 7's support-contacts "back" transition.

- [ ] **Step 1: Write the failing test**

Append to `backend/apps/channels/ussd/tests.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.channels.ussd.tests.TopicDetailTests apps.channels.ussd.tests.SafetyGateTests apps.channels.ussd.tests.ActionStepsTests -v 2`
Expected: FAIL — `AttributeError: module 'apps.channels.ussd.menus' has no attribute 'render_topic_detail'`

- [ ] **Step 3: Write minimal implementation**

Append to `backend/apps/channels/ussd/menus.py`:

```python
def _back_to_topic_detail(situation_slug, topic_slug):
    return "topic_detail", {
        "situation_slug": situation_slug,
        "topic_slug": topic_slug,
        "chunk_index": 9999,
    }


def _back_from_topic(situation_slug, topic_slug):
    situation = Situation.objects.filter(
        slug=situation_slug, is_active=True
    ).first()
    if situation is None:
        return "situation_list", {"page": 0}
    topics = list(_topics_for_situation(situation)[:9])
    if len(topics) <= 1:
        return "situation_list", {"page": 0}
    return (
        "situation_detail",
        {"situation_slug": situation_slug, "chunk_index": 9999},
    )


def render_topic_detail(session):
    topic = RightsTopic.objects.filter(
        slug=session.context.get("topic_slug"), is_active=True
    ).first()
    if topic is None:
        return get_copy("ussd.not_found", session.language), False

    chunk_index = session.context.get("chunk_index", 0)
    menu = get_copy("ussd.topic_menu", session.language)
    text = topic.summary or topic.title
    screen, _ = _chunked_screen(text, chunk_index, menu, session.language)
    return screen, False


def transition_topic_detail(session, user_input):
    situation_slug = session.context.get("situation_slug")
    topic_slug = session.context.get("topic_slug")
    topic = RightsTopic.objects.filter(slug=topic_slug, is_active=True).first()
    if topic is None:
        return "situation_list", {"page": 0}

    chunk_index = session.context.get("chunk_index", 0)
    text = topic.summary or topic.title
    is_last = _is_last_chunk(text, chunk_index)

    if not is_last:
        if user_input == "1":
            return (
                "topic_detail",
                {**session.context, "chunk_index": chunk_index + 1},
            )
        if user_input == "0":
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
    if user_input == "0":
        return _back_from_topic(situation_slug, topic_slug)
    return None


def render_safety_gate(session):
    topic = RightsTopic.objects.filter(
        slug=session.context.get("topic_slug"), is_active=True
    ).first()
    if topic is None:
        return get_copy("ussd.not_found", session.language), False

    safety = topic.safety_responses.filter(
        trigger_key="default", is_active=True
    ).first()
    message = safety.message if safety else topic.summary or topic.title
    chunk_index = session.context.get("chunk_index", 0)
    options = get_copy("ussd.safety_continue", session.language)
    screen, _ = _chunked_screen(message, chunk_index, options, session.language)
    return screen, False


def transition_safety_gate(session, user_input):
    situation_slug = session.context.get("situation_slug")
    topic_slug = session.context.get("topic_slug")
    topic = RightsTopic.objects.filter(slug=topic_slug, is_active=True).first()
    if topic is None:
        return "situation_list", {"page": 0}

    safety = topic.safety_responses.filter(
        trigger_key="default", is_active=True
    ).first()
    message = safety.message if safety else topic.summary or topic.title
    chunk_index = session.context.get("chunk_index", 0)
    is_last = _is_last_chunk(message, chunk_index)

    if not is_last:
        if user_input == "1":
            return (
                "safety_gate",
                {**session.context, "chunk_index": chunk_index + 1},
            )
        if user_input == "0":
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
    if user_input == "0":
        return _back_from_topic(situation_slug, topic_slug)
    return None


def render_action_steps(session):
    topic = RightsTopic.objects.filter(
        slug=session.context.get("topic_slug"), is_active=True
    ).first()
    if topic is None:
        return get_copy("ussd.not_found", session.language), False

    steps = list(
        topic.action_steps.filter(is_active=True).order_by("order", "id")
    )
    back_label = get_copy("ussd.back", session.language)
    if not steps:
        body = get_copy("ussd.no_action_steps", session.language)
        return f"{body}\n\n0. {back_label}", False

    step_index = min(session.context.get("step_index", 0), len(steps) - 1)
    step = steps[step_index]
    text = f"Step {step_index + 1}/{len(steps)}: {step.title}\n{step.description}"
    chunk_index = session.context.get("chunk_index", 0)

    has_next = step_index + 1 < len(steps)
    if has_next:
        next_label = get_copy("ussd.next", session.language)
        trailing = f"1. {next_label}\n0. {back_label}"
    else:
        trailing = f"0. {back_label}"

    return _chunked_screen(text, chunk_index, trailing, session.language)


def transition_action_steps(session, user_input):
    situation_slug = session.context.get("situation_slug")
    topic_slug = session.context.get("topic_slug")
    topic = RightsTopic.objects.filter(slug=topic_slug, is_active=True).first()
    if topic is None:
        return "situation_list", {"page": 0}

    steps = list(
        topic.action_steps.filter(is_active=True).order_by("order", "id")
    )
    if not steps:
        if user_input == "0":
            return _back_to_topic_detail(situation_slug, topic_slug)
        return None

    step_index = min(session.context.get("step_index", 0), len(steps) - 1)
    step = steps[step_index]
    text = f"Step {step_index + 1}/{len(steps)}: {step.title}\n{step.description}"
    chunk_index = session.context.get("chunk_index", 0)
    is_last = _is_last_chunk(text, chunk_index)
    has_next = step_index + 1 < len(steps)

    if not is_last:
        if user_input == "1":
            return (
                "action_steps",
                {**session.context, "chunk_index": chunk_index + 1},
            )
        if user_input == "0":
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
    if user_input == "0":
        return _back_to_topic_detail(situation_slug, topic_slug)
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python manage.py test apps.channels.ussd.tests.TopicDetailTests apps.channels.ussd.tests.SafetyGateTests apps.channels.ussd.tests.ActionStepsTests -v 2`
Expected: PASS (11 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/ussd/menus.py backend/apps/channels/ussd/tests.py
git commit -m "feat: add USSD topic detail, safety gate, and action steps screens"
```

---

### Task 7: Support contacts and emergency list screens

**Files:**
- Modify: `backend/apps/channels/ussd/menus.py`
- Test: `backend/apps/channels/ussd/tests.py`

**Interfaces:**
- Consumes: `apps.support.models.SupportService`, `_chunked_screen`/`_is_last_chunk` (Task 5), `_back_to_topic_detail` (Task 6), `get_copy` (Task 3)
- Produces: `menus.render_support_contacts`, `menus.transition_support_contacts`, `menus.render_emergency_list`, `menus.transition_emergency_list` (same render/transition shapes as prior tasks), plus internal helper `menus._format_contacts(services) -> str`

- [ ] **Step 1: Write the failing test**

Append to `backend/apps/channels/ussd/tests.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.channels.ussd.tests.SupportContactsTests apps.channels.ussd.tests.EmergencyListTests -v 2`
Expected: FAIL — `AttributeError: module 'apps.channels.ussd.menus' has no attribute 'render_support_contacts'`

- [ ] **Step 3: Write minimal implementation**

Append to `backend/apps/channels/ussd/menus.py`:

```python
from apps.support.models import SupportService


def _format_contacts(services):
    lines = []
    for service in services:
        phone = service.phone_number or service.alternate_phone_number or "N/A"
        lines.append(f"{service.name}: {phone}")
    return "\n".join(lines)


def render_support_contacts(session):
    topic = RightsTopic.objects.filter(
        slug=session.context.get("topic_slug"), is_active=True
    ).first()
    if topic is None:
        return get_copy("ussd.not_found", session.language), False

    services = list(topic.support_services.filter(is_active=True).order_by("name"))
    chunk_index = session.context.get("chunk_index", 0)
    back = f"0. {get_copy('ussd.back', session.language)}"

    if not services:
        body = get_copy("ussd.no_support_contacts", session.language)
        return f"{body}\n\n{back}", False

    screen, _ = _chunked_screen(
        _format_contacts(services), chunk_index, back, session.language
    )
    return screen, False


def transition_support_contacts(session, user_input):
    situation_slug = session.context.get("situation_slug")
    topic_slug = session.context.get("topic_slug")
    topic = RightsTopic.objects.filter(slug=topic_slug, is_active=True).first()
    if topic is None:
        return "situation_list", {"page": 0}

    services = list(topic.support_services.filter(is_active=True).order_by("name"))
    if not services:
        if user_input == "0":
            return _back_to_topic_detail(situation_slug, topic_slug)
        return None

    chunk_index = session.context.get("chunk_index", 0)
    is_last = _is_last_chunk(_format_contacts(services), chunk_index)

    if not is_last:
        if user_input == "1":
            return (
                "support_contacts",
                {**session.context, "chunk_index": chunk_index + 1},
            )
        if user_input == "0":
            return _back_to_topic_detail(situation_slug, topic_slug)
        return None

    if user_input == "0":
        return _back_to_topic_detail(situation_slug, topic_slug)
    return None


def render_emergency_list(session):
    services = list(
        SupportService.objects.filter(
            is_emergency_service=True, is_active=True
        ).order_by("name")
    )
    chunk_index = session.context.get("chunk_index", 0)
    back = f"0. {get_copy('ussd.back', session.language)}"

    if not services:
        body = get_copy("ussd.no_emergency_contacts", session.language)
        return f"{body}\n\n{back}", False

    screen, _ = _chunked_screen(
        _format_contacts(services), chunk_index, back, session.language
    )
    return screen, False


def transition_emergency_list(session, user_input):
    services = list(
        SupportService.objects.filter(
            is_emergency_service=True, is_active=True
        ).order_by("name")
    )
    if not services:
        if user_input == "0":
            return "main_menu", {}
        return None

    chunk_index = session.context.get("chunk_index", 0)
    is_last = _is_last_chunk(_format_contacts(services), chunk_index)

    if not is_last:
        if user_input == "1":
            return (
                "emergency_list",
                {**session.context, "chunk_index": chunk_index + 1},
            )
        if user_input == "0":
            return "main_menu", {}
        return None

    if user_input == "0":
        return "main_menu", {}
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python manage.py test apps.channels.ussd.tests.SupportContactsTests apps.channels.ussd.tests.EmergencyListTests -v 2`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/ussd/menus.py backend/apps/channels/ussd/tests.py
git commit -m "feat: add USSD support contacts and emergency list screens"
```

---

### Task 8: Dispatch tables and the `handler.py` orchestrator

**Files:**
- Modify: `backend/apps/channels/ussd/menus.py`
- Create: `backend/apps/channels/ussd/handler.py`
- Test: `backend/apps/channels/ussd/tests.py`

**Interfaces:**
- Consumes: every `render_*`/`transition_*` pair from Tasks 4-7, `sessions.get_or_create_session`/`update_session`/`end_session` (Task 2), `get_copy` (Task 3)
- Produces: `menus.render_state(state: str, session) -> (str, bool)`, `menus.transition_state(state: str, session, user_input: str) -> (str, dict) | None`, `handler.handle_ussd_request(session_id: str, phone_number: str, text: str) -> str` — the full `CON `/`END `-prefixed response string, consumed directly by Task 9's view.

- [ ] **Step 1: Write the failing test**

Append to `backend/apps/channels/ussd/tests.py`:

```python
from apps.channels.ussd.handler import handle_ussd_request


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.channels.ussd.tests.HandleUssdRequestTests -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.channels.ussd.handler'`

- [ ] **Step 3: Write minimal implementation**

Append to `backend/apps/channels/ussd/menus.py`:

```python
RENDER_HANDLERS = {
    "language_select": render_language_select,
    "main_menu": render_main_menu,
    "goodbye": render_goodbye,
    "situation_list": render_situation_list,
    "situation_detail": render_situation_detail,
    "safety_gate": render_safety_gate,
    "topic_detail": render_topic_detail,
    "action_steps": render_action_steps,
    "support_contacts": render_support_contacts,
    "emergency_list": render_emergency_list,
}

TRANSITION_HANDLERS = {
    "language_select": transition_language_select,
    "main_menu": transition_main_menu,
    "situation_list": transition_situation_list,
    "situation_detail": transition_situation_detail,
    "safety_gate": transition_safety_gate,
    "topic_detail": transition_topic_detail,
    "action_steps": transition_action_steps,
    "support_contacts": transition_support_contacts,
    "emergency_list": transition_emergency_list,
}


def render_state(state, session):
    return RENDER_HANDLERS[state](session)


def transition_state(state, session, user_input):
    return TRANSITION_HANDLERS[state](session, user_input)
```

Create `backend/apps/channels/ussd/handler.py`:

```python
from . import menus, sessions

MAX_INVALID_ATTEMPTS = 3


def handle_ussd_request(session_id, phone_number, text):
    session, created = sessions.get_or_create_session(session_id, phone_number)

    if created:
        response_text, ended = menus.render_state(session.state, session)
        sessions.update_session(session, is_active=not ended)
        return _format_response(response_text, ended)

    user_input = text.split("*")[-1] if text else ""
    result = menus.transition_state(session.state, session, user_input)

    if result is None:
        attempts = session.context.get("attempts", 0) + 1
        if attempts >= MAX_INVALID_ATTEMPTS:
            sessions.end_session(session)
            return _format_response(
                menus.get_copy("ussd.too_many_invalid", session.language), True
            )
        sessions.update_session(
            session, context={**session.context, "attempts": attempts}
        )
        response_text, ended = menus.render_state(session.state, session)
        invalid_prefix = menus.get_copy("ussd.invalid_choice", session.language)
        return _format_response(f"{invalid_prefix}\n{response_text}", ended)

    next_state, next_context = result
    session.state = next_state
    session.context = next_context
    response_text, ended = menus.render_state(next_state, session)
    sessions.update_session(
        session,
        state=next_state,
        context=next_context,
        language=session.language,
        is_active=not ended,
    )
    return _format_response(response_text, ended)


def _format_response(text, ended):
    prefix = "END " if ended else "CON "
    return f"{prefix}{text}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python manage.py test apps.channels.ussd.tests.HandleUssdRequestTests -v 2`
Expected: PASS (6 tests)

- [ ] **Step 5: Run the full test module to confirm nothing regressed**

Run: `cd backend && python manage.py test apps.channels -v 2`
Expected: PASS (all tests from Tasks 1-8)

- [ ] **Step 6: Commit**

```bash
git add backend/apps/channels/ussd/menus.py backend/apps/channels/ussd/handler.py backend/apps/channels/ussd/tests.py
git commit -m "feat: add USSD state dispatch and request handler orchestrator"
```

---

### Task 9: Webhook view and URL wiring

**Files:**
- Create: `backend/apps/channels/ussd/views.py`
- Create: `backend/apps/channels/urls.py`
- Modify: `backend/config/urls.py`
- Test: `backend/apps/channels/ussd/tests.py`

**Interfaces:**
- Consumes: `handler.handle_ussd_request` (Task 8)
- Produces: `apps.channels.ussd.views.ussd_callback` (Django view function), URL name `"ussd-callback"` resolving to `api/channels/ussd/`

- [ ] **Step 1: Write the failing test**

Append to `backend/apps/channels/ussd/tests.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.channels.ussd.tests.UssdCallbackViewTests -v 2`
Expected: FAIL — `NoReverseMatch: Reverse for 'ussd-callback' not found`

- [ ] **Step 3: Write minimal implementation**

Create `backend/apps/channels/ussd/views.py`:

```python
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .handler import handle_ussd_request


@csrf_exempt
@require_POST
def ussd_callback(request):
    session_id = request.POST.get("sessionId", "")
    phone_number = request.POST.get("phoneNumber", "")
    text = request.POST.get("text", "")

    response_text = handle_ussd_request(session_id, phone_number, text)
    return HttpResponse(response_text, content_type="text/plain")
```

Create `backend/apps/channels/urls.py`:

```python
from django.urls import path

from .ussd.views import ussd_callback

urlpatterns = [
    path("ussd/", ussd_callback, name="ussd-callback"),
]
```

Modify `backend/config/urls.py` — add a fourth `path(...)` entry after the `api/content/` block, before the closing `]`:

```python
    path(
        "api/channels/",
        include("apps.channels.urls"),
    ),
```

The full `urlpatterns` list should read:

```python
urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "api/rights/",
        include("apps.rights.urls"),
    ),

    path(
        "api/support/",
        include("apps.support.urls"),
    ),

    path(
        "api/content/",
        include("apps.content.urls"),
    ),

    path(
        "api/channels/",
        include("apps.channels.urls"),
    ),
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python manage.py test apps.channels.ussd.tests.UssdCallbackViewTests -v 2`
Expected: PASS (2 tests)

- [ ] **Step 5: Run the entire test suite**

Run: `cd backend && python manage.py test`
Expected: PASS, no failures or errors, across every app (`core`, `rights`, `support`, `channels`, `feedback`, `content`, `campaigns`, `analytics`)

- [ ] **Step 6: Manually verify with curl**

Run (from any terminal, with the dev server running via `cd backend && python manage.py runserver`):

```bash
curl -X POST localhost:8000/api/channels/ussd/ \
  -d "sessionId=manual1&phoneNumber=+256700000000&text="
curl -X POST localhost:8000/api/channels/ussd/ \
  -d "sessionId=manual1&phoneNumber=+256700000000&text=1"
```

Expected: first call returns `CON Welcome to Sauti Yo...` with language options; second call returns `CON 1. Find my rights...` (main menu, since `1` picked English).

- [ ] **Step 7: Commit**

```bash
git add backend/apps/channels/ussd/views.py backend/apps/channels/urls.py backend/config/urls.py backend/apps/channels/ussd/tests.py
git commit -m "feat: wire USSD webhook view and URL routing"
```

---

## Post-plan notes (not part of this implementation, tracked for follow-up)

- Seeding real `Situation`/`RightsTopic`/`SupportService` data (`backend/seed/*.json` are currently empty) is a separate content task — this plan's automated tests use their own fixtures and don't depend on seed data.
- Translated `ChannelContent` rows for non-English chrome are a follow-up content task, not code.
- SMS and Voice channel handlers get their own spec + plan cycles.
- A `prune_ussd_sessions` management command for cleaning up abandoned sessions was explicitly deferred in the spec — not built here.
