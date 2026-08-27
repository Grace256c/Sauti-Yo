# Voice Direct-Connect to Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a voice caller press a digit to be connected directly to a support number, everywhere one is currently spoken — the crisis/danger-word safety reply and the post-reply support-contacts menu — per `docs/superpowers/specs/2026-08-27-voice-direct-connect-design.md`.

**Architecture:** `voice/ivr.py` gains two new XML builders (a safety-reply-plus-connect-offer prompt, and a `<Dial>`-plus-fallback response). `voice/handler.py` gains one new session state (`awaiting_crisis_connect_digit`) that all three existing "speak the safety reply and end the call" code paths are refactored to go through via one shared helper, plus a new digit "3" in the post-reply menu. No changes to `apps/channels/sms/*` or `apps/rights/*`.

**Tech Stack:** Django (existing project), Africa's Talking Voice XML `<Dial>` verb (new to this codebase, same string-building approach as the existing `<Say>`/`<Record>`/`<GetDigits>` verbs in `ivr.py`).

## Global Constraints

- `record="false"` always on `<Dial>` — no connected call is ever recorded.
- Only the single "primary" number is ever dialed (first support service with a phone number for a known situation, or the first `is_emergency_service=True` `SupportService` when no situation is known) — never multiple numbers, never `sequential`.
- The safety reply text itself (`templates.build_safety_reply()`) is always spoken in full before any connect option is offered — this plan only changes what happens *after* that message.
- Pressing anything other than an explicit "1" after a connect offer — including no digit at all — ends the call exactly as it did before this plan, no extra friction for a caller who wants to hang up.
- No new file is created — both tasks modify existing files (`voice/ivr.py`, `voice/handler.py`, `voice/tests.py`).
- `apps.channels.sms.*` and `apps.rights.*` are not modified — only `apps.support.models.SupportService` is newly imported directly into `voice/handler.py`, mirroring the exact pattern `sms/templates.py.build_support_reply()` already uses for its no-situation emergency-list case.

---

## Task 1: IVR XML for the connect offer and the dial itself

**Files:**
- Modify: `backend/apps/channels/voice/ivr.py`
- Modify: `backend/apps/channels/voice/tests.py`

**Interfaces:**
- Consumes: nothing new (pure string-building, same as the rest of `ivr.py`).
- Produces:
  - `apps.channels.voice.ivr.build_safety_reply_with_connect_xml(safety_text: str) -> str`
  - `apps.channels.voice.ivr.build_dial_xml(phone_number: str) -> str`
  - `POST_REPLY_MENU_PROMPT` updated to mention the new option (existing callers of `build_reply_xml` are unaffected — same function, new copy).

- [ ] **Step 1: Write the failing tests**

Append to the existing `IvrXmlTests` class in `backend/apps/channels/voice/tests.py` (no new imports needed — `ivr` is already imported):

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python manage.py test apps.channels.voice.tests.IvrXmlTests -v 2`
Expected: FAIL — `AttributeError: module 'apps.channels.voice.ivr' has no attribute 'build_safety_reply_with_connect_xml'`.

- [ ] **Step 3: Implement the new XML builders**

In `backend/apps/channels/voice/ivr.py`, update `POST_REPLY_MENU_PROMPT` and add the new constants/functions. Replace:

```python
POST_REPLY_MENU_PROMPT = (
    "To hear support contacts, press 1. To hear that again, press 2. "
    "To end this call, press 0."
)
```

with:

```python
POST_REPLY_MENU_PROMPT = (
    "To hear support contacts, press 1. To hear that again, press 2. "
    "To be connected now, press 3. To end this call, press 0."
)

CRISIS_CONNECT_PROMPT = (
    "Press 1 to connect to that support line now. Stay on the line to "
    "end the call."
)

