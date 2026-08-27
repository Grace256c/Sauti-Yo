# SMS-to-Referral Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the SMS channel's SUPPORT keyword into `apps.referrals.services.create_citizen_referral()` (already built and merged) via a consent/district exchange, per `docs/superpowers/specs/2026-08-27-sms-referral-integration-design.md`.

**Architecture:** A new `SmsContext.pending_referral_step` field tracks a two-step exchange ("consent" then "district"), intercepted early in `handle_sms_request` — after the unconditional danger check, before any other keyword/AI matching — so an ambiguous reply always resolves immediately rather than being reinterpreted as something else. The existing `followup == "support"` branch is the only entry point into the flow, gated by `Situation.risk_level != "high_risk"` and `SmsContext.discreet is False`.

**Tech Stack:** Django (existing project), Django's built-in test runner (`manage.py test`), PostgreSQL.

## Global Constraints

- `high_risk` situations and discreet-mode contexts (`SmsContext.discreet`) never enter this flow — they keep today's raw `build_support_reply` output completely unchanged.
- All new user-facing copy (consent prompt, district prompt, referral confirmation) is English-only — do not add translation dict entries for lg/sw/nyn.
- An ambiguous or declined consent reply, or a district with no matching partner organisation, always falls back to today's raw `build_support_reply` — never a retry loop, never a dead end.
- `SmsContext.language` is already an ISO code (`"en"`/`"lg"`/`"sw"`/`"nyn"`) and is passed straight through to `create_citizen_referral(language=...)` — it normalizes internally. No mapping is added on the SMS side.
- The `pending_referral_step` intercept in `handle_sms_request` runs after the unconditional danger check and before every other matcher (situation keywords, other followups, AI classification).

---

## Task 1: `SmsContext.pending_referral_step` field

**Files:**
- Modify: `backend/apps/channels/models.py`
- Create: `backend/apps/channels/migrations/0012_smscontext_pending_referral_step.py` (via `makemigrations`)
- Test: `backend/apps/channels/sms/tests.py`

**Interfaces:**
- Consumes: `apps.channels.models.SmsContext` (existing).
- Produces: `SmsContext.pending_referral_step` — `CharField(max_length=20, choices=[("consent", ...), ("district", ...)], blank=True, default="")`.

- [ ] **Step 1: Write the failing test**

Add to `backend/apps/channels/sms/tests.py`, inside the existing `SmsContextModelTests` class (after `test_language_defaults_to_english`, which ends around line 104):

```python
    def test_pending_referral_step_defaults_to_blank(self):
        context = SmsContext.objects.create(
            phone_number="+256700000002",
        )
        self.assertEqual(context.pending_referral_step, "")

    def test_pending_referral_step_can_be_set(self):
        context = SmsContext.objects.create(
            phone_number="+256700000003",
            pending_referral_step="consent",
        )
        self.assertEqual(context.pending_referral_step, "consent")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend && python3 manage.py test apps.channels.sms.tests.SmsContextModelTests -v 2 --keepdb`
Expected: FAIL with `TypeError: 'pending_referral_step' is an invalid keyword argument for this function`

- [ ] **Step 3: Add the field**

In `backend/apps/channels/models.py`, in the `SmsContext` class, replace:

```python
    discreet = models.BooleanField(default=False)
    pending_safety_check = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
```

with:

```python
    discreet = models.BooleanField(default=False)
    pending_safety_check = models.BooleanField(default=False)
    pending_referral_step = models.CharField(
        max_length=20,
        choices=[
            ("consent", "Awaiting consent"),
            ("district", "Awaiting district"),
        ],
        blank=True,
        default="",
    )
    updated_at = models.DateTimeField(auto_now=True)
```

- [ ] **Step 4: Generate and apply the migration**

