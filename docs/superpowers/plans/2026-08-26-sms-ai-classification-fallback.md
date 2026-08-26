# SMS Free-Text AI Classification Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Claude-powered classification step as the SMS handler's new last-resort fallback — free text that matches no fixed keyword gets classified against the real seeded `Situation` catalog, and a matched slug is replied to through the exact same, already-shipped `build_situation_reply` template pipeline the keyword path uses.

**Architecture:** A new `ai_classifier.classify_situation(text) -> str | None` calls the Anthropic API with a strict "return a slug or NONE" system prompt and validates the result against the real active-situation catalog. `handler.py` gets a small refactor extracting the existing situation-reply logic into a shared `_reply_to_situation()` helper, used by both the keyword-match branch (unchanged behavior) and the new AI-fallback branch (new).

**Tech Stack:** `anthropic` Python SDK (not yet in `requirements.txt`), Claude Haiku (`claude-haiku-4-5`), Django settings/env vars already named in `.env.example` but unwired (`LLM_API_KEY`, `LLM_MODEL`).

## Global Constraints

- AI never composes the reply text sent to a user — it only returns a slug or `None`; the actual reply always comes from `templates.build_situation_reply()`, unchanged from the existing keyword path.
- Every classification failure mode — missing `LLM_API_KEY`, no active situations, network/API error, timeout, malformed response, a hallucinated slug not in the real catalog — returns `None` from `classify_situation()`. None of these ever raise out of that function.
- The Anthropic call uses a 5-second timeout (`client.with_options(timeout=5.0)`) since it runs inline in the SMS webhook request.
- Model is hardcoded as `MODEL = "claude-haiku-4-5"` inside `ai_classifier.py`, not read from the `LLM_MODEL` setting — `LLM_MODEL` is wired into settings for visibility/future use, but this specific call's model tier is a code decision, not an env-var-controlled one.
- The danger-word, `HELP`, situation-keyword, and follow-up branches in `handle_sms_request` are checked first, in that order, unchanged — AI classification only runs after all four have been tried and none matched.
- No automated test calls the real Anthropic API. Every test mocks the client.

---

## Task 1: `ai_classifier` module

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/config/settings.py`
- Create: `backend/apps/channels/sms/ai_classifier.py`
- Modify: `backend/apps/channels/sms/tests.py`

**Interfaces:**
- Consumes: `apps.rights.services.list_active_situations() -> list[dict]` (each `{"slug", "title", "risk_level"}`, already built and tested).
- Produces: `apps.channels.sms.ai_classifier.classify_situation(text: str) -> str | None`; Django settings `LLM_API_KEY`, `LLM_MODEL`.

- [ ] **Step 1: Add the dependency**

Add `anthropic` to `backend/requirements.txt` (append as its own line, matching the file's existing one-package-per-line style).

Run: `pip install anthropic`
Expected: `Successfully installed anthropic-... (and its transitive dependencies)`.

- [ ] **Step 2: Wire the LLM settings**

In `backend/config/settings.py`, immediately after the `AFRICASTALKING_SMS_SENDER_ID = ...` line (or wherever the Africa's Talking settings block ends), add:

```python

# LLM
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL") or "claude-haiku-4-5"
```

- [ ] **Step 3: Write the failing tests**

Append to `backend/apps/channels/sms/tests.py`. First, add these imports to the existing top-of-file import block (do not place them mid-file):

```python
from django.test import override_settings

from apps.channels.sms import ai_classifier
```

(If `override_settings` or `TestCase` is already imported from `django.test` elsewhere in the file, merge into that existing import line instead of adding a duplicate.)

Add this helper and test class:

```python
def _mock_text_response(text):
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.content = [block]
    return response