CONNECT_FAILED_TEXT_TEMPLATE = (
    "That number isn't answering right now. You can reach them "
    "directly at {phone_number}."
)
```

Then, after the existing `_get_digits` function, add:

```python
def _dial(phone_number):
    return (
        f'<Dial phoneNumbers="{escape(phone_number)}" record="false" '
        'maxDuration="300"/>'
    )
```

Finally, after `build_reply_xml`, add the two new public functions:

```python
def build_safety_reply_with_connect_xml(safety_text):
    return _response(
        _say(safety_text), _get_digits(CRISIS_CONNECT_PROMPT, num_digits=1)
    )


def build_dial_xml(phone_number):
    fallback_text = CONNECT_FAILED_TEXT_TEMPLATE.format(
        phone_number=phone_number
    )
    return _response(_dial(phone_number), _say(fallback_text))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python manage.py test apps.channels.voice -v 2`
Expected: PASS — all existing voice tests plus 4 new ones (verify the exact new count against the current total by reading the test runner's summary line — do not hardcode an expected number here, since Task 2 of the base voice plan already left this suite in flux across earlier fix rounds).

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/voice/ivr.py backend/apps/channels/voice/tests.py
git commit -m "feat: add IVR XML for connecting callers directly to support"
```

---

## Task 2: Handler support for the connect option

**Files:**
- Modify: `backend/apps/channels/voice/handler.py`
- Modify: `backend/apps/channels/voice/tests.py`