Run: `cd backend && python3 manage.py makemigrations channels`
Expected: creates `backend/apps/channels/migrations/0012_smscontext_pending_referral_step.py`, depending on `0011_merge_20260827_1652` (the current single migration leaf in this app — confirm the generated file's `dependencies` names it).

Run: `cd backend && python3 manage.py migrate channels`
Expected: `Applying channels.0012_smscontext_pending_referral_step... OK`

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd backend && python3 manage.py test apps.channels.sms.tests.SmsContextModelTests -v 2 --keepdb`
Expected: PASS (6 tests: the 4 pre-existing plus the 2 new ones)

- [ ] **Step 6: Commit**

```bash
git add backend/apps/channels/models.py backend/apps/channels/migrations/0012_smscontext_pending_referral_step.py backend/apps/channels/sms/tests.py
git commit -m "feat: add SmsContext.pending_referral_step for the referral consent/district flow"
```

---

## Task 2: Keyword matchers and reply templates

**Files:**
- Modify: `backend/apps/channels/sms/keywords.py`
- Modify: `backend/apps/channels/sms/templates.py`
- Test: `backend/apps/channels/sms/tests.py`

**Interfaces:**
- Consumes: nothing new (pure additions to existing modules).
- Produces:
  - `apps.channels.sms.keywords.match_consent_yes(text: str) -> bool`
  - `apps.channels.sms.keywords.match_consent_no(text: str) -> bool`
  - `apps.channels.sms.templates.build_referral_consent_prompt() -> str`
  - `apps.channels.sms.templates.build_referral_district_prompt() -> str`
  - `apps.channels.sms.templates.build_referral_confirmation_reply(referral: Referral) -> str` — reads `referral.organisation.support_service.name` and `referral.reference`.

- [ ] **Step 1: Write the failing tests**

Add to `backend/apps/channels/sms/tests.py`, right after the existing `MatchNotSafeAnswerTests` class (which ends around line 149, right before `class KeywordMatchingTests`):

```python
class MatchConsentTests(TestCase):
    def test_match_consent_yes_matches_bare_yes(self):
        self.assertTrue(match_consent_yes("yes"))

    def test_match_consent_yes_matches_yes_in_sentence(self):
        self.assertTrue(match_consent_yes("yes please connect me"))

    def test_match_consent_yes_matches_short_form(self):
        self.assertTrue(match_consent_yes("y"))

    def test_match_consent_yes_false_for_no(self):
        self.assertFalse(match_consent_yes("no"))

    def test_match_consent_no_matches_bare_no(self):
        self.assertTrue(match_consent_no("no"))

    def test_match_consent_no_matches_short_form(self):
        self.assertTrue(match_consent_no("n"))

    def test_match_consent_no_false_for_yes(self):
        self.assertFalse(match_consent_no("yes"))
```

Add `match_consent_yes` and `match_consent_no` to the existing keyword import block near the top of the file:

```python
from apps.channels.sms.keywords import (
    match_consent_no,
    match_consent_yes,
    match_danger,
    match_discreet,
    match_followup,
    match_help,
    match_language_command,
    match_not_safe_answer,
    match_situation,
)
```

Add a new test class right after `FixedReplyTests` (which ends around line 427, right before `class HandleSmsRequestTests`):

```python
class ReferralTemplateTests(TestCase):
    def test_build_referral_consent_prompt(self):
        self.assertEqual(
            templates.build_referral_consent_prompt(),
            templates.REFERRAL_CONSENT_PROMPT,
        )

    def test_build_referral_district_prompt(self):
        self.assertEqual(
            templates.build_referral_district_prompt(),
            templates.REFERRAL_DISTRICT_PROMPT,
        )

    def test_build_referral_confirmation_reply(self):
        service = SupportService.objects.create(
            name="Referral Template Test Partner",
            service_type="Legal Aid",
            verification_status="verified",
            is_active=True,
        )
        organisation = PartnerOrganisation.objects.create(
            support_service=service,
            organisation_type="legal_aid",
            is_active=True,
        )
        referral = Referral.objects.create(
            reference="SY-REF-TEMPLATE-TEST",
            organisation=organisation,
            citizen_consent_to_share=True,
            status="new",
        )

        message = templates.build_referral_confirmation_reply(referral)

        self.assertIn("Referral Template Test Partner", message)
        self.assertIn("SY-REF-TEMPLATE-TEST", message)
```

This test needs two new imports at the top of `backend/apps/channels/sms/tests.py`:

```python
from apps.partners.models import PartnerOrganisation
from apps.referrals.models import Referral
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && python3 manage.py test apps.channels.sms.tests.MatchConsentTests apps.channels.sms.tests.ReferralTemplateTests -v 2 --keepdb`
Expected: FAIL — `ImportError: cannot import name 'match_consent_yes'` (and similar for the others)

- [ ] **Step 3: Add the keyword matchers**

In `backend/apps/channels/sms/keywords.py`, add right after the `match_not_safe_answer` function (which ends right before the `LANGUAGE_COMMANDS` dict):

```python
def match_consent_yes(text):
    normalized = _normalize(text)
    return normalized in {"yes", "y"} or bool(re.search(r"\byes\b", normalized))


def match_consent_no(text):
    normalized = _normalize(text)
    return normalized in {"no", "n"} or bool(re.search(r"\bno\b", normalized))
```

- [ ] **Step 4: Add the templates**

In `backend/apps/channels/sms/templates.py`, add at the end of the file (after `build_followup_expired_reply`):

```python


REFERRAL_CONSENT_PROMPT = (
    "An organisation may be able to help you directly. Reply YES to let "
    "them contact you, or NO for just the number."
)
REFERRAL_DISTRICT_PROMPT = "Which district are you in?"


def build_referral_consent_prompt():
    return REFERRAL_CONSENT_PROMPT


def build_referral_district_prompt():
    return REFERRAL_DISTRICT_PROMPT


def build_referral_confirmation_reply(referral):
    return (
        f"You're referred to {referral.organisation.support_service.name}. "
        f"Reference {referral.reference}. They may call you on this number."
    )
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd backend && python3 manage.py test apps.channels.sms.tests.MatchConsentTests apps.channels.sms.tests.ReferralTemplateTests -v 2 --keepdb`
Expected: PASS (10 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/apps/channels/sms/keywords.py backend/apps/channels/sms/templates.py backend/apps/channels/sms/tests.py
git commit -m "feat: add consent keyword matchers and referral reply templates"
```

---

## Task 3: Wire the consent/district flow into `handle_sms_request`

**Files:**
- Modify: `backend/apps/channels/sms/handler.py`
- Test: `backend/apps/channels/sms/tests.py`

**Interfaces:**
- Consumes:
  - `apps.channels.models.SmsContext.pending_referral_step` (Task 1)
  - `apps.channels.sms.keywords.match_consent_yes` / `match_consent_no` (Task 2)
  - `apps.channels.sms.templates.build_referral_consent_prompt` / `build_referral_district_prompt` / `build_referral_confirmation_reply` (Task 2)
  - `apps.referrals.services.create_citizen_referral(*, phone_number, situation_slug, district, language, origin_channel) -> Referral | None` (already merged, from the foundation plan)
- Produces: the complete consent → district → referral behavior described in the design spec's Message Flow section. No new public interfaces — this is the integration point.

- [ ] **Step 1: Write the failing tests**

Add to `backend/apps/channels/sms/tests.py`, as a new class at the end of the file (after the existing `SafetyCheckinTests` class). First, extend the existing `apps.partners.models` import added in Task 2 (or add it now if Task 2 didn't already need it) to include `PartnerServiceConfiguration` and `PartnerVerificationRequest`:

```python
from apps.partners.models import (
    PartnerOrganisation,
    PartnerServiceConfiguration,
    PartnerVerificationRequest,
)
```

`RightsTopic`, `Situation`, and `SituationRightsTopic` are already imported at the top of this file from `apps.rights.models` (see the file's existing import block) — no changes needed there. `Referral` was already imported in Task 2.

Now add the test class:

```python
class ReferralConsentFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.situation = _create_problem_at_work_situation()

        RightsTopic.objects.filter(slug="workplace-rights").update(
            rights_category="work-employment",
        )

        service = SupportService.objects.create(
            name="Referral Flow Test Partner",
            service_type="Legal Aid",
            verification_status="verified",
            is_active=True,
        )
        self.organisation = PartnerOrganisation.objects.create(
            support_service=service,
            organisation_type="legal_aid",
            is_active=True,
            is_test=False,
        )
        PartnerServiceConfiguration.objects.create(
            organisation=self.organisation,
            rights_categories=["work-employment"],
            languages=["English"],
            support_channels=["phone"],
            districts_served=["Kampala"],
            accepting_referrals=True,
        )
        PartnerVerificationRequest.objects.create(
            organisation=self.organisation,
            status="verified",
        )

    @patch("apps.channels.sms.handler.send_sms")
    def test_support_on_standard_situation_sends_consent_prompt(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000", last_situation_slug="problem-at-work"
        )
        handle_sms_request("+256700000000", "SUPPORT")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.REFERRAL_CONSENT_PROMPT)
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.pending_referral_step, "consent")

    @patch("apps.channels.sms.handler.send_sms")
    def test_consent_yes_sends_district_prompt(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000",
            last_situation_slug="problem-at-work",
            pending_referral_step="consent",
        )
        handle_sms_request("+256700000000", "yes")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.REFERRAL_DISTRICT_PROMPT)
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.pending_referral_step, "district")

    @patch("apps.channels.sms.handler.send_sms")
    def test_consent_no_falls_back_to_raw_support_reply(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000",
            last_situation_slug="problem-at-work",
            pending_referral_step="consent",
        )
        handle_sms_request("+256700000000", "no")
        message = mock_send.call_args[0][1]
        self.assertNotEqual(message, templates.REFERRAL_DISTRICT_PROMPT)
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.pending_referral_step, "")

    @patch("apps.channels.sms.handler.send_sms")
    def test_consent_unrecognized_falls_back_to_raw_support_reply(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000",
            last_situation_slug="problem-at-work",
            pending_referral_step="consent",
        )
        handle_sms_request("+256700000000", "maybe later")
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.pending_referral_step, "")

    @patch("apps.channels.sms.handler.send_sms")
    def test_district_match_sends_confirmation_and_creates_referral(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000",
            last_situation_slug="problem-at-work",
            pending_referral_step="district",
            language="en",
        )
        handle_sms_request("+256700000000", "Kampala")
        message = mock_send.call_args[0][1]
        self.assertIn("Referral Flow Test Partner", message)
        self.assertIn("SY-REF-", message)
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.pending_referral_step, "")

        referral = Referral.objects.get(organisation=self.organisation)
        self.assertEqual(referral.contact_phone, "+256700000000")
        self.assertEqual(referral.district, "Kampala")

    @patch("apps.channels.sms.handler.send_sms")
    def test_district_no_match_falls_back_to_raw_support_reply(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000",
            last_situation_slug="problem-at-work",
            pending_referral_step="district",
            language="en",
        )
        handle_sms_request("+256700000000", "Gulu")
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.pending_referral_step, "")
        self.assertEqual(Referral.objects.count(), 0)

    @patch("apps.channels.sms.handler.send_sms")
    def test_high_risk_support_bypasses_consent_flow(self, mock_send):
        _create_home_safety_situation()
        SmsContext.objects.create(
            phone_number="+256700000001", last_situation_slug="home-safety"
        )
        handle_sms_request("+256700000001", "SUPPORT")
        message = mock_send.call_args[0][1]
        self.assertNotEqual(message, templates.REFERRAL_CONSENT_PROMPT)
        context = SmsContext.objects.get(phone_number="+256700000001")
        self.assertEqual(context.pending_referral_step, "")

    @patch("apps.channels.sms.handler.send_sms")
    def test_discreet_support_bypasses_consent_flow(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000002",
            last_situation_slug="problem-at-work",
            discreet=True,
        )
        handle_sms_request("+256700000002", "SUPPORT")
        message = mock_send.call_args[0][1]
        self.assertNotEqual(message, templates.REFERRAL_CONSENT_PROMPT)
        context = SmsContext.objects.get(phone_number="+256700000002")
        self.assertEqual(context.pending_referral_step, "")

    @patch("apps.channels.sms.handler.send_sms")
    def test_danger_word_while_pending_referral_step_clears_it(self, mock_send):
        SmsContext.objects.create(
            phone_number="+256700000000",
            last_situation_slug="problem-at-work",
            pending_referral_step="district",
        )
        handle_sms_request("+256700000000", "there's a weapon here right now")
        context = SmsContext.objects.get(phone_number="+256700000000")
        self.assertEqual(context.pending_referral_step, "")

    @patch("apps.channels.sms.handler.send_sms")
    def test_expired_context_clears_pending_referral_step(self, mock_send):
        context = SmsContext.objects.create(
            phone_number="+256700000000",
            last_situation_slug="problem-at-work",
            pending_referral_step="district",
        )
        SmsContext.objects.filter(pk=context.pk).update(
            updated_at=timezone.now() - timedelta(minutes=11),
        )
        handle_sms_request("+256700000000", "Kampala")
        message = mock_send.call_args[0][1]
        self.assertEqual(message, templates.build_followup_expired_reply())
        context.refresh_from_db()
        self.assertEqual(context.pending_referral_step, "")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && python3 manage.py test apps.channels.sms.tests.ReferralConsentFlowTests -v 2 --keepdb`
Expected: FAIL — most tests will fail because `pending_referral_step` is never read or acted on yet (e.g. `test_support_on_standard_situation_sends_consent_prompt` fails because the SUPPORT reply is still the raw phone number list, not `REFERRAL_CONSENT_PROMPT`).

- [ ] **Step 3: Add the import**

In `backend/apps/channels/sms/handler.py`, add to the imports at the top:

```python
from apps.referrals.services import create_citizen_referral
```

- [ ] **Step 4: Rename and extend the pending-state clearing helper**

Replace:

```python
def _clear_pending_safety_check(phone_number):
    SmsContext.objects.filter(
        phone_number=phone_number, pending_safety_check=True
    ).update(pending_safety_check=False)
```

with:

```python
def _clear_pending_flows(phone_number):
    SmsContext.objects.filter(phone_number=phone_number).update(
        pending_safety_check=False,
        pending_referral_step="",
    )
```

Update its one call site — replace:

```python
        _clear_pending_safety_check(phone_number)
```

with:

```python
        _clear_pending_flows(phone_number)
```

- [ ] **Step 5: Extend the follow-up-window expiry reset**

In `_live_context`, replace:

```python
    if context.updated_at < cutoff:
        context.last_situation_slug = ""
        context.discreet = False
        context.pending_safety_check = False
        context.save(
            update_fields=[
                "last_situation_slug",
                "discreet",
                "pending_safety_check",
            ]
        )
        return None
```

with:

```python
    if context.updated_at < cutoff:
        context.last_situation_slug = ""
        context.discreet = False
        context.pending_safety_check = False
        context.pending_referral_step = ""
        context.save(
            update_fields=[
                "last_situation_slug",
                "discreet",
                "pending_safety_check",
                "pending_referral_step",
            ]
        )
        return None
```

- [ ] **Step 6: Add `_handle_referral_step`**

Add this function right before `def handle_sms_request(phone_number, text):`:

```python
def _handle_referral_step(phone_number, context, text):
    if context.pending_referral_step == "consent":
        if keywords.match_consent_yes(text):
            _send(phone_number, templates.build_referral_district_prompt())
            SmsContext.objects.filter(phone_number=phone_number).update(
                pending_referral_step="district",
            )
            return

        detail = get_situation_detail(context.last_situation_slug)
        mode = "discreet" if context.discreet else "normal"
        _send(phone_number, templates.build_support_reply(detail, mode))
        SmsContext.objects.filter(phone_number=phone_number).update(
            pending_referral_step="",
        )
        return

    district = text.strip()
    referral = create_citizen_referral(
        phone_number=phone_number,
        situation_slug=context.last_situation_slug,
        district=district,
        language=context.language,
        origin_channel="sms",
    )

    detail = get_situation_detail(context.last_situation_slug)
    mode = "discreet" if context.discreet else "normal"

    if referral is not None:
        _send(
            phone_number,
            templates.build_referral_confirmation_reply(referral),
        )
    else:
        _send(phone_number, templates.build_support_reply(detail, mode))

    SmsContext.objects.filter(phone_number=phone_number).update(
        pending_referral_step="",
    )
```

- [ ] **Step 7: Insert the intercept in `handle_sms_request`**

In `handle_sms_request`, right after the danger-check block (after `_clear_pending_flows(phone_number)` / `return`) and before the existing `pending = _live_context(phone_number)` line that starts the safety-check-in handling, insert:

```python
    referral_pending = _live_context(phone_number)
    if referral_pending is not None and referral_pending.pending_referral_step:
        _handle_referral_step(phone_number, referral_pending, text)
        return

```

- [ ] **Step 8: Modify the `followup == "support"` branch**

Note: by this step, `_handle_referral_step` (added in Step 6) also contains a `mode = "discreet" if context.discreet else "normal"` line, so that single line is no longer unique in the file — use the full block below (inside `handle_sms_request`'s `followup` handling, identifiable by the preceding `build_followup_expired_reply` guard and the trailing `else:` that leads into the STEPS branch) as the anchor.

Replace:

```python
        detail = get_situation_detail(context.last_situation_slug)
        if detail is None:
            _send(phone_number, templates.build_followup_expired_reply(language))
            return
        mode = "discreet" if context.discreet else "normal"
        if followup == "support":
            _send(phone_number, templates.build_support_reply(detail, mode))
        else:
```

with:

```python
        detail = get_situation_detail(context.last_situation_slug)
        if detail is None:
            _send(phone_number, templates.build_followup_expired_reply(language))
            return
        mode = "discreet" if context.discreet else "normal"
        if followup == "support":
            if detail["risk_level"] == "high_risk" or context.discreet:
                _send(phone_number, templates.build_support_reply(detail, mode))
            else:
                _send(phone_number, templates.build_referral_consent_prompt())
                SmsContext.objects.filter(phone_number=phone_number).update(
                    pending_referral_step="consent",
                )
        else:
```

- [ ] **Step 9: Run the tests to verify they pass**

Run: `cd backend && python3 manage.py test apps.channels.sms.tests.ReferralConsentFlowTests -v 2 --keepdb`
Expected: PASS (10 tests)

- [ ] **Step 10: Run the full SMS test suite to confirm no regression**

Run: `cd backend && python3 manage.py test apps.channels.sms -v 2 --keepdb`
Expected: PASS — every pre-existing test (safety check-in, language, AI fallback, etc.) still passes unchanged, since `home-safety` (high_risk) and discreet-mode SUPPORT tests never enter the new flow, and no other pre-existing test uses SUPPORT on a standard-risk, non-discreet context.

- [ ] **Step 11: Run the full project test suite**

Run: `cd backend && python3 manage.py test -v 2 --keepdb`
Expected: PASS

- [ ] **Step 12: Commit**

```bash
git add backend/apps/channels/sms/handler.py backend/apps/channels/sms/tests.py
git commit -m "feat: wire SMS SUPPORT keyword into the citizen referral consent/district flow"
```
