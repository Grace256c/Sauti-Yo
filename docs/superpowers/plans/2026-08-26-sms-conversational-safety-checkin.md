# SMS Conversational Safety Check-In and Reply Rewording Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a one-shot "are you safe right now?" check-in for high-risk situations (routing "not safe" answers to the existing verbatim `SafetyResponse` path, never AI-composed), and warmth-only AI rewording of the normal-mode situation reply with a fact-preservation check and template-text fallback on any failure.

**Architecture:** `SmsContext` gains one field, `pending_safety_check`. `keywords.match_not_safe_answer()` recognizes "not safe" signals. `ai_classifier.reword_reply()` rephrases an already-built template string without changing its facts, validated by checking every phone number in the original still appears in the output. `handler.py` gets the check-in trigger (in `_reply_to_situation`) and two checkpoints for resolving a pending check (one early, right after the danger-word check, so "unsafe" — which is also a `home-safety` keyword — still resolves as a safety answer; one late, after every other branch has had a chance to match, so a genuine topic-switch message isn't swallowed as a stale answer).

**Tech Stack:** Same as the already-shipped SMS channel and its AI classification fallback — `anthropic` Python SDK, Claude Haiku, Django.

## Global Constraints

- `match_danger()` keeps its unconditional, first-checked position in the match order and its behavior is completely unchanged by this plan.
- `build_safety_reply()` is never called with AI-composed input and its own behavior is unchanged — it still returns the verbatim `SafetyResponse` message.
- The AI rewording step (`ai_classifier.reword_reply`) is given only the already-built template string, never raw DB fields — it may only rephrase, never assemble facts itself.
- Discreet-mode replies are never reworded — `_compose_situation_reply` returns the template text unchanged whenever `mode == "discreet"`.
- Every phone number present in the original template text must still be present verbatim in a reworded reply, or `reword_reply()` discards it and returns `None`. Every other failure mode (missing `LLM_API_KEY`, empty input, API error) also returns `None`.
- No automated test calls the real Anthropic API. Every test mocks the client.
- `pending_safety_check` is cleared every time it's resolved, on every path that resolves it (including the danger-word branch, which resolves it implicitly by answering the underlying question) — never left `True` after a check-in has, in effect, been answered.
- The check-in only triggers for a *new* topic (`SmsContext.last_situation_slug` doesn't already equal the newly-resolved slug, using the same staleness-aware lookup the follow-up window already uses) whose `risk_level == "high_risk"` — never on every message, never for standard-risk situations.

---

## Task 1: `SmsContext.pending_safety_check` and `keywords.match_not_safe_answer`

**Files:**
- Modify: `backend/apps/channels/models.py`
- Create: `backend/apps/channels/migrations/0005_smscontext_pending_safety_check.py` (via `makemigrations`)
- Modify: `backend/apps/channels/sms/keywords.py`
- Modify: `backend/apps/channels/sms/tests.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `apps.channels.models.SmsContext.pending_safety_check` (`BooleanField`, default `False`); `apps.channels.sms.keywords.match_not_safe_answer(text: str) -> bool`.

- [ ] **Step 1: Write the failing tests**

Append to `backend/apps/channels/sms/tests.py`. First, ensure `match_not_safe_answer` is imported alongside the other `keywords` imports at the top of the file (merge into the existing `from apps.channels.sms.keywords import (...)` line rather than adding a new one):

```python
from apps.channels.sms.keywords import (
    match_danger,
    match_discreet,
    match_followup,
    match_help,
    match_not_safe_answer,
    match_situation,
)
```

Add to `SmsContextModelTests`:

```python
    def test_pending_safety_check_defaults_to_false(self):
        context = SmsContext.objects.create(
            phone_number="+256700000000", last_situation_slug="home-safety"
        )
        self.assertFalse(context.pending_safety_check)
```

Add a new test class:

```python
class MatchNotSafeAnswerTests(TestCase):
    def test_matches_no(self):
        self.assertTrue(match_not_safe_answer("no"))

    def test_matches_unsafe(self):
        self.assertTrue(match_not_safe_answer("unsafe"))

    def test_matches_not_safe_phrase(self):
        self.assertTrue(match_not_safe_answer("not safe"))

    def test_matches_danger_word(self):
        self.assertTrue(match_not_safe_answer("there's a weapon here"))

    def test_false_for_yes(self):
        self.assertFalse(match_not_safe_answer("yes"))

    def test_false_for_okay(self):
        self.assertFalse(match_not_safe_answer("I'm okay"))

    def test_does_not_false_positive_on_know(self):
        self.assertFalse(match_not_safe_answer("I don't know what to do"))

    def test_does_not_false_positive_on_info(self):
        self.assertFalse(match_not_safe_answer("send me more info please"))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: FAIL — `ImportError: cannot import name 'match_not_safe_answer'` (and `SmsContextModelTests.test_pending_safety_check_defaults_to_false` would fail separately once the import error is fixed, since the field doesn't exist yet — fix both in this task before re-running).

- [ ] **Step 3: Add the model field**

In `backend/apps/channels/models.py`, add `pending_safety_check` to `SmsContext`, after the existing `discreet` field:

```python
class SmsContext(models.Model):
    phone_number = models.CharField(max_length=50, unique=True)
    last_situation_slug = models.SlugField()
    discreet = models.BooleanField(default=False)
    pending_safety_check = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.phone_number} -> {self.last_situation_slug}"
```

- [ ] **Step 4: Generate and inspect the migration**

Run: `cd backend && python manage.py makemigrations channels`
Expected: `Migrations for 'channels': backend/apps/channels/migrations/0005_smscontext_pending_safety_check.py - Add field pending_safety_check to smscontext`

Open the generated file and confirm it ONLY adds `pending_safety_check` (an `AddField` operation) — same caution as every prior `SmsContext` migration in this project: if Django also proposes an unrelated `AlterField` on `UssdSession.id` (the pre-existing `AutoField`/`BigAutoField` W042 debt), remove that operation from the generated file before applying it — it's out of scope for this task.

- [ ] **Step 5: Add the keyword matcher**

In `backend/apps/channels/sms/keywords.py`, add after `match_discreet`:

```python
NOT_SAFE_ANSWER_PHRASES = ["not safe", "unsafe", "not okay", "not ok"]


def match_not_safe_answer(text):
    normalized = _normalize(text)
    if match_danger(text):
        return True
    if re.search(r"\bno\b", normalized):
        return True
    return any(phrase in normalized for phrase in NOT_SAFE_ANSWER_PHRASES)
```

- [ ] **Step 6: Apply the migration and run tests**

Run: `cd backend && python manage.py migrate channels && python manage.py test apps.channels.sms -v 2`
Expected: PASS — all tests OK, including the 1 new model test and 8 new `MatchNotSafeAnswerTests`.

- [ ] **Step 7: Commit**

```bash
git add backend/apps/channels/models.py backend/apps/channels/migrations/0005_smscontext_pending_safety_check.py backend/apps/channels/sms/keywords.py backend/apps/channels/sms/tests.py
git commit -m "feat: add pending_safety_check field and not-safe-answer matching"
```

---

## Task 2: AI reply rewording

**Files:**
- Modify: `backend/apps/channels/sms/ai_classifier.py`
- Modify: `backend/apps/channels/sms/tests.py`

**Interfaces:**
- Consumes: nothing new (reuses the existing `_get_client()`/`_client` machinery already in `ai_classifier.py`).
- Produces: `apps.channels.sms.ai_classifier.reword_reply(template_text: str) -> str | None`.

- [ ] **Step 1: Write the failing test**

Append to `backend/apps/channels/sms/tests.py`. Add a new test class (reuse the existing `_mock_text_response` helper already in the file from the classifier tests):

```python
class RewordReplyTests(TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        ai_classifier._client = self.mock_client

    def tearDown(self):
        ai_classifier._client = None

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_reworded_text_when_facts_preserved(self):
        self.mock_client.with_options.return_value.messages.create.return_value = (
            _mock_text_response(
                "I'm sorry you're going through this. Call 116 for free help."
            )
        )
        result = ai_classifier.reword_reply("Sauti 116: Call 116 for help.")
        self.assertEqual(
            result,
            "I'm sorry you're going through this. Call 116 for free help.",
        )

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_none_when_phone_number_dropped(self):
        self.mock_client.with_options.return_value.messages.create.return_value = (
            _mock_text_response("I'm sorry you're going through this.")
        )
        result = ai_classifier.reword_reply("Sauti 116: Call 116 for help.")
        self.assertIsNone(result)

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_none_when_client_raises(self):
        self.mock_client.with_options.return_value.messages.create.side_effect = (
            RuntimeError("boom")
        )
        result = ai_classifier.reword_reply("Some template text")
        self.assertIsNone(result)

    @override_settings(LLM_API_KEY="")
    def test_returns_none_and_skips_call_when_api_key_unset(self):
        result = ai_classifier.reword_reply("Some template text")
        self.assertIsNone(result)
        self.mock_client.with_options.assert_not_called()

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_none_for_empty_template_text(self):
        result = ai_classifier.reword_reply("   ")
        self.assertIsNone(result)
        self.mock_client.with_options.assert_not_called()

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_reworded_text_when_original_has_no_phone_number(self):
        self.mock_client.with_options.return_value.messages.create.return_value = (
            _mock_text_response("I'm here for you.")
        )
        result = ai_classifier.reword_reply("You're not alone in this.")
        self.assertEqual(result, "I'm here for you.")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: FAIL — `AttributeError: module 'apps.channels.sms.ai_classifier' has no attribute 'reword_reply'`.

- [ ] **Step 3: Implement `reword_reply`**

In `backend/apps/channels/sms/ai_classifier.py`, add `import re` to the top-of-file imports (alongside the existing `import logging`), and add the new prompt constant and function after `CLASSIFIER_SYSTEM_PROMPT`:

```python
REWORD_SYSTEM_PROMPT = (
    "You rewrite Sauti Yo SMS replies in a warmer, more conversational "
    "tone. You MUST NOT add, remove, or change any fact, phone number, "
    "name, or instruction in the original message - only rephrase how "
    "it is said. Keep it concise. Reply with ONLY the reworded "
    "message, nothing else."
)
```

```python
def reword_reply(template_text):
    """
    Asks Claude to rephrase an already-composed, verified SMS reply in a
    warmer tone, without changing any fact. Returns the reworded text,
    or None if rewording isn't possible/safe - the caller should send
    the original `template_text` unchanged in that case. Every failure
    mode (missing key, empty input, API error, or the reworded text
    dropping a phone number that was in the original) returns None.
    """
    if not settings.LLM_API_KEY or not template_text.strip():
        return None

    phone_numbers = re.findall(r"\d{3,}", template_text)

    try:
        client = _get_client()
        response = client.with_options(timeout=5.0).messages.create(
            model=MODEL,
            max_tokens=200,
            system=REWORD_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": template_text}],
        )
        reworded = next(
            (block.text for block in response.content if block.type == "text"),
            "",
        ).strip()
    except Exception:
        logger.warning("Reply rewording failed", exc_info=True)
        return None

    if not reworded:
        return None
    for number in phone_numbers:
        if number not in reworded:
            logger.warning(
                "Reworded reply dropped a phone number, discarding"
            )
            return None
    return reworded
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: PASS — all 6 new tests OK, plus every pre-existing test still passing.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/sms/ai_classifier.py backend/apps/channels/sms/tests.py
git commit -m "feat: add fact-preserving AI reply rewording"
```

---

## Task 3: Wire the safety check-in and rewording into the handler

**Files:**
- Modify: `backend/apps/channels/sms/templates.py`
- Modify: `backend/apps/channels/sms/handler.py`
- Modify: `backend/apps/channels/sms/tests.py`

**Interfaces:**
- Consumes: `apps.channels.models.SmsContext.pending_safety_check` (Task 1), `apps.channels.sms.keywords.match_not_safe_answer` (Task 1), `apps.channels.sms.ai_classifier.reword_reply` (Task 2).
- Produces: `apps.channels.sms.templates.SAFETY_CHECKIN_QUESTION` (constant); no change to `handle_sms_request`'s signature or contract.

- [ ] **Step 1: Write the failing tests**

Append to `backend/apps/channels/sms/tests.py`. Add `from django.test import override_settings` to the top-of-file imports if not already present from Task 2 (it will be — don't duplicate). Add a new test class:

```python
@override_settings(LLM_API_KEY="")
class SafetyCheckinTests(TestCase):
    """
    LLM_API_KEY is pinned empty at the class level so every test here is
    safe from hitting the real Anthropic API by default - several of
    these tests exercise paths (a non-high-risk reply, a topic switch,
    a post-danger-word follow-up) that reach reword_reply()/
    classify_situation() without explicitly mocking them. Tests that DO
    need to control the AI's behavior mock it explicitly via @patch,
    which overrides this regardless of the empty key.
    """

    def setUp(self):
        _create_home_safety_situation()
        cache.clear()

    @patch("apps.channels.sms.handler.send_sms")
    def test_new_high_risk_topic_sends_only_checkin_question(self, mock_send):
        handle_sms_request("+256700000000", "my husband beats me")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.SAFETY_CHECKIN_QUESTION)
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertTrue(context.pending_safety_check)
        self.assertEqual(context.last_situation_slug, "home-safety")

    @patch("apps.channels.sms.handler.send_sms")
    def test_non_high_risk_topic_skips_checkin(self, mock_send):
        _create_land_situation_without_safety_response()
        handle_sms_request("+256700000000", "they want to evict me from my land")
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertFalse(context.pending_safety_check)
        message = mock_send.call_args[0][1]
        self.assertNotEqual(message, templates.SAFETY_CHECKIN_QUESTION)

    @patch("apps.channels.sms.handler.ai_classifier.reword_reply")
    @patch("apps.channels.sms.handler.send_sms")
    def test_repeat_message_about_same_pending_topic_does_not_retrigger_checkin(
        self, mock_send, mock_reword
    ):
        mock_reword.return_value = None
        handle_sms_request("+256700000000", "my husband beats me")
        handle_sms_request("+256700000000", "my husband beats me")
        second_message = mock_send.call_args_list[1][0][1]
        self.assertNotEqual(second_message, templates.SAFETY_CHECKIN_QUESTION)

    @patch("apps.channels.sms.handler.ai_classifier.reword_reply")
    @patch("apps.channels.sms.handler.send_sms")
    def test_pending_checkin_answered_unsafe_sends_verbatim_safety_reply(
        self, mock_send, mock_reword
    ):
        handle_sms_request("+256700000000", "my husband beats me")
        handle_sms_request("+256700000000", "unsafe")
        second_message = mock_send.call_args_list[1][0][1]
        self.assertEqual(second_message, "Your safety matters. Call Sauti 116.")
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertFalse(context.pending_safety_check)
        mock_reword.assert_not_called()

    @patch("apps.channels.sms.handler.send_sms")
    def test_pending_checkin_answered_no_sends_verbatim_safety_reply(
        self, mock_send
    ):
        handle_sms_request("+256700000000", "my husband beats me")
        handle_sms_request("+256700000000", "no")
        second_message = mock_send.call_args_list[1][0][1]
        self.assertEqual(second_message, "Your safety matters. Call Sauti 116.")

    @patch("apps.channels.sms.handler.ai_classifier.reword_reply")
    @patch("apps.channels.sms.handler.send_sms")
    def test_pending_checkin_answered_yes_sends_situation_reply(
        self, mock_send, mock_reword
    ):
        mock_reword.return_value = None
        handle_sms_request("+256700000000", "my husband beats me")
        handle_sms_request("+256700000000", "yes")
        second_message = mock_send.call_args_list[1][0][1]
        self.assertIn("Sauti 116 - Child & GBV Helpline", second_message)
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertFalse(context.pending_safety_check)

    @patch("apps.channels.sms.handler.send_sms")
    def test_pending_checkin_answered_with_different_topic_switches_topic(
        self, mock_send
    ):
        _create_problem_at_work_situation()
        handle_sms_request("+256700000000", "my husband beats me")
        handle_sms_request("+256700000000", "I was fired from my job")
        second_message = mock_send.call_args_list[1][0][1]
        self.assertIn("Identify the workplace issue", second_message)
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.last_situation_slug, "problem-at-work")
        self.assertFalse(context.pending_safety_check)

    @patch("apps.channels.sms.handler.send_sms")
    def test_danger_word_while_checkin_pending_still_gets_safety_reply_and_clears_flag(
        self, mock_send
    ):
        handle_sms_request("+256700000000", "my husband beats me")
        handle_sms_request("+256700000000", "there's a weapon here")
        second_message = mock_send.call_args_list[1][0][1]
        self.assertEqual(second_message, "Your safety matters. Call Sauti 116.")
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertFalse(context.pending_safety_check)
        # A follow-up message must not be mis-interpreted as answering a
        # question that, in effect, was already answered.
        handle_sms_request("+256700000000", "yes")
        third_message = mock_send.call_args_list[2][0][1]
        self.assertNotEqual(third_message, "Your safety matters. Call Sauti 116.")

    @patch("apps.channels.sms.handler.ai_classifier.reword_reply")
    @patch("apps.channels.sms.handler.send_sms")
    def test_normal_mode_reply_uses_reworded_text_when_available(
        self, mock_send, mock_reword
    ):
        mock_reword.return_value = "A warmer version of the same message."
        _create_problem_at_work_situation()
        handle_sms_request("+256700000000", "I was fired from my job")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, "A warmer version of the same message.")

    @patch("apps.channels.sms.handler.ai_classifier.reword_reply")
    @patch("apps.channels.sms.handler.send_sms")
    def test_normal_mode_reply_falls_back_to_template_when_reword_fails(
        self, mock_send, mock_reword
    ):
        mock_reword.return_value = None
        _create_problem_at_work_situation()
        handle_sms_request("+256700000000", "I was fired from my job")
        message = mock_send.call_args[0][1]
        self.assertIn("Identify the workplace issue", message)

    @patch("apps.channels.sms.handler.ai_classifier.reword_reply")
    @patch("apps.channels.sms.handler.send_sms")
    def test_discreet_mode_reply_is_never_reworded(self, mock_send, mock_reword):
        _create_problem_at_work_situation()
        handle_sms_request("+256700000000", "I was fired from my job discreet")
        mock_reword.assert_not_called()