**Interfaces:**
- Consumes: `apps.channels.voice.ivr.build_safety_reply_with_connect_xml`, `apps.channels.voice.ivr.build_dial_xml` (Task 1); `apps.support.models.SupportService` (new import, read-only query, mirrors `apps.channels.sms.templates.build_support_reply`'s existing no-detail case).
- Produces: `apps.channels.voice.handler._primary_support_phone_number(detail: dict | None) -> str | None` (internal helper, but named here since Task 2's tests call it indirectly through `handle_voice_request` and directly in one unit test).

- [ ] **Step 1: Write the failing tests**

Append to `backend/apps/channels/voice/tests.py`. Add this import at the top of the file (merge into the existing `apps.channels.voice.handler` import line if there is one, otherwise add a new line):

```python
from apps.channels.voice.handler import _primary_support_phone_number, handle_voice_request
```

Add this fixture helper near the top of the file (module level, alongside where other test helpers would go — or as a local import if `apps.support.models` isn't already imported):

```python
from apps.support.models import SupportService
```

Add a new test class:

```python
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

    def test_danger_words_offer_connect_instead_of_ending_immediately(self):
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python manage.py test apps.channels.voice.tests.DirectConnectTests -v 2`
Expected: FAIL — `ImportError: cannot import name '_primary_support_phone_number'`.

- [ ] **Step 3: Implement the handler changes**

In `backend/apps/channels/voice/handler.py`, add the import at the top (alongside the existing `apps.rights.services` import):

```python
from apps.support.models import SupportService
```

Add `_primary_support_phone_number` after `_compose_reply`:

```python
def _primary_support_phone_number(detail):
    if detail is not None:
        for topic in detail["rights_topics"]:
            for service in topic["support_services"]:
                if service.get("phone_number"):
                    return service["phone_number"]
        return None
    service = (
        SupportService.objects.filter(is_emergency_service=True, is_active=True)
        .order_by("name")
        .values("phone_number")
        .first()
    )
    return service["phone_number"] if service else None
```

Add `_offer_crisis_connect` right after it:

```python
def _offer_crisis_connect(session, detail):
    update_session(
        session,
        state="awaiting_crisis_connect_digit",
        context={"slug": detail["slug"] if detail is not None else None},
    )
    return ivr.build_safety_reply_with_connect_xml(
        templates.build_safety_reply(detail)
    )
```

Replace the danger-word branch in `_handle_recording` — change:

```python
    if keywords.match_danger(transcript):
        end_session(session)
        return ivr.build_final_message_xml(templates.build_safety_reply())
```

to:

```python
    if keywords.match_danger(transcript):
        return _offer_crisis_connect(session, None)
```

In `_handle_safety_digit`, replace the `digit == "2"` branch — change:

```python
    if digit == "2":
        end_session(session)
        return ivr.build_final_message_xml(templates.build_safety_reply(detail))
```

to:

```python
    if digit == "2":
        return _offer_crisis_connect(session, detail)
```

And replace the fail-closed branch at the bottom of the same function — change:

```python
    attempts = session.context.get("safety_check_attempts", 0)
    if attempts >= MAX_SAFETY_CHECK_ATTEMPTS - 1:
        end_session(session)
        return ivr.build_final_message_xml(templates.build_safety_reply(detail))
```

to:

```python
    attempts = session.context.get("safety_check_attempts", 0)
    if attempts >= MAX_SAFETY_CHECK_ATTEMPTS - 1:
        return _offer_crisis_connect(session, detail)
```

Add the new digit handler after `_handle_safety_digit`:

```python
def _handle_crisis_connect_digit(session, digit):
    slug = session.context.get("slug")
    detail = get_situation_detail(slug) if slug else None

    if digit == "1":
        phone = _primary_support_phone_number(detail)
        end_session(session)
        if phone:
            return ivr.build_dial_xml(phone)
        return ivr.build_closing_xml()

    end_session(session)
    return ivr.build_closing_xml()
```

In `_handle_digits`, add the new state branch — change:

```python
def _handle_digits(session_id, phone_number, dtmf_digits):
    session, _ = get_or_create_session(session_id, phone_number)

    if session.state == "awaiting_safety_digit":
        return _handle_safety_digit(session, dtmf_digits)

    if session.state == "post_reply_menu":
        return _handle_menu_digit(session, dtmf_digits)

    end_session(session)
    return ivr.build_closing_xml()
```

to:

```python
def _handle_digits(session_id, phone_number, dtmf_digits):
    session, _ = get_or_create_session(session_id, phone_number)

    if session.state == "awaiting_safety_digit":
        return _handle_safety_digit(session, dtmf_digits)

    if session.state == "post_reply_menu":
        return _handle_menu_digit(session, dtmf_digits)

    if session.state == "awaiting_crisis_connect_digit":
        return _handle_crisis_connect_digit(session, dtmf_digits)

    end_session(session)
    return ivr.build_closing_xml()
```

In `handle_voice_request`, extend the GetDigits-timeout state tuple — change:

```python
        if existing.state in ("awaiting_safety_digit", "post_reply_menu"):
```

to:

```python
        if existing.state in (
            "awaiting_safety_digit",
            "post_reply_menu",
            "awaiting_crisis_connect_digit",
        ):
```

Finally, in `_handle_menu_digit`, add the digit "3" branch before the final else — change:

```python
    if digit == "2":
        return ivr.build_reply_xml(_compose_reply(detail, mode))

    end_session(session)
    return ivr.build_closing_xml()
```

to:

```python
    if digit == "2":
        return ivr.build_reply_xml(_compose_reply(detail, mode))

    if digit == "3":
        phone = _primary_support_phone_number(detail)
        if phone:
            end_session(session)
            return ivr.build_dial_xml(phone)
        return ivr.build_reply_xml(templates.build_support_reply(detail, mode))

    end_session(session)
    return ivr.build_closing_xml()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python manage.py test apps.channels.voice -v 2`
Expected: PASS — every existing voice test still passes, plus the new `DirectConnectTests` cases.

Then run the full suite to confirm nothing else broke:

Run: `cd backend && python manage.py test`
Expected: PASS — full project suite green, same as before this task (no SMS/USSD/other-app test should be affected, since only `voice/*` files changed).

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/voice/handler.py backend/apps/channels/voice/tests.py
git commit -m "feat: connect voice callers directly to support numbers"
```