class ClassifySituationTests(TestCase):
    def setUp(self):
        _create_home_safety_situation()
        self.mock_client = MagicMock()
        ai_classifier._client = self.mock_client

    def tearDown(self):
        ai_classifier._client = None

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_slug_when_model_names_real_situation(self):
        self.mock_client.with_options.return_value.messages.create.return_value = (
            _mock_text_response("home-safety")
        )
        result = ai_classifier.classify_situation("someone hurt me at home")
        self.assertEqual(result, "home-safety")

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_none_when_model_says_none(self):
        self.mock_client.with_options.return_value.messages.create.return_value = (
            _mock_text_response("NONE")
        )
        result = ai_classifier.classify_situation("what's the weather today")
        self.assertIsNone(result)

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_none_for_hallucinated_slug(self):
        self.mock_client.with_options.return_value.messages.create.return_value = (
            _mock_text_response("made-up-slug")
        )
        result = ai_classifier.classify_situation("something unrelated")
        self.assertIsNone(result)

    @override_settings(LLM_API_KEY="test-key")
    def test_returns_none_when_client_raises(self):
        self.mock_client.with_options.return_value.messages.create.side_effect = (
            RuntimeError("boom")
        )
        result = ai_classifier.classify_situation("anything")
        self.assertIsNone(result)

    @override_settings(LLM_API_KEY="")
    def test_returns_none_and_skips_call_when_api_key_unset(self):
        result = ai_classifier.classify_situation("anything")
        self.assertIsNone(result)
        self.mock_client.with_options.assert_not_called()
```

`MagicMock` should already be imported (from Task 2 of the earlier SMS channel plan); if not, add `from unittest.mock import MagicMock, patch` to the top-of-file imports (merging with any existing `unittest.mock` import rather than duplicating it).

- [ ] **Step 4: Run tests to verify they fail**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.channels.sms.ai_classifier'`.

- [ ] **Step 5: Implement the classifier**

Create `backend/apps/channels/sms/ai_classifier.py`:

```python
import anthropic
from django.conf import settings

from apps.rights.services import list_active_situations

MODEL = "claude-haiku-4-5"

CLASSIFIER_SYSTEM_PROMPT = (
    "You are a strict classifier for Sauti Yo, a rights-to-action SMS "
    "service. Given a list of known situations and a free-text message "
    "from a citizen, respond with ONLY the matching situation's slug, "
    "or the single word NONE if nothing clearly matches. Never explain, "
    "never add commentary, never invent a slug that isn't in the list."
)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.LLM_API_KEY)
    return _client


def classify_situation(text):
    """
    Classifies free text against the catalog of known situations using
    Claude. Returns the matching situation slug, or None if nothing
    matched, the API key isn't configured, or the call failed for any
    reason - every failure mode is treated identically to "no match" so
    the caller can safely fall back to the unmatched-keyword reply.
    """
    if not settings.LLM_API_KEY:
        return None

    situations = list_active_situations()
    if not situations:
        return None

    valid_slugs = {s["slug"] for s in situations}
    catalog = "\n".join(f"{s['slug']}: {s['title']}" for s in situations)

    try:
        client = _get_client()
        response = client.with_options(timeout=5.0).messages.create(
            model=MODEL,
            max_tokens=32,
            system=CLASSIFIER_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Known situations:\n{catalog}\n\nMessage: {text}"
                    ),
                }
            ],
        )
    except Exception:
        # Any failure (auth, rate limit, network, timeout, unexpected SDK
        # error) degrades to "no match" - a classification failure has a
        # well-defined safe fallback, so it must never crash the SMS
        # handler over this call.
        return None

    reply_text = next(
        (block.text for block in response.content if block.type == "text"),
        "",
    ).strip()

    if reply_text in valid_slugs:
        return reply_text
    return None
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: PASS — 5 new tests OK, plus all pre-existing SMS tests still passing (57 total per the last known count, now 62).

- [ ] **Step 7: Commit**

```bash
git add backend/requirements.txt backend/config/settings.py backend/apps/channels/sms/ai_classifier.py backend/apps/channels/sms/tests.py
git commit -m "feat: add Claude-based free-text situation classifier"
```

---

## Task 2: Wire the AI fallback into the SMS handler

**Files:**
- Modify: `backend/apps/channels/sms/handler.py`
- Modify: `backend/apps/channels/sms/tests.py`

**Interfaces:**
- Consumes: `apps.channels.sms.ai_classifier.classify_situation(text) -> str | None` (Task 1).
- Produces: no new public interface — `handle_sms_request`'s signature and contract are unchanged; this task only changes its internal match order and extracts a new internal helper, `_reply_to_situation(phone_number, slug, text) -> None`.

- [ ] **Step 1: Write the failing test**

Append to `backend/apps/channels/sms/tests.py`, inside (or near) the existing `HandleSmsRequestTests` class — add a new test class so these are clearly grouped:

```python
class AiFallbackTests(TestCase):
    def setUp(self):
        _create_home_safety_situation()
        cache.clear()

    @patch("apps.channels.sms.handler.ai_classifier.classify_situation")
    @patch("apps.channels.sms.handler.send_sms")
    def test_ai_classified_slug_sends_situation_reply(
        self, mock_send, mock_classify
    ):
        mock_classify.return_value = "home-safety"
        handle_sms_request(
            "+256700000000", "I'm scared of my spouse and don't know what to do"
        )
        message = mock_send.call_args[0][1]
        self.assertIn("Sauti 116 - Child & GBV Helpline", message)

    @patch("apps.channels.sms.handler.ai_classifier.classify_situation")
    @patch("apps.channels.sms.handler.send_sms")
    def test_ai_classified_slug_persists_sms_context(
        self, mock_send, mock_classify
    ):
        mock_classify.return_value = "home-safety"
        handle_sms_request(
            "+256700000000", "I'm scared of my spouse and don't know what to do"
        )
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.last_situation_slug, "home-safety")

    @patch("apps.channels.sms.handler.ai_classifier.classify_situation")
    @patch("apps.channels.sms.handler.send_sms")
    def test_ai_no_match_sends_unmatched_reply(self, mock_send, mock_classify):
        mock_classify.return_value = None
        handle_sms_request("+256700000000", "what time is it")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.build_unmatched_reply())
