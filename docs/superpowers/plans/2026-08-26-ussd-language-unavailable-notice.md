# USSD Unavailable-Language Notice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When a USSD user selects Luganda, Kiswahili, or Runyankole at the language picker, show a short "not available yet" notice and stay on the picker, instead of silently setting that language and continuing in English.

**Architecture:** Only `"1"` (English) sets `session.language` and proceeds to `main_menu`. `"2"`/`"3"`/`"4"` return a *valid* transition back to `language_select` with a `context` flag, so `render_language_select` can show the notice — this is not the invalid-input path, so it never touches `handler.py`'s 3-strikes counter and needs no `handler.py` changes at all.

**Tech Stack:** Django, `apps.channels.ussd.menus`, existing `TestCase`-based suite (`manage.py test`).

## Global Constraints

- No changes to `handler.py` — the fix is contained entirely to `transition_language_select`/`render_language_select` in `menus.py`, because returning a valid `(next_state, context)` tuple (not `None`) for `"2"`/`"3"`/`"4"` already keeps this off the invalid-attempts path with zero extra code.
- Selecting an unavailable language must NOT set `session.language` — it stays whatever it was before (empty on a fresh session).
- New copy goes through the existing `DEFAULT_COPY`/`get_copy` mechanism, same as every other string in this file — no hardcoded text outside that dict.
- Screen budget: this screen doesn't use `_chunked_screen` (it's always a single short screen); adding the notice keeps total length well under the ~160/182 char limits, no chunking needed.

---

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `backend/apps/channels/ussd/menus.py` | Modify | `DEFAULT_COPY` key + `render_language_select`/`transition_language_select` |
| `backend/apps/channels/ussd/tests.py` | Modify | Update/split `LanguageSelectTests` |

---

### Task 1: Unavailable-language notice

**Files:**
- Modify: `backend/apps/channels/ussd/menus.py`
- Modify: `backend/apps/channels/ussd/tests.py`

**Interfaces:**
- Consumes: `get_copy` (pre-existing, unchanged)
- Produces: no new public functions — `render_language_select`/`transition_language_select` keep their existing signatures, only their bodies change; downstream code (`RENDER_HANDLERS`/`TRANSITION_HANDLERS` dispatch tables) needs no changes since these function names/signatures are unchanged.

- [ ] **Step 1: Write the failing tests**

Find `LanguageSelectTests` in `backend/apps/channels/ussd/tests.py`. It currently reads:

```python
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
```

Replace the whole class with:

```python
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

    def test_transition_unavailable_language_stays_on_picker_with_notice(self):
        for digit in ("2", "3", "4"):
            session = UssdSession(state="language_select", language="", context={})
            next_state, context = menus.transition_language_select(session, digit)
            self.assertEqual(next_state, "language_select")
            self.assertEqual(context, {"unavailable_notice": True})
            self.assertEqual(session.language, "")

    def test_transition_rejects_invalid_choice(self):
        session = UssdSession(state="language_select", language="", context={})
        result = menus.transition_language_select(session, "9")
        self.assertIsNone(result)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && /Users/admin/Desktop/Sauti\ Yo/Sauti-Yo/.venv/bin/python manage.py test apps.channels.ussd.tests.LanguageSelectTests -v 2`
Expected: FAIL — `test_render_shows_unavailable_notice_when_flagged` fails because the notice never appears (old `render_language_select` ignores `context`); `test_transition_unavailable_language_stays_on_picker_with_notice` fails because the old `transition_language_select` still sets `session.language` and returns `"main_menu"` for `"2"`/`"3"`/`"4"`.

- [ ] **Step 3: Add the new copy key**

In `backend/apps/channels/ussd/menus.py`, find the `DEFAULT_COPY` dict and add this key (near `"ussd.language_prompt"`):

```python
    "ussd.language_unavailable": (
        "That language isn't available yet. Please choose English for now."
    ),
```

- [ ] **Step 4: Update `render_language_select` and `transition_language_select`**

Find (current code):

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
```

Replace with:

```python
def render_language_select(session):
    body = get_copy("ussd.welcome", session.language)
    prompt = get_copy("ussd.language_prompt", session.language)
    if session.context.get("unavailable_notice"):
        notice = get_copy("ussd.language_unavailable", session.language)
        return f"{notice}\n\n{body}\n{prompt}", False
    return f"{body}\n{prompt}", False


def transition_language_select(session, user_input):
    mapping = {"1": "en", "2": "lg", "3": "sw", "4": "nyn"}
    language = mapping.get(user_input)
    if language is None:
        return None
    if language != "en":
        return "language_select", {"unavailable_notice": True}
    session.language = language
    return "main_menu", {}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && /Users/admin/Desktop/Sauti\ Yo/Sauti-Yo/.venv/bin/python manage.py test apps.channels.ussd.tests.LanguageSelectTests -v 2`
Expected: PASS (5 tests)

- [ ] **Step 6: Run the full test suite**

Run: `cd backend && /Users/admin/Desktop/Sauti\ Yo/Sauti-Yo/.venv/bin/python manage.py test`
Expected: PASS, no failures anywhere in the project. Nothing outside `LanguageSelectTests` should be affected — no other test exercises `transition_language_select`/`render_language_select` with inputs other than `"1"` or an invalid digit (`HandleUssdRequestTests` and similar handler-level tests always send `"1"` for the language step).

- [ ] **Step 7: Manually verify via curl**

With the dev server running (`cd backend && /Users/admin/Desktop/Sauti\ Yo/Sauti-Yo/.venv/bin/python manage.py runserver`), from another terminal:

```bash
curl -X POST localhost:8000/api/channels/ussd/ \
  -d "sessionId=lang-check&phoneNumber=+256700000000&text="
curl -X POST localhost:8000/api/channels/ussd/ \
  -d "sessionId=lang-check&phoneNumber=+256700000000&text=2"
```

Expected: the second call returns `CON That language isn't available yet. Please choose English for now.` followed by the welcome text and the four language options again — not the main menu.

- [ ] **Step 8: Commit**

```bash
git add backend/apps/channels/ussd/menus.py backend/apps/channels/ussd/tests.py
git commit -m "feat: show notice for unavailable USSD language selections"
```