```

`_create_problem_at_work_situation` was added in an earlier task (the AI classification fallback plan's Task 1 fix wave) — reuse it, don't redefine it. If it isn't present under that exact name, search the file for the closest existing equivalent and use that instead; do not create a duplicate fixture helper.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: FAIL — `AttributeError: module 'apps.channels.sms.templates' has no attribute 'SAFETY_CHECKIN_QUESTION'` (and further failures once that's fixed, since the handler doesn't implement the check-in flow yet).

- [ ] **Step 3: Add the template constant**

In `backend/apps/channels/sms/templates.py`, add near the other fixed-reply constants (after `DISCREET_STEPS_REPLY`):

```python
SAFETY_CHECKIN_QUESTION = "Are you safe right now? Reply YES or NO."
```

- [ ] **Step 4: Rewrite the handler**

Replace the full contents of `backend/apps/channels/sms/handler.py`:

```python
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone

from apps.channels.africastalking_client import send_sms
from apps.channels.models import SmsContext
from apps.channels.sms import ai_classifier, keywords, templates
from apps.rights.services import get_situation_detail

FOLLOWUP_WINDOW_MINUTES = 10

MAX_SMS_LENGTH = templates.SMS_SEGMENT_BUDGET * 2

RATE_LIMIT_MAX_MESSAGES = 5
RATE_LIMIT_WINDOW_SECONDS = 60


