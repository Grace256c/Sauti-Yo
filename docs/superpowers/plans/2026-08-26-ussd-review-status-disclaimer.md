# USSD Unreviewed-Content Disclaimer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show a short, fixed disclaimer as the leading text of a `RightsTopic`'s content in the USSD channel whenever its `verification_status` is anything other than `"verified"`, so unreviewed legal content is no longer served indistinguishably from reviewed content.

**Architecture:** A single helper, `_prepend_unreviewed_notice(text, verification_status, language)`, prepends a fixed notice string to whatever body text a screen was about to render. It's called from the four functions that render `RightsTopic` content — `render_topic_detail`, `transition_topic_detail`, `render_safety_gate`, `transition_safety_gate` — before that text reaches `_chunked_screen`. No changes to `_chunked_screen`, `chunk_text`, or their budget math: the notice becomes ordinary body text and is paginated by the exact same mechanism as everything else.

**Tech Stack:** Django, existing `apps.channels.ussd.menus` module and its `TestCase`-based test suite (`manage.py test`, not pytest).

## Global Constraints

- Applies to `RightsTopic.verification_status` values `"review_required"`, `"expired"`, and `"archived"` — only `"verified"` renders with no notice.
- Scoped to USSD only (`backend/apps/channels/ussd/menus.py`). No changes to the DRF API, the frontend, `action_steps`, `support_contacts`, or `SupportService`'s own `verification_status`.
- The notice is prepended to raw body text before chunking, not handled as a special first-chunk case — this means it can end up alone in its own first chunk when the real content is long (each paragraph is wrapped independently near the full budget, so a short notice line plus a long first wrapped line of body text won't always fit in the same pack-chunk). This is expected, verified behavior, not a bug to route around.
- `RightsTopic.verification_status` defaults to `"review_required"` at the model level. One existing test, `SafetyGateTests.test_render_shows_safety_message`, currently creates its topic fixture without setting `verification_status` and asserts the safety message appears at `chunk_index=0` — after this change, the notice takes that chunk instead and the message moves to `chunk_index=1`, breaking the assertion. This was verified empirically by prototyping the change and running the full suite before this plan was written — it is the *only* existing test affected; every other existing test's assertions are substring-based (`assertIn`) or use the `chunk_index=9999`-clamps-to-actual-last-chunk pattern, both of which are robust to the added text. Fix: add `verification_status="verified"` to that one fixture, since the test is about safety-message content, not this feature.

---

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `backend/apps/channels/ussd/menus.py` | Modify | Add `_prepend_unreviewed_notice` helper, new `DEFAULT_COPY` key, wire into the 4 call sites |
| `backend/apps/channels/ussd/tests.py` | Modify | New `UnreviewedNoticeTests` class; fix `SafetyGateTests.setUp`'s fixture |

---

### Task 1: Unreviewed-content disclaimer

**Files:**
- Modify: `backend/apps/channels/ussd/menus.py`
- Modify: `backend/apps/channels/ussd/tests.py`

**Interfaces:**
- Consumes: `RightsTopic.verification_status` (pre-existing field, unchanged), `get_copy` (pre-existing), `_chunked_screen` (pre-existing, unchanged)
- Produces: `menus._prepend_unreviewed_notice(text: str, verification_status: str, language: str) -> str`

- [ ] **Step 1: Write the failing tests**

Append to `backend/apps/channels/ussd/tests.py` (uses `RightsTopic`, `SafetyResponse`, `UssdSession`, and `menus`, all already imported earlier in the file — no new imports needed):

```python
class UnreviewedNoticeTests(TestCase):
    def test_prepend_notice_leaves_verified_text_unchanged(self):
        text = menus._prepend_unreviewed_notice("Some text.", "verified", "en")
        self.assertEqual(text, "Some text.")

    def test_prepend_notice_adds_notice_for_review_required(self):
        text = menus._prepend_unreviewed_notice(
            "Some text.", "review_required", "en"
        )
        self.assertTrue(text.startswith("Note: not yet reviewed.\n\n"))
        self.assertIn("Some text.", text)

    def test_prepend_notice_adds_notice_for_expired_and_archived(self):
        for status in ("expired", "archived"):
            text = menus._prepend_unreviewed_notice("Some text.", status, "en")
            self.assertTrue(text.startswith("Note: not yet reviewed.\n\n"))

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

    def test_render_safety_gate_long_message_puts_notice_in_its_own_first_chunk(self):
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
        # With a long safety message, the notice doesn't fit on the same
        # screen as the start of the message - each paragraph is wrapped
        # independently near the full budget, so the notice takes its own
        # first chunk and the real message starts on chunk 1. This is
        # expected, verified behavior (see Global Constraints).
        self.assertIn("Note: not yet reviewed.", text)
        self.assertNotIn("Call the emergency line", text)
        self.assertLessEqual(len(text), 182)

        session.context["chunk_index"] = 1
        text_chunk_1, _ = menus.render_safety_gate(session)
        self.assertIn("Call the emergency line", text_chunk_1)

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && /Users/admin/Desktop/Sauti\ Yo/Sauti-Yo/.venv/bin/python manage.py test apps.channels.ussd.tests.UnreviewedNoticeTests -v 2`
Expected: FAIL — `AttributeError: module 'apps.channels.ussd.menus' has no attribute '_prepend_unreviewed_notice'`

- [ ] **Step 3: Add the new copy key**

In `backend/apps/channels/ussd/menus.py`, find the `DEFAULT_COPY` dict and add this key (placement within the dict doesn't matter, but keep it near the other short chrome strings like `"ussd.more"`):

```python
    "ussd.unreviewed_notice": "Note: not yet reviewed.",
```

- [ ] **Step 4: Add the helper function**

In `backend/apps/channels/ussd/menus.py`, add this function. Place it near `_back_from_topic` (just before `render_topic_detail`), since it's used by both `topic_detail` and `safety_gate`:

```python
def _prepend_unreviewed_notice(text, verification_status, language):
    if verification_status == "verified":
        return text
    notice = get_copy("ussd.unreviewed_notice", language)
    return f"{notice}\n\n{text}" if text else notice
```

- [ ] **Step 5: Wire it into `render_topic_detail` and `transition_topic_detail`**

Find `render_topic_detail`. It currently reads:

```python
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
```

Add one line, right after `text = topic.summary or topic.title`:

```python
def render_topic_detail(session):
    topic = RightsTopic.objects.filter(
        slug=session.context.get("topic_slug"), is_active=True
    ).first()
    if topic is None:
        return get_copy("ussd.not_found", session.language), False

    chunk_index = session.context.get("chunk_index", 0)
    menu = get_copy("ussd.topic_menu", session.language)
    text = topic.summary or topic.title
    text = _prepend_unreviewed_notice(text, topic.verification_status, session.language)
    screen, _ = _chunked_screen(text, chunk_index, menu, session.language)
    return screen, False
```

Find `transition_topic_detail`. It currently reads:

```python
def transition_topic_detail(session, user_input):
    situation_slug = session.context.get("situation_slug")
    topic_slug = session.context.get("topic_slug")
    topic = RightsTopic.objects.filter(slug=topic_slug, is_active=True).first()
    if topic is None:
        return "situation_list", {"page": 0}

    chunk_index = session.context.get("chunk_index", 0)
    text = topic.summary or topic.title
    menu = get_copy("ussd.topic_menu", session.language)
    _, is_last = _chunked_screen(text, chunk_index, menu, session.language)
```

(the rest of the function is unchanged — only these first few lines). Add the same prepend call, in the same relative position as in `render_topic_detail` — **this is the render/transition sync discipline this file already follows**: both functions must call `_chunked_screen` with identical input text, or they can disagree about where chunk boundaries fall:

```python
def transition_topic_detail(session, user_input):
    situation_slug = session.context.get("situation_slug")
    topic_slug = session.context.get("topic_slug")
    topic = RightsTopic.objects.filter(slug=topic_slug, is_active=True).first()
    if topic is None:
        return "situation_list", {"page": 0}

    chunk_index = session.context.get("chunk_index", 0)
    text = topic.summary or topic.title
    text = _prepend_unreviewed_notice(text, topic.verification_status, session.language)
    menu = get_copy("ussd.topic_menu", session.language)
    _, is_last = _chunked_screen(text, chunk_index, menu, session.language)
```

- [ ] **Step 6: Wire it into `render_safety_gate` and `transition_safety_gate`**

Find `render_safety_gate`. It currently reads:

```python
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
```

Add one line after `message = safety.message if safety else topic.summary or topic.title`:

```python
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
    message = _prepend_unreviewed_notice(message, topic.verification_status, session.language)
    chunk_index = session.context.get("chunk_index", 0)
    options = get_copy("ussd.safety_continue", session.language)
    screen, _ = _chunked_screen(message, chunk_index, options, session.language)
    return screen, False
```

Find `transition_safety_gate`. The relevant opening lines currently read:

```python
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
    options = get_copy("ussd.safety_continue", session.language)
    _, is_last = _chunked_screen(message, chunk_index, options, session.language)
```

(the rest of the function is unchanged). Add the same prepend call in the same relative position:

```python
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
    message = _prepend_unreviewed_notice(message, topic.verification_status, session.language)
    chunk_index = session.context.get("chunk_index", 0)
    options = get_copy("ussd.safety_continue", session.language)
    _, is_last = _chunked_screen(message, chunk_index, options, session.language)
```

- [ ] **Step 7: Run the new tests to verify they pass**

Run: `cd backend && /Users/admin/Desktop/Sauti\ Yo/Sauti-Yo/.venv/bin/python manage.py test apps.channels.ussd.tests.UnreviewedNoticeTests -v 2`
Expected: PASS (10 tests). This run doesn't touch `SafetyGateTests`, so it won't yet surface the one pre-existing test Step 8 fixes — that only shows up once you run the broader suite in Step 9.

- [ ] **Step 8: Fix the one pre-existing test this change affects**

In `backend/apps/channels/ussd/tests.py`, find `SafetyGateTests.setUp`. It currently reads:

```python
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
```

Add `verification_status="verified"` to the `RightsTopic.objects.create` call — this test (`test_render_shows_safety_message` and its siblings in the class) is about safety-message rendering mechanics, not this feature, so it should be decoupled from the model's `review_required` default rather than updated to expect the notice:

```python
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
```

- [ ] **Step 9: Run the full test suite**

Run: `cd backend && /Users/admin/Desktop/Sauti\ Yo/Sauti-Yo/.venv/bin/python manage.py test apps.channels -v 2`
Expected: PASS, all tests green (88 pre-existing + 10 new `UnreviewedNoticeTests` = 98 total). If anything other than the one fixture in Step 8 fails, investigate before proceeding — the Global Constraints section above states this was empirically verified to be the only affected test, so a different failure means something unexpected changed and needs to be understood, not papered over.

- [ ] **Step 10: Run the full project suite**

Run: `cd backend && /Users/admin/Desktop/Sauti\ Yo/Sauti-Yo/.venv/bin/python manage.py test`
Expected: PASS, no failures anywhere in the project.

- [ ] **Step 11: Commit**

```bash
git add backend/apps/channels/ussd/menus.py backend/apps/channels/ussd/tests.py
git commit -m "feat: show unreviewed-content notice for non-verified USSD topics"
```

---

## Post-plan notes (not part of this implementation, tracked for follow-up)

- The DRF API and citizen frontend still don't distinguish reviewed from unreviewed content — this plan only closes the gap for USSD, per the spec's explicit scope. Wiring the frontend to the live API at all is a separate, larger integration task (it currently runs on static local data).
- `SupportService.verification_status` is not surfaced anywhere either — out of scope here, same as it was in the original final review that identified this gap.
