# SMS Channel Handler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the SMS channel end-to-end — inbound keyword-triggered replies, normal/discreet templates, danger-word safety short-circuit, and outbound sending via Africa's Talking — per `docs/superpowers/specs/2026-08-26-sms-channel-handler-design.md`.

**Architecture:** A stateless-by-default inbound webhook (`sms/views.py` → `sms/handler.py`) matches each incoming text against keyword rules (`sms/keywords.py`), looks up verified content through the shared Rights-to-Action service layer (`apps/rights/services.py`, vendored in Task 1), composes a reply (`sms/templates.py`), and sends it via `africastalking_client.send_sms`. A tiny `SmsContext` model (phone number → last matched situation, 10-minute window) is the only persisted state, supporting one natural `STEPS`/`SUPPORT` follow-up — not a USSD-style session/state-machine.

**Tech Stack:** Django (existing project), `africastalking` Python SDK (`==2.0.3`, already in `backend/requirements.txt` but not yet `pip install`ed in this dev environment — Task 2 installs it), PostgreSQL, Django's built-in test runner (`manage.py test`).

## Global Constraints

- SMS replies target `SMS_SEGMENT_BUDGET = 160` characters (GSM-7 single segment); templates should read tight enough to usually fit one segment.
- `FOLLOWUP_WINDOW_MINUTES = 10` — a `STEPS`/`SUPPORT` follow-up only resolves against `SmsContext` if its `updated_at` is within this window; otherwise treat as no context.
- Match order in the handler is fixed: danger words → `HELP` → situation keyword → follow-up keyword → unmatched. Danger-word matching runs unconditionally first on every request, no exceptions.
- No SMS is ever sent as an automatic side effect beyond the one reply to the inbound message — no auto-contacting police/relatives, no bulk/campaign sends (out of scope).
- Safety replies (`build_safety_reply`) must return the human-reviewed `SafetyResponse` message verbatim when a situation is known — never compose or paraphrase safety-critical wording.
- SMS is English-only for v1 — no language picker, no `language` parameter threaded through the SMS handler.
- `apps.channels.sms` depends on `apps.rights.services` (Task 1) rather than duplicating direct ORM queries — the one exception is the general emergency-services list, which queries `SupportService` directly (matching how `ussd/menus.py`'s `render_emergency_list` already does it — there's no service-layer helper for that lookup).
- No retry/backoff logic on send failures (matches the project's "no Redis/Celery" constraint carried over from the USSD design) — `send_sms` raises on failure; the webhook view catches broadly so Africa's Talking always gets a 200, but does not retry.

---

## Task 1: Vendor the Rights-to-Action service layer

**Files:**
- Create: `backend/apps/rights/services.py`
- Modify: `backend/apps/rights/tests.py`

**Interfaces:**
- Consumes: nothing (first task).
- Produces:
  - `list_active_situations() -> list[dict]` (each `{"slug", "title", "risk_level"}`)
  - `get_situation_detail(slug: str) -> dict | None` — `{"slug", "title", "description", "risk_level", "rights_topics": [...]}`, each topic `{"slug", "title", "summary", "action_steps": [{"order","title","description","is_safety_critical"}], "safety_responses": [{"trigger_key","message"}], "support_services": [{"name","phone_number","is_emergency_service"}]}`
  - `get_channel_text(situation_slug: str, channel: str, language: str = "en") -> str | None`
  - `get_safety_message(situation_slug: str, trigger_key: str = "immediate_danger") -> str | None`

- [ ] **Step 1: Write the failing tests**

Replace the contents of `backend/apps/rights/tests.py` with:

```python
from django.test import TestCase

from apps.content.models import ChannelContent
from apps.rights.models import (
    ActionStep,
    RightsTopic,
    SafetyResponse,
    Situation,
    SituationRightsTopic,
)
from apps.rights.services import (
    get_channel_text,
    get_safety_message,
    get_situation_detail,
    list_active_situations,
)
from apps.support.models import SupportService


class RightsServicesTests(TestCase):
    def setUp(self):
        self.situation = Situation.objects.create(
            slug="home-safety",
            title="I don't feel safe at home",
            description="For situations involving abuse or fear at home.",
            risk_level="high_risk",
        )
        self.inactive_situation = Situation.objects.create(
            slug="inactive-situation",
            title="Inactive",
            is_active=False,
        )
        self.topic = RightsTopic.objects.create(
            slug="domestic-violence-rights",
            title="Domestic Violence & Your Rights",
            summary="The Domestic Violence Act protects you from abuse.",
            risk_level="high_risk",
        )
        SituationRightsTopic.objects.create(
            situation=self.situation, rights_topic=self.topic
        )
        self.action_step = ActionStep.objects.create(
            rights_topic=self.topic,
            order=1,
            title="Move somewhere safer",
            description="If you can safely do so, move to a safer location.",
            is_safety_critical=True,
        )
        self.safety_response = SafetyResponse.objects.create(
            rights_topic=self.topic,
            trigger_key="immediate_danger",
            message="Your safety matters. Call Sauti 116.",
        )
        self.support_service = SupportService.objects.create(
            name="Sauti 116 - Child & GBV Helpline",
            service_type="helpline",
            phone_number="116",
        )
        self.topic.support_services.add(self.support_service)

    def test_list_active_situations_returns_active_only(self):
        result = list_active_situations()
        slugs = [item["slug"] for item in result]
        self.assertIn("home-safety", slugs)
        self.assertNotIn("inactive-situation", slugs)

    def test_get_situation_detail_returns_full_picture(self):
        detail = get_situation_detail("home-safety")
        self.assertEqual(detail["slug"], "home-safety")
        self.assertEqual(len(detail["rights_topics"]), 1)
        topic = detail["rights_topics"][0]
        self.assertEqual(topic["slug"], "domestic-violence-rights")
        self.assertEqual(len(topic["action_steps"]), 1)
        self.assertEqual(
            topic["action_steps"][0]["title"], "Move somewhere safer"
        )
        self.assertEqual(len(topic["safety_responses"]), 1)
        self.assertEqual(len(topic["support_services"]), 1)
        self.assertEqual(
            topic["support_services"][0]["name"],
            "Sauti 116 - Child & GBV Helpline",
        )

    def test_get_situation_detail_returns_none_for_missing_slug(self):
        self.assertIsNone(get_situation_detail("does-not-exist"))

    def test_get_channel_text_returns_text_when_exists(self):
        ChannelContent.objects.create(
            content_key="home_safety_intro",
            channel="sms",
            language="en",
            text="Custom SMS intro text.",
        )
        result = get_channel_text("home-safety", "sms", "en")
        self.assertEqual(result, "Custom SMS intro text.")

    def test_get_channel_text_returns_none_when_missing(self):
        result = get_channel_text("home-safety", "sms", "en")
        self.assertIsNone(result)

    def test_get_safety_message_returns_message_for_trigger_key(self):
        message = get_safety_message("home-safety", "immediate_danger")
        self.assertEqual(message, "Your safety matters. Call Sauti 116.")

    def test_get_safety_message_returns_none_when_no_match(self):
        message = get_safety_message("home-safety", "nonexistent_trigger")
        self.assertIsNone(message)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python manage.py test apps.rights -v 2`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'apps.rights.services'` (or `ImportError`).

- [ ] **Step 3: Create the service layer**

Create `backend/apps/rights/services.py`:

```python
"""
Internal service layer for the Rights-to-Action Engine.

These functions are called directly by other Django apps in this same
project (mainly apps.channels) - not over HTTP. USSD/SMS/Voice responses
need to be fast and can't depend on this server making an HTTP request to
itself.
"""

from apps.content.models import ChannelContent
from apps.rights.models import Situation


def list_active_situations():
    """
    Returns a simple list for building a situation-picker menu
    (e.g. the USSD 'What's happening?' screen).
    """
    return list(
        Situation.objects.filter(is_active=True)
        .order_by("title")
        .values("slug", "title", "risk_level")
    )


def get_situation_detail(slug):
    """
    Returns the full Rights-to-Action picture for one situation:
    linked rights topics, their action steps, safety responses, and
    support services. Returns None if the slug doesn't exist or isn't active.
    """
    try:
        situation = Situation.objects.prefetch_related(
            "rights_links__rights_topic__action_steps",
            "rights_links__rights_topic__safety_responses",
            "rights_links__rights_topic__support_services",
        ).get(slug=slug, is_active=True)
    except Situation.DoesNotExist:
        return None

    topics = []
    for link in situation.rights_links.all():
        topic = link.rights_topic
        topics.append({
            "slug": topic.slug,
            "title": topic.title,
            "summary": topic.summary,
            "action_steps": [
                {
                    "order": step.order,
                    "title": step.title,
                    "description": step.description,
                    "is_safety_critical": step.is_safety_critical,
                }
                for step in topic.action_steps.filter(is_active=True).order_by("order")
            ],
            "safety_responses": [
                {"trigger_key": r.trigger_key, "message": r.message}
                for r in topic.safety_responses.filter(is_active=True)
            ],
            "support_services": [
                {
                    "name": s.name,
                    "phone_number": s.phone_number,
                    "is_emergency_service": s.is_emergency_service,
                }
                for s in topic.support_services.filter(is_active=True)
            ],
        })

    return {
        "slug": situation.slug,
        "title": situation.title,
        "description": situation.description,
        "risk_level": situation.risk_level,
        "rights_topics": topics,
    }


def get_channel_text(situation_slug, channel, language="en"):
    """
    Looks up pre-written, channel-specific copy for a situation, following
    the naming convention: content_key = "{slug_with_underscores}_intro"

    Returns None if nobody's written channel-specific text for this
    situation yet - callers should fall back to Situation.description
    in that case, not treat it as an error.
    """
    content_key = f"{situation_slug.replace('-', '_')}_intro"
    try:
        content = ChannelContent.objects.get(
            content_key=content_key,
            channel=channel,
            language=language,
            is_active=True,
        )
        return content.text
    except ChannelContent.DoesNotExist:
        return None


def get_safety_message(situation_slug, trigger_key="immediate_danger"):
    """
    Returns the predefined safety response for a high-risk situation.

    This function exists specifically so channel code NEVER has to
    construct safety-critical wording itself - it always comes from a
    human-reviewed SafetyResponse row. Returns None if no matching
    safety response exists.
    """
    detail = get_situation_detail(situation_slug)
    if not detail:
        return None
    for topic in detail["rights_topics"]:
        for response in topic["safety_responses"]:
            if response["trigger_key"] == trigger_key:
                return response["message"]
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python manage.py test apps.rights -v 2`
Expected: PASS — 7 tests OK.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/rights/services.py backend/apps/rights/tests.py
git commit -m "feat: add Rights-to-Action service layer for channel handlers"
```

---

## Task 2: Africa's Talking SMS send wrapper

**Files:**
- Modify: `backend/apps/channels/africastalking_client.py`
- Modify: `backend/config/settings.py`
- Test: `backend/apps/channels/sms/tests.py` (new file)

**Interfaces:**
- Consumes: nothing.
- Produces: `apps.channels.africastalking_client.send_sms(phone_number: str, message: str) -> dict` (raises on failure); Django settings `AFRICASTALKING_USERNAME`, `AFRICASTALKING_API_KEY`, `AFRICASTALKING_SMS_SENDER_ID`.

- [ ] **Step 1: Install the SDK into the dev environment**

Run: `pip install africastalking==2.0.3`
Expected: `Successfully installed africastalking-2.0.3 ...` (it's already pinned in `backend/requirements.txt`, just not yet installed locally).

- [ ] **Step 2: Write the failing test**

Create `backend/apps/channels/sms/tests.py`:

```python
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.channels import africastalking_client


class SendSmsTests(TestCase):
    def setUp(self):
        self.mock_sms_service = MagicMock()
        africastalking_client._sms_service = self.mock_sms_service

    def tearDown(self):
        africastalking_client._sms_service = None

    def test_send_sms_calls_sdk_with_message_and_recipient(self):
        africastalking_client.send_sms("+256700000000", "Hello")
        self.mock_sms_service.send.assert_called_once_with(
            "Hello", ["+256700000000"], sender_id=None
        )

    def test_send_sms_passes_configured_sender_id(self):
        with self.settings(AFRICASTALKING_SMS_SENDER_ID="SAUTIYO"):
            africastalking_client.send_sms("+256700000000", "Hello")
        self.mock_sms_service.send.assert_called_once_with(
            "Hello", ["+256700000000"], sender_id="SAUTIYO"
        )

    @patch("apps.channels.africastalking_client.africastalking")
    def test_get_sms_service_initializes_sdk_with_settings_credentials(
        self, mock_at
    ):
        africastalking_client._sms_service = None
        with self.settings(
            AFRICASTALKING_USERNAME="sandbox",
            AFRICASTALKING_API_KEY="test-key",
        ):
            africastalking_client._get_sms_service()
        mock_at.initialize.assert_called_once_with("sandbox", "test-key")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: FAIL — `AttributeError: module 'apps.channels.africastalking_client' has no attribute '_sms_service'` (the file is currently empty).

- [ ] **Step 4: Add Africa's Talking settings**

In `backend/config/settings.py`, immediately after the `ALLOWED_HOSTS = [...]` block (before the `# Application definition` comment), add:

```python
# Africa's Talking
AFRICASTALKING_USERNAME = os.getenv("AFRICASTALKING_USERNAME", "sandbox")
AFRICASTALKING_API_KEY = os.getenv("AFRICASTALKING_API_KEY", "")
AFRICASTALKING_SMS_SENDER_ID = os.getenv("AFRICASTALKING_SMS_SENDER_ID", "")
```

- [ ] **Step 5: Implement the send wrapper**

Write `backend/apps/channels/africastalking_client.py`:

```python
import africastalking
from django.conf import settings

_sms_service = None


def _get_sms_service():
    global _sms_service
    if _sms_service is None:
        africastalking.initialize(
            settings.AFRICASTALKING_USERNAME,
            settings.AFRICASTALKING_API_KEY,
        )
        _sms_service = africastalking.SMS
    return _sms_service


def send_sms(phone_number, message):
    """
    Sends an SMS via Africa's Talking. Returns the SDK's response dict.
    Raises on failure - callers are responsible for handling/logging.
    """
    sms_service = _get_sms_service()
    sender_id = settings.AFRICASTALKING_SMS_SENDER_ID or None
    return sms_service.send(message, [phone_number], sender_id=sender_id)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: PASS — 3 tests OK.

- [ ] **Step 7: Commit**

```bash
git add backend/apps/channels/africastalking_client.py backend/apps/channels/sms/tests.py backend/config/settings.py
git commit -m "feat: add Africa's Talking SMS send wrapper"
```

---

## Task 3: `SmsContext` model

**Files:**
- Modify: `backend/apps/channels/models.py`
- Create: `backend/apps/channels/migrations/0003_smscontext.py` (via `makemigrations`)
- Modify: `backend/apps/channels/sms/tests.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `apps.channels.models.SmsContext` — fields `phone_number` (unique, `CharField`), `last_situation_slug` (`SlugField`), `updated_at` (`auto_now`).

- [ ] **Step 1: Write the failing test**

Append to `backend/apps/channels/sms/tests.py`:

```python
from django.db import IntegrityError

from apps.channels.models import SmsContext


class SmsContextModelTests(TestCase):
    def test_create_context_with_defaults(self):
        context = SmsContext.objects.create(
            phone_number="+256700000000", last_situation_slug="home-safety"
        )
        self.assertEqual(context.last_situation_slug, "home-safety")
        self.assertIsNotNone(context.updated_at)

    def test_phone_number_is_unique(self):
        SmsContext.objects.create(
            phone_number="+256700000000", last_situation_slug="home-safety"
        )
        with self.assertRaises(IntegrityError):
            SmsContext.objects.create(
                phone_number="+256700000000", last_situation_slug="work"
            )
```

Add `from django.test import TestCase` import at the top of the file if not already present (it is, from Task 2).

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: FAIL — `ImportError: cannot import name 'SmsContext' from 'apps.channels.models'`.

- [ ] **Step 3: Add the model**

In `backend/apps/channels/models.py`, append after the `UssdSession` class:

```python


class SmsContext(models.Model):
    phone_number = models.CharField(max_length=50, unique=True)
    last_situation_slug = models.SlugField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.phone_number} -> {self.last_situation_slug}"
```

- [ ] **Step 4: Generate and inspect the migration**

Run: `cd backend && python manage.py makemigrations channels`
Expected: `Migrations for 'channels': backend/apps/channels/migrations/0003_smscontext.py - Create model SmsContext`

Open the generated file and confirm it only adds `SmsContext` with the three fields above and depends on `('channels', '0002_ussdsession_last_response_ussdsession_last_text')` — no unrelated changes. If Django also proposes altering `UssdSession`'s auto-created primary key (the `models.W042` warning seen in the existing test suite), do not accept that change here — it's pre-existing and out of scope; if prompted, answer to only add the new model.

- [ ] **Step 5: Apply the migration and run tests**

Run: `cd backend && python manage.py migrate channels && python manage.py test apps.channels.sms -v 2`
Expected: PASS — 5 tests OK (3 from Task 2 + 2 new).

- [ ] **Step 6: Commit**

```bash
git add backend/apps/channels/models.py backend/apps/channels/migrations/0003_smscontext.py backend/apps/channels/sms/tests.py
git commit -m "feat: add SmsContext model for SMS follow-up memory"
```

---

## Task 4: SMS keyword matching

**Files:**
- Create: `backend/apps/channels/sms/keywords.py`
- Modify: `backend/apps/channels/sms/tests.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `match_danger(text: str) -> bool`
  - `match_help(text: str) -> bool`
  - `match_situation(text: str) -> str | None` (a situation slug: `"home-safety"`, `"work"`, `"land"`, or `"child"`)
  - `match_followup(text: str) -> "steps" | "support" | None`
  - `match_discreet(text: str) -> bool`

- [ ] **Step 1: Write the failing test**

Append to `backend/apps/channels/sms/tests.py`:

```python
from apps.channels.sms.keywords import (
    match_danger,
    match_discreet,
    match_followup,
    match_help,
    match_situation,
)


class KeywordMatchingTests(TestCase):
    def test_match_situation_home_safety(self):
        self.assertEqual(match_situation("My husband beats me"), "home-safety")

    def test_match_situation_work(self):
        self.assertEqual(match_situation("I was fired from my job"), "work")

    def test_match_situation_land(self):
        self.assertEqual(
            match_situation("someone wants to evict me from my land"), "land"
        )

    def test_match_situation_child(self):
        self.assertEqual(
            match_situation("my child is unsafe at school"), "child"
        )

    def test_match_situation_returns_none_for_unmatched_text(self):
        self.assertIsNone(match_situation("hello there"))

    def test_match_danger_detects_danger_word(self):
        self.assertTrue(match_danger("he has a weapon right now"))

    def test_match_danger_false_for_safe_text(self):
        self.assertFalse(match_danger("I have a problem at work"))

    def test_match_followup_steps(self):
        self.assertEqual(match_followup("what are the steps"), "steps")

    def test_match_followup_support(self):
        self.assertEqual(match_followup("SUPPORT"), "support")

    def test_match_followup_returns_none(self):
        self.assertIsNone(match_followup("hello"))

    def test_match_help_matches_standalone_word(self):
        self.assertTrue(match_help("HELP"))

    def test_match_help_false_for_unrelated_text(self):
        self.assertFalse(match_help("helpful tips"))

    def test_match_discreet_detects_keyword(self):
        self.assertTrue(match_discreet("HOME DISCREET"))

    def test_match_discreet_false_by_default(self):
        self.assertFalse(match_discreet("HOME"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.channels.sms.keywords'`.

- [ ] **Step 3: Implement keyword matching**

Create `backend/apps/channels/sms/keywords.py`:

```python
import re

DANGER_WORDS = [
    "danger", "weapon", "threatened", "emergency", "hurt", "right now",
]

SITUATION_KEYWORDS = {
    "home-safety": ["home", "abuse", "husband", "wife", "beat", "unsafe"],
    "work": ["work", "job", "salary", "fired", "boss"],
    "land": ["land", "plot", "evict", "property"],
    "child": ["child", "school", "minor", "kid"],
}

FOLLOWUP_WORDS = {
    "steps": ["step"],
    "support": ["support"],
}


def _normalize(text):
    return (text or "").strip().lower()


def match_danger(text):
    normalized = _normalize(text)
    return any(word in normalized for word in DANGER_WORDS)


def match_situation(text):
    normalized = _normalize(text)
    for slug in sorted(SITUATION_KEYWORDS):
        if any(word in normalized for word in SITUATION_KEYWORDS[slug]):
            return slug
    return None


def match_followup(text):
    normalized = _normalize(text)
    for intent in ("steps", "support"):
        if any(word in normalized for word in FOLLOWUP_WORDS[intent]):
            return intent
    return None


def match_help(text):
    normalized = _normalize(text)
    return bool(re.search(r"\bhelp\b", normalized))


def match_discreet(text):
    normalized = _normalize(text)
    return "discreet" in normalized
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: PASS — 14 new tests OK (plus the 5 from Tasks 2-3).

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/sms/keywords.py backend/apps/channels/sms/tests.py
git commit -m "feat: add SMS keyword matching"
```

---

## Task 5: SMS reply templates

**Files:**
- Create: `backend/apps/channels/sms/templates.py`
- Modify: `backend/apps/channels/sms/tests.py`

**Interfaces:**
- Consumes: `apps.rights.services.get_channel_text`, `apps.rights.services.get_safety_message` (Task 1); `apps.support.models.SupportService` (existing).
- Produces:
  - `build_situation_reply(detail: dict, mode: "normal" | "discreet" = "normal") -> str`
  - `build_support_reply(detail: dict | None = None) -> str`
  - `build_safety_reply(detail: dict | None = None, trigger_key: str = "immediate_danger") -> str`
  - `build_steps_reply(detail: dict) -> str`
  - `build_unmatched_reply() -> str`
  - `build_followup_expired_reply() -> str`
  - Constants: `SMS_SEGMENT_BUDGET`, `NO_SUPPORT_SERVICES_REPLY`, `NO_ACTION_STEPS_REPLY`, `GENERAL_SAFETY_REPLY`, `UNMATCHED_REPLY`, `FOLLOWUP_EXPIRED_REPLY`

- [ ] **Step 1: Write the failing test**

Append to `backend/apps/channels/sms/tests.py`, and add these imports at the top of the file (alongside the existing ones):

```python
from apps.rights.models import (
    ActionStep,
    RightsTopic,
    SafetyResponse,
    Situation,
    SituationRightsTopic,
)
from apps.rights.services import get_situation_detail
from apps.support.models import SupportService
```

Add this module-level fixture helper (used by this task and later tasks) and the test classes:

```python
def _create_home_safety_situation():
    situation = Situation.objects.create(
        slug="home-safety",
        title="I don't feel safe at home",
        description="For situations involving abuse or fear at home.",
        risk_level="high_risk",
    )
    topic = RightsTopic.objects.create(
        slug="domestic-violence-rights",
        title="Domestic Violence & Your Rights",
        summary="The Domestic Violence Act protects you from abuse.",
        risk_level="high_risk",
    )
    SituationRightsTopic.objects.create(situation=situation, rights_topic=topic)
    ActionStep.objects.create(
        rights_topic=topic,
        order=1,
        title="Move somewhere safer",
        description="Move to a safer location if you can.",
        is_safety_critical=True,
    )
    SafetyResponse.objects.create(
        rights_topic=topic,
        trigger_key="immediate_danger",
        message="Your safety matters. Call Sauti 116.",
    )
    service = SupportService.objects.create(
        name="Sauti 116 - Child & GBV Helpline",
        service_type="helpline",
        phone_number="116",
        is_emergency_service=True,
    )
    topic.support_services.add(service)
    return situation


def _create_land_situation_without_safety_response():
    situation = Situation.objects.create(
        slug="land-property",
        title="Land or property problem",
        risk_level="standard",
    )
    topic = RightsTopic.objects.create(
        slug="matrimonial-property-rights",
        title="Property Rights After Separation",
        summary="You may have a right to a share of matrimonial property.",
    )
    SituationRightsTopic.objects.create(situation=situation, rights_topic=topic)
    return situation


class BuildSituationReplyTests(TestCase):
    def setUp(self):
        _create_home_safety_situation()
        self.detail = get_situation_detail("home-safety")

    def test_normal_mode_includes_full_names(self):
        reply = templates.build_situation_reply(self.detail, mode="normal")
        self.assertIn("Sauti 116 - Child & GBV Helpline", reply)
        self.assertIn("Move to a safer location", reply)

    def test_discreet_mode_omits_service_name(self):
        reply = templates.build_situation_reply(self.detail, mode="discreet")
        self.assertNotIn("Sauti 116 - Child & GBV Helpline", reply)
        self.assertIn("116", reply)

    def test_falls_back_to_description_without_channel_content(self):
        reply = templates.build_situation_reply(self.detail, mode="normal")
        self.assertIn(
            "For situations involving abuse or fear at home.", reply
        )


class BuildSupportReplyTests(TestCase):
    def setUp(self):
        _create_home_safety_situation()
        self.detail = get_situation_detail("home-safety")

    def test_uses_situation_support_services_when_detail_given(self):
        reply = templates.build_support_reply(self.detail)
        self.assertIn("116", reply)

    def test_falls_back_to_no_services_message_when_empty(self):
        empty_detail = dict(self.detail)
        empty_detail["rights_topics"] = [
            dict(t, support_services=[]) for t in self.detail["rights_topics"]
        ]
        reply = templates.build_support_reply(empty_detail)
        self.assertEqual(reply, templates.NO_SUPPORT_SERVICES_REPLY)

    def test_uses_general_emergency_services_when_no_detail(self):
        SupportService.objects.create(
            name="Uganda Police GBV Helpline",
            service_type="helpline",
            phone_number="0800199195",
            is_emergency_service=True,
        )
        reply = templates.build_support_reply(None)
        self.assertIn("0800199195", reply)


class BuildSafetyReplyTests(TestCase):
    def setUp(self):
        _create_home_safety_situation()
        self.detail = get_situation_detail("home-safety")

    def test_uses_predefined_safety_message_when_detail_given(self):
        reply = templates.build_safety_reply(self.detail)
        self.assertEqual(reply, "Your safety matters. Call Sauti 116.")

    def test_falls_back_to_general_safety_reply_without_detail(self):
        reply = templates.build_safety_reply(None)
        self.assertIn("999", reply)

    def test_falls_back_to_general_safety_reply_when_no_matching_response(self):
        _create_land_situation_without_safety_response()
        detail = get_situation_detail("land-property")
        reply = templates.build_safety_reply(detail)
        self.assertIn("999", reply)


class BuildStepsReplyTests(TestCase):
    def setUp(self):
        _create_home_safety_situation()
        self.detail = get_situation_detail("home-safety")

    def test_lists_action_steps(self):
        reply = templates.build_steps_reply(self.detail)
        self.assertIn("Move to a safer location", reply)

    def test_falls_back_when_no_steps(self):
        _create_land_situation_without_safety_response()
        detail = get_situation_detail("land-property")
        reply = templates.build_steps_reply(detail)
        self.assertEqual(reply, templates.NO_ACTION_STEPS_REPLY)


class FixedReplyTests(TestCase):
    def test_build_unmatched_reply(self):
        self.assertIn("HOME", templates.build_unmatched_reply())

    def test_build_followup_expired_reply(self):
        self.assertIn("STEPS", templates.build_followup_expired_reply())
```

Add `from apps.channels.sms import templates` to the imports at the top of the file.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.channels.sms.templates'`.

- [ ] **Step 3: Implement templates**

Create `backend/apps/channels/sms/templates.py`:

```python
from apps.rights.services import get_channel_text, get_safety_message
from apps.support.models import SupportService

SMS_SEGMENT_BUDGET = 160

UNMATCHED_REPLY = (
    "You can text HOME, WORK, LAND or CHILD for help, or HELP for support."
)
FOLLOWUP_EXPIRED_REPLY = (
    "Please first text HOME, WORK, LAND or CHILD to tell us what's going "
    "on, then text STEPS or SUPPORT."
)
GENERAL_SAFETY_REPLY = (
    "If you are in immediate danger, call the Police on 999 or 112 now. "
    "Free support: Sauti 116."
)
NO_SUPPORT_SERVICES_REPLY = (
    "No support contacts are available right now. In an emergency, call "
    "the Police on 999 or 112."
)
NO_ACTION_STEPS_REPLY = (
    "No specific steps are available for this yet. Text SUPPORT for help "
    "contacts."
)


def _situation_intro(detail):
    text = get_channel_text(detail["slug"], "sms", "en")
    if text:
        return text
    return detail["description"] or detail["title"]


def _first_action_step(detail):
    for topic in detail["rights_topics"]:
        if topic["action_steps"]:
            return topic["action_steps"][0]["description"]
    return None


def _first_support_service(detail):
    for topic in detail["rights_topics"]:
        for service in topic["support_services"]:
            if service.get("phone_number"):
                return service
    return None


def build_situation_reply(detail, mode="normal"):
    intro = _situation_intro(detail)
    step = _first_action_step(detail)
    service = _first_support_service(detail)

    parts = [intro]
    if step:
        parts.append(f"Next step: {step}")
    if service:
        if mode == "discreet":
            parts.append(f"A support contact is available: {service['phone_number']}")
        else:
            parts.append(f"{service['name']}: {service['phone_number']}")

    return " ".join(parts)


def build_support_reply(detail=None):
    """
    Builds a support-contacts reply. If `detail` (from get_situation_detail)
    is given, uses that situation's linked support services; otherwise
    falls back to the general emergency-services list.
    """
    if detail is not None:
        services = []
        for topic in detail["rights_topics"]:
            services.extend(topic["support_services"])
    else:
        services = list(
            SupportService.objects.filter(
                is_emergency_service=True, is_active=True
            )
            .order_by("name")
            .values("name", "phone_number")
        )

    lines = [
        f"{s['name']}: {s['phone_number']}"
        for s in services
        if s.get("phone_number")
    ]
    return "\n".join(lines) if lines else NO_SUPPORT_SERVICES_REPLY


def build_safety_reply(detail=None, trigger_key="immediate_danger"):
    if detail is not None:
        message = get_safety_message(detail["slug"], trigger_key)
        if message:
            return message
    return GENERAL_SAFETY_REPLY


def build_steps_reply(detail):
    steps = []
    for topic in detail["rights_topics"]:
        steps.extend(topic["action_steps"])
    if not steps:
        return NO_ACTION_STEPS_REPLY
    lines = [f"{i + 1}. {step['description']}" for i, step in enumerate(steps)]
    return "\n".join(lines)


def build_unmatched_reply():
    return UNMATCHED_REPLY


def build_followup_expired_reply():
    return FOLLOWUP_EXPIRED_REPLY
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: PASS — 12 new tests OK (plus the 19 from Tasks 2-4).

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/sms/templates.py backend/apps/channels/sms/tests.py
git commit -m "feat: add SMS reply templates"
```

---

## Task 6: SMS handler orchestrator

**Files:**
- Create: `backend/apps/channels/sms/handler.py`
- Modify: `backend/apps/channels/sms/tests.py`

**Interfaces:**
- Consumes: `apps.channels.africastalking_client.send_sms` (Task 2), `apps.channels.models.SmsContext` (Task 3), `apps.channels.sms.keywords.*` (Task 4), `apps.channels.sms.templates.*` (Task 5), `apps.rights.services.get_situation_detail` (Task 1).
- Produces: `apps.channels.sms.handler.handle_sms_request(phone_number: str, text: str) -> None`.

- [ ] **Step 1: Write the failing test**

Append to `backend/apps/channels/sms/tests.py`. Add these imports at the top:

```python
from datetime import timedelta

from django.utils import timezone

from apps.channels.sms.handler import handle_sms_request
```

Add:

```python
class HandleSmsRequestTests(TestCase):
    def setUp(self):
        _create_home_safety_situation()

    @patch("apps.channels.sms.handler.send_sms")
    def test_situation_keyword_sends_normal_reply(self, mock_send):
        handle_sms_request("+256700000000", "My husband beats me")
        mock_send.assert_called_once()
        phone, message = mock_send.call_args[0]
        self.assertEqual(phone, "+256700000000")
        self.assertIn("Sauti 116 - Child & GBV Helpline", message)

    @patch("apps.channels.sms.handler.send_sms")
    def test_situation_keyword_with_discreet_omits_service_name(self, mock_send):
        handle_sms_request("+256700000000", "home discreet")
        message = mock_send.call_args[0][1]
        self.assertNotIn("Sauti 116 - Child & GBV Helpline", message)

    @patch("apps.channels.sms.handler.send_sms")
    def test_situation_keyword_creates_sms_context(self, mock_send):
        handle_sms_request("+256700000000", "my husband beats me")
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.last_situation_slug, "home-safety")

    @patch("apps.channels.sms.handler.send_sms")
    def test_danger_word_sends_safety_reply_with_context(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000", last_situation_slug="home-safety"
        )
        handle_sms_request("+256700000000", "he has a weapon right now")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, "Your safety matters. Call Sauti 116.")

    @patch("apps.channels.sms.handler.send_sms")
    def test_danger_word_sends_general_safety_reply_without_context(self, mock_send):
        handle_sms_request("+256711111111", "emergency, weapon")
        message = mock_send.call_args[0][1]
        self.assertIn("999", message)

    @patch("apps.channels.sms.handler.send_sms")
    def test_help_alone_sends_support_reply(self, mock_send):
        SupportService.objects.create(
            name="Uganda Police GBV Helpline",
            service_type="helpline",
            phone_number="0800199195",
            is_emergency_service=True,
        )
        handle_sms_request("+256700000000", "HELP")
        message = mock_send.call_args[0][1]
        self.assertIn("0800199195", message)

    @patch("apps.channels.sms.handler.send_sms")
    def test_followup_support_within_window(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000", last_situation_slug="home-safety"
        )
        handle_sms_request("+256700000000", "SUPPORT")
        message = mock_send.call_args[0][1]
        self.assertIn("116", message)

    @patch("apps.channels.sms.handler.send_sms")
    def test_followup_steps_within_window(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000", last_situation_slug="home-safety"
        )
        handle_sms_request("+256700000000", "STEPS")
        message = mock_send.call_args[0][1]
        self.assertIn("Move to a safer location", message)

    @patch("apps.channels.sms.handler.send_sms")
    def test_followup_expired_context(self, mock_send):
        context = SmsContext.objects.create(
            phone_number="+256700000000", last_situation_slug="home-safety"
        )
        SmsContext.objects.filter(pk=context.pk).update(
            updated_at=timezone.now() - timedelta(minutes=11)
        )
        handle_sms_request("+256700000000", "STEPS")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.build_followup_expired_reply())

    @patch("apps.channels.sms.handler.send_sms")
    def test_followup_without_any_context(self, mock_send):
        handle_sms_request("+256799999999", "SUPPORT")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.build_followup_expired_reply())

    @patch("apps.channels.sms.handler.send_sms")
    def test_unmatched_text_sends_fallback_reply(self, mock_send):
        handle_sms_request("+256700000000", "hello there")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.build_unmatched_reply())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.channels.sms.handler'`.

- [ ] **Step 3: Implement the handler**

Create `backend/apps/channels/sms/handler.py`:

```python
from datetime import timedelta

from django.utils import timezone

from apps.channels.africastalking_client import send_sms
from apps.channels.models import SmsContext
from apps.channels.sms import keywords, templates
from apps.rights.services import get_situation_detail

FOLLOWUP_WINDOW_MINUTES = 10


def handle_sms_request(phone_number, text):
    if keywords.match_danger(text):
        detail = _live_context_detail(phone_number)
        send_sms(phone_number, templates.build_safety_reply(detail))
        return

    if keywords.match_help(text):
        send_sms(phone_number, templates.build_support_reply(None))
        return

    slug = keywords.match_situation(text)
    if slug:
        detail = get_situation_detail(slug)
        mode = "discreet" if keywords.match_discreet(text) else "normal"
        send_sms(phone_number, templates.build_situation_reply(detail, mode))
        SmsContext.objects.update_or_create(
            phone_number=phone_number,
            defaults={"last_situation_slug": slug},
        )
        return

    followup = keywords.match_followup(text)
    if followup:
        detail = _live_context_detail(phone_number)
        if detail is None:
            send_sms(phone_number, templates.build_followup_expired_reply())
            return
        if followup == "support":
            send_sms(phone_number, templates.build_support_reply(detail))
        else:
            send_sms(phone_number, templates.build_steps_reply(detail))
        return

    send_sms(phone_number, templates.build_unmatched_reply())


def _live_context_detail(phone_number):
    cutoff = timezone.now() - timedelta(minutes=FOLLOWUP_WINDOW_MINUTES)
    context = SmsContext.objects.filter(
        phone_number=phone_number, updated_at__gte=cutoff
    ).first()
    if context is None:
        return None
    return get_situation_detail(context.last_situation_slug)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: PASS — 11 new tests OK (plus the 31 from Tasks 2-5).

- [ ] **Step 5: Commit**

```bash
git add backend/apps/channels/sms/handler.py backend/apps/channels/sms/tests.py
git commit -m "feat: add SMS handler orchestrator"
```

---

## Task 7: SMS webhook view and URL wiring

**Files:**
- Create: `backend/apps/channels/sms/views.py`
- Modify: `backend/apps/channels/urls.py`
- Modify: `backend/apps/channels/sms/tests.py`

**Interfaces:**
- Consumes: `apps.channels.sms.handler.handle_sms_request` (Task 6).
- Produces: URL `sms-callback` at `POST /api/channels/sms/`.

- [ ] **Step 1: Write the failing test**

Append to `backend/apps/channels/sms/tests.py`:

```python
class SmsCallbackViewTests(TestCase):
    def setUp(self):
        _create_home_safety_situation()

    @patch("apps.channels.sms.handler.send_sms")
    def test_valid_request_returns_200(self, mock_send):
        response = self.client.post(
            "/api/channels/sms/",
            {"from": "+256700000000", "text": "home"},
        )
        self.assertEqual(response.status_code, 200)
        mock_send.assert_called_once()

    def test_get_request_not_allowed(self):
        response = self.client.get("/api/channels/sms/")
        self.assertEqual(response.status_code, 405)

    @patch(
        "apps.channels.sms.views.handle_sms_request",
        side_effect=RuntimeError("boom"),
    )
    def test_unhandled_error_still_returns_200(self, mock_handle):
        response = self.client.post(
            "/api/channels/sms/",
            {"from": "+256700000000", "text": "home"},
        )
        self.assertEqual(response.status_code, 200)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.channels.sms.views'`.

- [ ] **Step 3: Implement the view**

Create `backend/apps/channels/sms/views.py`:

```python
import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .handler import handle_sms_request

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def sms_callback(request):
    phone_number = request.POST.get("from", "")
    text = request.POST.get("text", "")

    try:
        handle_sms_request(phone_number, text)
    except Exception:
        logger.exception("Unhandled error processing SMS request")

    return HttpResponse(status=200)
```

- [ ] **Step 4: Wire the URL**

Replace the contents of `backend/apps/channels/urls.py`:

```python
from django.urls import path

from .sms.views import sms_callback
from .ussd.views import ussd_callback

urlpatterns = [
    path("ussd/", ussd_callback, name="ussd-callback"),
    path("sms/", sms_callback, name="sms-callback"),
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && python manage.py test apps.channels.sms -v 2`
Expected: PASS — 3 new tests OK (plus the 42 from Tasks 2-6; 45 total in `apps.channels.sms`).

- [ ] **Step 6: Run the full backend test suite**

Run: `cd backend && python manage.py test`
Expected: PASS, no regressions (existing USSD/other app tests still green).

- [ ] **Step 7: Manual smoke test**

Run: `cd backend && python manage.py runserver`, then in another terminal:

```bash
curl -X POST http://localhost:8000/api/channels/sms/ \
  -d "from=%2B256700000000&text=home"
```

Expected: `HTTP/1.1 200 OK` with an empty body. Check the dev server log — since no real `AFRICASTALKING_API_KEY` is configured, `send_sms` will raise inside the try/except in the view; confirm the log shows `Unhandled error processing SMS request` (proving the handler ran and attempted to send) rather than a 500 to the client.

- [ ] **Step 8: Commit**

```bash
git add backend/apps/channels/sms/views.py backend/apps/channels/urls.py backend/apps/channels/sms/tests.py
git commit -m "feat: add SMS webhook view and URL routing"
```

---

## Self-Review Notes

- **Spec coverage:** Architecture (Tasks 3-7), keyword matching (Task 4), templates/content keys (Task 5), safety handling (Tasks 5-6), outbound sending (Task 2), and the automated test list from the spec's Testing section (Task 6, plus the view-layer test in Task 7) are each covered by a task. The spec's two manual/sandbox testing methods are covered by Task 7 Step 7 (curl) — the Africa's Talking sandbox simulator check is inherently manual/external and isn't reproducible as a plan step; it's the natural next manual verification once real sandbox credentials are available, noted here rather than scripted.
- **Placeholder scan:** no TBD/TODO; every step has runnable code or an exact command.
- **Type consistency:** `send_sms(phone_number, message)`, `SmsContext.last_situation_slug`, and all `templates.build_*` signatures are used identically across Tasks 5-7 as defined in their producing task.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-26-sms-channel-handler.md`. Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