def _is_rate_limited(phone_number):
    """
    Simple in-memory rate limit (Django's default local-memory cache -
    single-process only, resets on restart). Good enough to blunt basic
    webhook abuse at hackathon scale; a distributed limiter needs Redis,
    which this project deliberately doesn't run.
    """
    cache_key = f"sms_rate:{phone_number}"
    count = cache.get(cache_key, 0)
    if count >= RATE_LIMIT_MAX_MESSAGES:
        return True
    cache.set(cache_key, count + 1, timeout=RATE_LIMIT_WINDOW_SECONDS)
    return False


def _send(phone_number, message):
    if len(message) > MAX_SMS_LENGTH:
        message = message[: MAX_SMS_LENGTH - 3].rstrip() + "..."
    send_sms(phone_number, message)


def _compose_situation_reply(detail, mode):
    template_text = templates.build_situation_reply(detail, mode)
    if mode == "discreet":
        return template_text
    reworded = ai_classifier.reword_reply(template_text)
    return reworded or template_text


def _clear_pending_safety_check(phone_number):
    SmsContext.objects.filter(
        phone_number=phone_number, pending_safety_check=True
    ).update(pending_safety_check=False)


def _reply_to_situation(phone_number, slug, text):
    detail = get_situation_detail(slug)
    if detail is None:
        _send(phone_number, templates.build_unmatched_reply())
        return
    discreet = keywords.match_discreet(text)

    existing = _live_context(phone_number)
    is_new_topic = existing is None or existing.last_situation_slug != slug

    if is_new_topic and detail["risk_level"] == "high_risk":
        _send(phone_number, templates.SAFETY_CHECKIN_QUESTION)
        SmsContext.objects.update_or_create(
            phone_number=phone_number,
            defaults={
                "last_situation_slug": slug,
                "discreet": discreet,
                "pending_safety_check": True,
            },
        )
        return

    mode = "discreet" if discreet else "normal"
    _send(phone_number, _compose_situation_reply(detail, mode))
    SmsContext.objects.update_or_create(
        phone_number=phone_number,
        defaults={
            "last_situation_slug": slug,
            "discreet": discreet,
            "pending_safety_check": False,
        },
    )


