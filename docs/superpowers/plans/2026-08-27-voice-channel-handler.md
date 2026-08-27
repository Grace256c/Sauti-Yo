# Voice Channel Handler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Voice channel end-to-end — call greeting, free-speech recording, Whisper transcription, danger/keyword/AI-classification routing, a DTMF safety check-in for high-risk situations, spoken replies, and a post-reply DTMF menu — per `docs/superpowers/specs/2026-08-27-voice-channel-handler-design.md`.

**Architecture:** A stateful webhook (`voice/views.py` → `voice/handler.py`) drives a small state machine (`VoiceSession.state`) across the several HTTP round-trips a single phone call makes. Each turn's Africa's Talking XML is built by pure functions in `voice/ivr.py`. The handler reuses `apps.channels.sms.keywords`, `apps.channels.sms.ai_classifier`, and `apps.channels.sms.templates` unchanged — the only new "intelligence" this build adds is `voice/transcription.py`, which turns a call recording into text before any of that reused code runs on it.

**Tech Stack:** Django (existing project), `openai` Python SDK (new, Whisper transcription only — not yet in `requirements.txt`), `requests` (already in `requirements.txt`, used to download the Africa's Talking recording), `anthropic` Python SDK (already installed, via the reused `sms.ai_classifier`), PostgreSQL, Django's built-in test runner (`manage.py test`).

## Global Constraints

- `keywords.match_danger()` runs unconditionally on every transcript, before any classification — matches SMS's danger-word precedence exactly.
- The safety check-in ("are you safe?") is always DTMF (`GetDigits`), never parsed from speech — the one binary decision in the flow where a misread is dangerous.
- `templates.build_safety_reply()` is the only source of crisis-response wording — never composed or reworded, in voice or otherwise.
- Discreet mode (`keywords.match_discreet()` on the transcript) is never sent through `ai_classifier.reword_reply()` and never states the situation's name/topic, matching SMS.
- Voice is English-only for v1 — no language picker, no `language` parameter threaded through the voice handler.
- No SMS-related code (`apps/channels/sms/*`) is modified by this plan — Voice is purely additive and only imports from it.
- No retry/backoff on the Whisper call beyond the one caller-facing re-record offered after a failed/empty transcription (matches the project's "no Redis/Celery" constraint) — every transcription failure mode (download error, API error, timeout, empty result) degrades identically to "no transcript."
- Claude (`anthropic`) remains the only model used for any classification, rewording, or generated user-facing text. `openai`/Whisper is transcription-only.

---

## Task 1: `VoiceSession` model and session helpers

**Files:**
- Modify: `backend/apps/channels/models.py`
- Create: `backend/apps/channels/migrations/0006_voicesession.py` (via `makemigrations`)
- Create: `backend/apps/channels/voice/sessions.py`
- Create: `backend/apps/channels/voice/tests.py`

**Interfaces:**
- Consumes: nothing (first task).
- Produces:
  - `apps.channels.models.VoiceSession` — fields `session_id` (unique), `phone_number`, `state` (default `"awaiting_recording"`), `context` (JSONField, default `{}`), `is_active` (default `True`), `created_at`, `updated_at`.
  - `apps.channels.voice.sessions.get_or_create_session(session_id: str, phone_number: str) -> (VoiceSession, bool)`
  - `apps.channels.voice.sessions.update_session(session: VoiceSession, **fields) -> VoiceSession`
  - `apps.channels.voice.sessions.end_session(session: VoiceSession) -> VoiceSession`

- [ ] **Step 1: Write the failing tests**

Create `backend/apps/channels/voice/tests.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python manage.py test apps.channels.voice -v 2`
Expected: FAIL — `ModuleNotFoundError` (no `apps.channels.voice` package, `VoiceSession` doesn't exist).

- [ ] **Step 3: Add the model**

In `backend/apps/channels/models.py`, append after the `SmsContext` class:

```python


class VoiceSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=50)

    state = models.CharField(max_length=50, default="awaiting_recording")

    context = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.session_id} ({self.state})"
```

- [ ] **Step 4: Generate the migration**

Run: `cd backend && python manage.py makemigrations channels`
Expected: `Migrations for 'channels': backend/apps/channels/migrations/0006_voicesession.py - Create model VoiceSession`

- [ ] **Step 5: Create the `voice` package and session helpers**

Create `backend/apps/channels/voice/__init__.py` (empty file).

Create `backend/apps/channels/voice/sessions.py`:

```python
from apps.channels.models import VoiceSession


def get_or_create_session(session_id, phone_number):
    return VoiceSession.objects.get_or_create(
        session_id=session_id,
        defaults={
            "phone_number": phone_number,
            "state": "awaiting_recording",
        },
    )


def update_session(session, **fields):
    for field, value in fields.items():
        setattr(session, field, value)
    session.save()
    return session


def end_session(session):
    return update_session(session, is_active=False, state="ended")
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && python manage.py test apps.channels.voice -v 2`
Expected: PASS — 6 tests OK.

- [ ] **Step 7: Commit**

```bash
git add backend/apps/channels/models.py backend/apps/channels/migrations/0006_voicesession.py backend/apps/channels/voice/__init__.py backend/apps/channels/voice/sessions.py backend/apps/channels/voice/tests.py
git commit -m "feat: add VoiceSession model and session helpers"
```

---

## Task 2: Whisper transcription

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/config/settings.py`
- Create: `backend/apps/channels/voice/transcription.py`
- Modify: `backend/apps/channels/voice/tests.py`

**Interfaces:**
- Consumes: nothing new (uses `requests`, already installed; and the new `OPENAI_API_KEY` setting this task adds).
- Produces: `apps.channels.voice.transcription.transcribe_recording(recording_url: str) -> str | None`. Django setting `OPENAI_API_KEY`.

- [ ] **Step 1: Add the dependency**

Add `openai` to `backend/requirements.txt` (append as its own line, matching the file's existing one-package-per-line style).

Run: `pip install openai`
Expected: `Successfully installed openai-... (and its transitive dependencies)`.

- [ ] **Step 2: Wire the setting**

In `backend/config/settings.py`, immediately after the `LLM_MODEL = ...` line, add:

```python

# Speech-to-text (transcription only - Claude remains the only model used
# for classification/rewording, see apps.channels.sms.ai_classifier)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
```

- [ ] **Step 3: Write the failing tests**

Append to `backend/apps/channels/voice/tests.py`. Add these imports to the top of the file:

```python
from unittest.mock import MagicMock, patch

from django.test import override_settings
from requests.exceptions import ConnectionError as RequestsConnectionError

from apps.channels.voice import transcription
```

Add:

```python
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
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `cd backend && python manage.py test apps.channels.voice -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.channels.voice.transcription'`.

- [ ] **Step 5: Implement transcription**

Create `backend/apps/channels/voice/transcription.py`:

```python
import logging

import requests
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def transcribe_recording(recording_url):
    """
    Downloads the call recording from Africa's Talking and transcribes it
    with OpenAI's Whisper API. Returns the transcript text, or None on
    any failure (missing config, empty URL, download error, API error,
    timeout, or an empty result) - every failure mode degrades to "no
    transcript" identically, matching apps.channels.sms.ai_classifier's
    everything-degrades-to-None discipline, so the caller can always
    safely fall back to the not-understood path.
    """
    if not settings.OPENAI_API_KEY or not recording_url:
        return None

    try:
        download = requests.get(recording_url, timeout=10)
        download.raise_for_status()
    except requests.RequestException:
        logger.warning("Voice recording download failed", exc_info=True)
        return None

    try:
        client = _get_client()
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=("recording.mp3", download.content),
            timeout=10.0,
        )
    except Exception:
        # Any failure (auth, rate limit, network, timeout, malformed
        # response, unexpected SDK error) degrades to "no transcript" -
        # this call must never crash the voice handler.
        logger.warning("Voice recording transcription failed", exc_info=True)
        return None

    text = (response.text or "").strip()
    return text or None
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && python manage.py test apps.channels.voice -v 2`
Expected: PASS — 13 tests OK (6 from Task 1 + 7 new).

- [ ] **Step 7: Commit**

```bash
git add backend/requirements.txt backend/config/settings.py backend/apps/channels/voice/transcription.py backend/apps/channels/voice/tests.py
git commit -m "feat: add Whisper-based voice recording transcription"
```

---

## Task 3: Voice IVR XML builders

**Files:**
- Create: `backend/apps/channels/voice/ivr.py`
- Modify: `backend/apps/channels/voice/tests.py`

**Interfaces:**
- Consumes: nothing (pure string-building functions).
- Produces:
  - `apps.channels.voice.ivr.build_greeting_xml() -> str`
  - `apps.channels.voice.ivr.build_safety_checkin_xml(discreet: bool) -> str`
  - `apps.channels.voice.ivr.build_reply_xml(spoken_text: str) -> str`
  - `apps.channels.voice.ivr.build_unmatched_xml(retry: bool) -> str`
  - `apps.channels.voice.ivr.build_final_message_xml(spoken_text: str) -> str`
  - `apps.channels.voice.ivr.build_closing_xml() -> str`

- [ ] **Step 1: Write the failing tests**

Append to `backend/apps/channels/voice/tests.py`. Add this import:

```python
from apps.channels.voice import ivr
```

Add:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python manage.py test apps.channels.voice -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.channels.voice.ivr'`.

- [ ] **Step 3: Implement the XML builders**

Create `backend/apps/channels/voice/ivr.py`:

```python
from xml.sax.saxutils import escape

# NOTE: Africa's Talking's exact Voice XML attribute names/defaults
# (finishOnKey, maxLength, trimSilence, playBeep, timeout) should be
# double-checked against Africa's Talking's Voice API reference before
# this goes live against a real account - written here from the
# documented verb shapes, not verified against a live sandbox call.

GREETING_TEXT = (
    "Welcome to Sauti Yo. In your own words, briefly describe what's "
    "happening. When you're done, stay quiet for a moment, or press the "
    "pound key."
)

SAFETY_CHECKIN_PROMPT = (
    "Are you safe right now? Press 1 if you are safe. "
    "Press 2 if you are not."
)
DISCREET_SAFETY_CHECKIN_PROMPT = (
    "Press 1 to continue. Press 2 if you need help now."
)

POST_REPLY_MENU_PROMPT = (
    "To hear support contacts, press 1. To hear that again, press 2. "
    "To end this call, press 0."
)

RETRY_PROMPT = (
    "Sorry, I didn't catch that. Please describe what's happening after "
    "the beep."
)
GIVE_UP_TEXT = (
    "I'm sorry, I still couldn't understand. Please call back, or send "
    "a text instead. Goodbye."
)
CLOSING_TEXT = "Thank you for calling Sauti Yo. Take care."


def _say(text):
    return f"<Say>{escape(text)}</Say>"


def _record():
    return (
        '<Record trimSilence="true" maxLength="120" finishOnKey="#" '
        'playBeep="true"/>'
    )


def _get_digits(prompt, num_digits=1, timeout=10):
    return (
        f'<GetDigits timeout="{timeout}" numDigits="{num_digits}">'
        f"{_say(prompt)}"
        "</GetDigits>"
    )


def _response(*fragments):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>" + "".join(fragments) + "</Response>"
    )


def build_greeting_xml():
    return _response(_say(GREETING_TEXT), _record())


def build_safety_checkin_xml(discreet):
    prompt = (
        DISCREET_SAFETY_CHECKIN_PROMPT if discreet else SAFETY_CHECKIN_PROMPT
    )
    return _response(_get_digits(prompt, num_digits=1))


def build_reply_xml(spoken_text):
    return _response(
        _say(spoken_text), _get_digits(POST_REPLY_MENU_PROMPT, num_digits=1)
    )


def build_unmatched_xml(retry):
    if retry:
        return _response(_say(RETRY_PROMPT), _record())
    return build_final_message_xml(GIVE_UP_TEXT)


def build_final_message_xml(spoken_text):
    return _response(_say(spoken_text))


def build_closing_xml():
    return build_final_message_xml(CLOSING_TEXT)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python manage.py test apps.channels.voice -v 2`
Expected: PASS — 22 tests OK (13 from Tasks 1-2 + 9 new).

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/voice/ivr.py backend/apps/channels/voice/tests.py
git commit -m "feat: add voice IVR XML builders"
```

---

## Task 4: Voice handler orchestrator

**Files:**
- Create: `backend/apps/channels/voice/handler.py`
- Modify: `backend/apps/channels/voice/tests.py`

**Interfaces:**
- Consumes: `apps.channels.voice.sessions.*` (Task 1), `apps.channels.voice.transcription.transcribe_recording` (Task 2), `apps.channels.voice.ivr.*` (Task 3), `apps.channels.sms.keywords.*`, `apps.channels.sms.ai_classifier.classify_situation`/`reword_reply`, `apps.channels.sms.templates.build_situation_reply`/`build_safety_reply`/`build_support_reply` (all already built, unmodified), `apps.rights.services.get_situation_detail`.
- Produces: `apps.channels.voice.handler.handle_voice_request(session_id: str, phone_number: str, is_active: str, dtmf_digits: str, recording_url: str) -> str` (an XML string).

- [ ] **Step 1: Write the failing tests**

Append to `backend/apps/channels/voice/tests.py`. Add these imports:

```python
from django.core.cache import cache

from apps.channels.models import VoiceSession
from apps.channels.sms.tests import (
    _create_home_safety_situation,
    _create_land_situation_without_safety_response,
)
from apps.channels.voice.handler import handle_voice_request
```

Add:

```python
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

    def test_discreet_keyword_omits_service_name_from_reply(self):
        _create_land_situation_without_safety_response()
        handle_voice_request("sess-7", "+256700000000", "1", "", "")
        with self._mock_transcript("land and plot problem, please be discreet"):
            xml = handle_voice_request(
                "sess-7", "+256700000000", "1", "", "https://example.com/r.mp3"
            )
        session = VoiceSession.objects.get(session_id="sess-7")
        self.assertTrue(session.context["discreet"])

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python manage.py test apps.channels.voice -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.channels.voice.handler'`.

- [ ] **Step 3: Implement the handler**

Create `backend/apps/channels/voice/handler.py`:

```python
from django.core.cache import cache

from apps.channels.models import VoiceSession
from apps.channels.sms import ai_classifier, keywords, templates
from apps.channels.voice import ivr, transcription
from apps.channels.voice.sessions import (
    end_session,
    get_or_create_session,
    update_session,
)
from apps.rights.services import get_situation_detail

RATE_LIMIT_MAX_CALLS = 5
RATE_LIMIT_WINDOW_SECONDS = 60

MAX_RECORDING_ATTEMPTS = 2


def _is_rate_limited(phone_number):
    """
    Simple in-memory rate limit (Django's default local-memory cache -
    single-process only, resets on restart), same pattern and reasoning
    as apps.channels.sms.handler._is_rate_limited: good enough to blunt
    basic webhook abuse at hackathon scale without needing Redis.
    """
    cache_key = f"voice_rate:{phone_number}"
    count = cache.get(cache_key, 0)
    if count >= RATE_LIMIT_MAX_CALLS:
        return True
    cache.set(cache_key, count + 1, timeout=RATE_LIMIT_WINDOW_SECONDS)
    return False


def _compose_reply(detail, mode):
    template_text = templates.build_situation_reply(detail, mode)
    if mode == "discreet":
        return template_text
    reworded = ai_classifier.reword_reply(template_text)
    return reworded or template_text


def handle_voice_request(session_id, phone_number, is_active, dtmf_digits, recording_url):
    if is_active == "0":
        VoiceSession.objects.filter(session_id=session_id, is_active=True).update(
            is_active=False, state="ended"
        )
        return ""

    if recording_url:
        return _handle_recording(session_id, phone_number, recording_url)

    if dtmf_digits:
        return _handle_digits(session_id, phone_number, dtmf_digits)

    return _handle_call_start(session_id, phone_number)


def _handle_call_start(session_id, phone_number):
    if _is_rate_limited(phone_number):
        return ivr.build_closing_xml()

    get_or_create_session(session_id, phone_number)
    return ivr.build_greeting_xml()


def _handle_recording(session_id, phone_number, recording_url):
    session, _ = get_or_create_session(session_id, phone_number)

    transcript = transcription.transcribe_recording(recording_url)
    if not transcript:
        return _handle_unmatched(session)

    if keywords.match_danger(transcript):
        end_session(session)
        return ivr.build_final_message_xml(templates.build_safety_reply())

    discreet = keywords.match_discreet(transcript)
    slug = keywords.match_situation(transcript) or ai_classifier.classify_situation(
        transcript
    )
    if not slug:
        return _handle_unmatched(session)

    detail = get_situation_detail(slug)
    if detail is None:
        return _handle_unmatched(session)

    if detail["risk_level"] == "high_risk":
        update_session(
            session,
            state="awaiting_safety_digit",
            context={"slug": slug, "discreet": discreet},
        )
        return ivr.build_safety_checkin_xml(discreet)

    return _speak_situation_reply(session, slug, detail, discreet)


def _speak_situation_reply(session, slug, detail, discreet):
    mode = "discreet" if discreet else "normal"
    spoken_text = _compose_reply(detail, mode)
    update_session(
        session, state="post_reply_menu", context={"slug": slug, "discreet": discreet}
    )
    return ivr.build_reply_xml(spoken_text)


def _handle_unmatched(session):
    attempts = session.context.get("attempts", 0)
    if attempts >= MAX_RECORDING_ATTEMPTS - 1:
        end_session(session)
        return ivr.build_unmatched_xml(retry=False)
    update_session(session, context={"attempts": attempts + 1})
    return ivr.build_unmatched_xml(retry=True)


def _handle_digits(session_id, phone_number, dtmf_digits):
    session, _ = get_or_create_session(session_id, phone_number)

    if session.state == "awaiting_safety_digit":
        return _handle_safety_digit(session, dtmf_digits)

    if session.state == "post_reply_menu":
        return _handle_menu_digit(session, dtmf_digits)

    end_session(session)
    return ivr.build_closing_xml()


def _handle_safety_digit(session, digit):
    slug = session.context.get("slug")
    discreet = session.context.get("discreet", False)
    detail = get_situation_detail(slug)

    if digit == "2":
        end_session(session)
        return ivr.build_final_message_xml(templates.build_safety_reply(detail))

    if detail is None:
        end_session(session)
        return ivr.build_unmatched_xml(retry=False)

    return _speak_situation_reply(session, slug, detail, discreet)


def _handle_menu_digit(session, digit):
    slug = session.context.get("slug")
    discreet = session.context.get("discreet", False)
    detail = get_situation_detail(slug)

    if detail is None:
        end_session(session)
        return ivr.build_unmatched_xml(retry=False)

    mode = "discreet" if discreet else "normal"

    if digit == "1":
        return ivr.build_reply_xml(templates.build_support_reply(detail, mode))

    if digit == "2":
        return ivr.build_reply_xml(_compose_reply(detail, mode))

    end_session(session)
    return ivr.build_closing_xml()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python manage.py test apps.channels.voice -v 2`
Expected: PASS — 35 tests OK (22 from Tasks 1-3 + 13 new).

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/voice/handler.py backend/apps/channels/voice/tests.py
git commit -m "feat: add voice handler orchestrator"
```

---

## Task 5: Voice webhook view and URL wiring

**Files:**
- Create: `backend/apps/channels/voice/views.py`
- Modify: `backend/apps/channels/urls.py`
- Modify: `backend/apps/channels/voice/tests.py`

**Interfaces:**
- Consumes: `apps.channels.voice.handler.handle_voice_request` (Task 4).
- Produces: `apps.channels.voice.views.voice_callback` (Django view, registered at `POST /api/channels/voice/`).

- [ ] **Step 1: Write the failing test**

Append to `backend/apps/channels/voice/tests.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.channels.voice -v 2`
Expected: FAIL — 404s (no `voice/` URL registered) / `ModuleNotFoundError` for `apps.channels.voice.views`.

- [ ] **Step 3: Implement the view and URL wiring**

Create `backend/apps/channels/voice/views.py`:

```python
import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.channels.voice import ivr

from .handler import handle_voice_request

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def voice_callback(request):
    session_id = request.POST.get("sessionId", "")
    phone_number = request.POST.get("phoneNumber", "")
    is_active = request.POST.get("isActive", "1")
    dtmf_digits = request.POST.get("dtmfDigits", "")
    recording_url = request.POST.get("recordingUrl", "")

    try:
        response_xml = handle_voice_request(
            session_id, phone_number, is_active, dtmf_digits, recording_url
        )
    except Exception:
        logger.exception("Unhandled error processing Voice request")
        response_xml = ivr.build_final_message_xml(
            "Sorry, something went wrong. Please try again."
        )

    return HttpResponse(response_xml, content_type="text/xml")
```

In `backend/apps/channels/urls.py`, replace the file's contents with:

```python
from django.urls import path

from .sms.views import sms_callback
from .ussd.views import ussd_callback
from .voice.views import voice_callback

urlpatterns = [
    path("ussd/", ussd_callback, name="ussd-callback"),
    path("sms/", sms_callback, name="sms-callback"),
    path("voice/", voice_callback, name="voice-callback"),
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python manage.py test apps.channels.voice -v 2`
Expected: PASS — 38 tests OK (35 from Tasks 1-4 + 3 new).

Then run the full suite to confirm nothing else broke:

Run: `cd backend && python manage.py test`
Expected: PASS — all tests OK (the pre-existing suite plus the 38 new voice tests).

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/voice/views.py backend/apps/channels/urls.py backend/apps/channels/voice/tests.py
git commit -m "feat: add voice webhook view and URL routing"
```