```

Note the test message ("I'm scared of my spouse and don't know what to do") is deliberately chosen to match none of `keywords.py`'s existing fixed word lists (no "home"/"abuse"/"husband"/"wife"/"beat"/"unsafe", no danger words, no "help"/"step"/"support" substrings) — it must fall through every earlier branch and actually reach the AI-fallback branch for these tests to be meaningful. Do not change the wording without re-checking it against `SITUATION_KEYWORDS`, `DANGER_WORDS`, and `FOLLOWUP_WORDS` in `keywords.py`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: FAIL — `AttributeError: <module 'apps.channels.sms.handler' ...> does not have the attribute 'ai_classifier'` (the patch target doesn't exist yet because `handler.py` doesn't import `ai_classifier`).

- [ ] **Step 3: Refactor and wire the handler**

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


def _reply_to_situation(phone_number, slug, text):
    detail = get_situation_detail(slug)
    if detail is None:
        _send(phone_number, templates.build_unmatched_reply())
        return
    discreet = keywords.match_discreet(text)
    mode = "discreet" if discreet else "normal"
    _send(phone_number, templates.build_situation_reply(detail, mode))
    SmsContext.objects.update_or_create(
        phone_number=phone_number,
        defaults={"last_situation_slug": slug, "discreet": discreet},
    )


def handle_sms_request(phone_number, text):
    if _is_rate_limited(phone_number):
        return

    if keywords.match_danger(text):
        detail = _live_context_detail(phone_number)
        _send(phone_number, templates.build_safety_reply(detail))
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

This is a refactor of the situation-keyword branch (its body is now `_reply_to_situation`, called from two places) plus one new branch (the `ai_classifier.classify_situation` call) inserted between the follow-up branch and the final unmatched fallback. Every other function is unchanged from its current form.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: PASS — 3 new tests OK, and every pre-existing test in the file (including all the situation-keyword, danger-word, follow-up, and rate-limit tests) still passes unmodified — proving the refactor preserved existing behavior exactly.

- [ ] **Step 5: Run the full backend test suite**

Run: `cd backend && python manage.py test`
Expected: PASS, no regressions anywhere else in the project.

- [ ] **Step 6: Commit**

```bash
git add backend/apps/channels/sms/handler.py backend/apps/channels/sms/tests.py
git commit -m "feat: add AI classification fallback to SMS handler"
```

---

## Self-Review Notes

- **Spec coverage:** the classification-only design, the exact match-order placement, settings wiring, the 5-second timeout, the hardcoded-model decision, and the "every failure returns None" contract are all covered by Task 1's implementation and tests. The refactor + wiring + behavior-preservation requirement is covered by Task 2.
- **Placeholder scan:** no TBD/TODO; every step has runnable code or an exact command.
- **Type consistency:** `classify_situation(text) -> str | None` and `_reply_to_situation(phone_number, slug, text) -> None` are used identically between where they're defined (Task 1, Task 2 Step 3) and where they're called (Task 2 Step 3, and the tests in both tasks).

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-26-sms-ai-classification-fallback.md`. Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