def handle_sms_request(phone_number, text):
    if _is_rate_limited(phone_number):
        return

    if keywords.match_danger(text):
        detail = _live_context_detail(phone_number)
        _send(phone_number, templates.build_safety_reply(detail))
        _clear_pending_safety_check(phone_number)
        return

    pending = _live_context(phone_number)
    if pending is not None and pending.pending_safety_check:
        if keywords.match_not_safe_answer(text):
            detail = get_situation_detail(pending.last_situation_slug)
            _send(phone_number, templates.build_safety_reply(detail))
            _clear_pending_safety_check(phone_number)
            return

    if keywords.match_help(text):
        _send(phone_number, templates.build_support_reply(None))
        return

    slug = keywords.match_situation(text)
    if slug:
        _reply_to_situation(phone_number, slug, text)
        return

    followup = keywords.match_followup(text)
    if followup:
        context = _live_context(phone_number)
        if context is None:
            _send(phone_number, templates.build_followup_expired_reply())
            return
        detail = get_situation_detail(context.last_situation_slug)
        if detail is None:
            _send(phone_number, templates.build_followup_expired_reply())
            return
        mode = "discreet" if context.discreet else "normal"
        if followup == "support":
            _send(phone_number, templates.build_support_reply(detail, mode))
        else:
            _send(phone_number, templates.build_steps_reply(detail, mode))
        return

    slug = ai_classifier.classify_situation(text)
    if slug:
        _reply_to_situation(phone_number, slug, text)
        return

    pending = _live_context(phone_number)
    if pending is not None and pending.pending_safety_check:
        detail = get_situation_detail(pending.last_situation_slug)
        _clear_pending_safety_check(phone_number)
        if detail is None:
            _send(phone_number, templates.build_unmatched_reply())
            return
        mode = "discreet" if pending.discreet else "normal"
        _send(phone_number, _compose_situation_reply(detail, mode))
        return

    _send(phone_number, templates.build_unmatched_reply())


def _live_context(phone_number):
    cutoff = timezone.now() - timedelta(minutes=FOLLOWUP_WINDOW_MINUTES)
    context = SmsContext.objects.filter(phone_number=phone_number).first()
    if context is None:
        return None
    if context.updated_at < cutoff:
        context.delete()
        return None
    return context


def _live_context_detail(phone_number):
    context = _live_context(phone_number)
    if context is None:
        return None
    return get_situation_detail(context.last_situation_slug)
```

Note what changed from the current file: `_reply_to_situation` now checks `is_new_topic`/`risk_level` and either sends the check-in question or delegates to the new `_compose_situation_reply` helper (instead of calling `templates.build_situation_reply` directly); `handle_sms_request` gained the early pending-check checkpoint (right after the danger-word branch) and the late one (right before the final unmatched fallback), plus clearing the pending flag in the danger-word branch. Every other branch (`HELP`, follow-up, the overall structure) is unchanged.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: PASS — all 11 new tests OK, plus every pre-existing test in the file still passing unmodified (proving the refactor preserved existing behavior for every situation that isn't high-risk, and every path this task didn't intend to change).

- [ ] **Step 6: Run the full backend test suite**

Run: `cd backend && python manage.py test`
Expected: PASS, no regressions anywhere else in the project.

- [ ] **Step 7: Commit**

```bash
git add backend/apps/channels/sms/templates.py backend/apps/channels/sms/handler.py backend/apps/channels/sms/tests.py
git commit -m "feat: add safety check-in and reply rewording to SMS handler"
```

---

## Self-Review Notes

- **Spec coverage:** the check-in trigger condition (new high-risk topic only), the two-checkpoint resolution (including the specific "unsafe" overlap-with-`SITUATION_KEYWORDS` fix), the reword-only-in-normal-mode rule, the fact-preservation validation, and the "every failure falls back to the template text" contract are all covered by tasks 1-3 and their tests.
- **Placeholder scan:** no TBD/TODO; every step has runnable code or an exact command.
- **Type consistency:** `match_not_safe_answer(text) -> bool`, `reword_reply(template_text) -> str | None`, and `SmsContext.pending_safety_check` are used identically between the task that defines them and the task that consumes them (Task 3 consumes both Task 1 and Task 2's interfaces).

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-26-sms-conversational-safety-checkin.md`. Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
