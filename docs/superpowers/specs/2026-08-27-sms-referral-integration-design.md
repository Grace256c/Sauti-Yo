# SMS-to-Referral Integration

## Problem

The foundation work (`docs/superpowers/specs/2026-08-27-channel-referral-integration-design.md`,
implemented in `apps/referrals/services.py::create_citizen_referral()`) lets
any channel create a tracked `Referral` for a citizen when a matching
partner organisation exists. No channel calls it yet. This design wires the
SMS channel in — the first of the three channel plans the foundation spec
deferred (SMS, voice, USSD).

Today, texting SUPPORT on any situation just replies with raw
`SupportService` phone numbers (`apps/channels/sms/templates.py::build_support_reply`,
called from `handler.py`'s `followup == "support"` branch). Nothing on the
partner-portal side ever learns the citizen reached out.

## Scope

- **In scope:** SMS only.
- **In scope:** only situations where `Situation.risk_level != "high_risk"`
  — matches the foundation design's crisis-path exclusion.
- **In scope, new decision:** discreet-mode citizens (`SmsContext.discreet`)
  also bypass this flow, getting today's raw `build_support_reply` output
  unchanged. Discreet mode exists for citizens who don't want a visible
  footprint (e.g. an abuser might see the phone); a multi-message
  consent/district exchange and an org-callback offer works against that,
  and this case wasn't covered by the foundation spec's original SMS sketch.
- **In scope, new decision:** all new user-facing copy (consent prompt,
  district prompt, referral confirmation) ships **English-only**. The rest
  of the SMS handler is fully multilingual (en/lg/sw/nyn, see
  `SAFETY_CHECKIN_QUESTIONS` etc. in `templates.py`), but translating this
  new copy correctly (particularly into legal-adjacent Luganda/Swahili/
  Runyankole phrasing) needs a reviewer who isn't this design process.
  Existing multilingual replies are untouched by this plan.
- **Out of scope:** voice, USSD (separate plans). Any change to language
  tracking for other channels. Any change to the `high_risk` crisis path.

## Architecture

Three additions, all hooking into the existing `followup == "support"`
branch in `apps/channels/sms/handler.py`:

### 1. `SmsContext.pending_referral_step`

New field on `apps.channels.models.SmsContext`:

```python
pending_referral_step = models.CharField(
    max_length=20,
    choices=[
        ("consent", "Awaiting consent"),
        ("district", "Awaiting district"),
    ],
    blank=True,
    default="",
)
```

Mirrors the existing `pending_safety_check` boolean pattern but generalized
to two steps, since the consent→district exchange needs to remember *which*
step it's on, not just whether one is pending.

### 2. New keyword matchers in `apps/channels/sms/keywords.py`

```python
def match_consent_yes(text):
    normalized = _normalize(text)
    return normalized in {"yes", "y"} or bool(re.search(r"\byes\b", normalized))


def match_consent_no(text):
    normalized = _normalize(text)
    return normalized in {"no", "n"} or bool(re.search(r"\bno\b", normalized))
```

Same style as the existing `match_not_safe_answer` (word-boundary regex +
short-form exact matches). `match_consent_no` is defined for completeness
and symmetry even though the handler logic below treats "anything that
isn't a yes" as a decline (see Message Flow) — it's still useful as a named,
testable concept and mirrors how `match_not_safe_answer` is used elsewhere.

### 3. Three new templates in `apps/channels/sms/templates.py`

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

`build_referral_confirmation_reply` takes the `Referral` object directly
(not a pre-extracted dict) — it's a one-off lookup in a webhook handler, not
a loop, so the two extra attribute-access queries
(`referral.organisation.support_service.name`) are not a performance
concern, consistent with similar one-off lookups elsewhere in this handler.

## Message flow and state handling

Trigger: citizen texts something matching `keywords.match_followup() ==
"support"`, on a situation where `detail["risk_level"] != "high_risk"` and
`context.discreet` is `False`.

**Turn 1 — consent prompt.** In the existing `followup == "support"` branch:

```python
if followup == "support":
    if detail["risk_level"] == "high_risk" or context.discreet:
        _send(phone_number, templates.build_support_reply(detail, mode))
    else:
        _send(phone_number, templates.build_referral_consent_prompt())
        SmsContext.objects.filter(phone_number=phone_number).update(
            pending_referral_step="consent",
        )
```

**Turn 2 onward — hard intercept.** A new check runs early in
`handle_sms_request`, after the existing unconditional danger check and
before any other matching (situation keywords, other followups, AI
classification) — an ambiguous answer here must resolve immediately, not
fall through to being reinterpreted as something else:

```python
referral_pending = _live_context(phone_number)
if referral_pending is not None and referral_pending.pending_referral_step:
    _handle_referral_step(phone_number, referral_pending, text, language)
    return
```

`_handle_referral_step`:

- **`pending_referral_step == "consent"`:**
  - `match_consent_yes(text)` → send district prompt, step becomes
    `"district"`.
  - Anything else (explicit "no", gibberish, an attempt to state a new
    situation) → send today's raw `build_support_reply(detail, mode)`,
    clear the step to `""`. No retry loop.
- **`pending_referral_step == "district"`:** the entire message is the
  district — trimmed, no keyword matching, no validation beyond that (an
  invalid district name just means `create_citizen_referral` won't find a
  match, which degrades gracefully — see Error Handling). Calls:

  ```python
  create_citizen_referral(
      phone_number=phone_number,
      situation_slug=context.last_situation_slug,
      district=text.strip(),
      language=context.language,
      origin_channel="sms",
  )
  ```

  `context.language` is already the ISO code (`"en"`/`"lg"`/`"sw"`/`"nyn"`)
  `SmsContext` tracks today; `create_citizen_referral` normalizes it to a
  display name internally (`LANGUAGE_DISPLAY_NAMES`), so no mapping is
  needed on the SMS side.

  - Match found → `build_referral_confirmation_reply(referral)`.
  - No match → `build_support_reply(detail, mode)` (today's fallback).
  - Step cleared to `""` either way.

**Interrupt and expiry clearing.** Two existing code paths get one new
field added to what they already clear, so a stale step never survives past
where it should:

- The unconditional danger-check branch (`keywords.match_danger`) already
  clears `pending_safety_check` via `_clear_pending_safety_check` — extend
  this same function (rename to `_clear_pending_flows` for clarity, its one
  call site updates) to also clear `pending_referral_step`.
- `_live_context`'s existing 10-minute-inactivity reset (which already
  clears `last_situation_slug`, `discreet`, `pending_safety_check`) adds
  `pending_referral_step` to the same reset.

## Error handling

Every failure mode degrades to today's existing raw-phone-number reply —
never a dead end, never an unhandled exception surfacing to the webhook:

- No matching partner organisation for the given district → fallback reply
  (this is `create_citizen_referral`'s own `None` return, already handled
  gracefully by the foundation layer, including its own try/except around
  `Referral` creation).
- Consent declined or unrecognized → fallback reply, no retry loop.
- `high_risk` or discreet-mode situations never reach this code at all.

## Testing

Extends `apps/channels/sms/tests.py` in the existing style (each as its own
test method, following the file's existing `SmsContext`/`SupportService`/
`PartnerOrganisation` fixture patterns):

- consent `YES` → district prompt sent, `pending_referral_step == "district"`
- consent `NO` / unrecognized reply → fallback `build_support_reply` sent,
  `pending_referral_step == ""`
- district reply matching a partner org → confirmation reply sent,
  `pending_referral_step == ""`, a `Referral` row exists with the right
  `contact_phone`/`district`/`language`/`rights_topic`
- district reply matching no partner org → fallback reply sent,
  `pending_referral_step == ""`, no `Referral` created
- `high_risk` situation + `SUPPORT` → unchanged existing raw-reply behavior,
  flow never triggers (`pending_referral_step` stays `""`)
- discreet-mode `SUPPORT` → unchanged existing raw-reply behavior, flow
  never triggers
- a danger-word message while `pending_referral_step` is set → step cleared,
  existing danger-reply behavior unchanged
- an expired (>10 min stale) context with a leftover `pending_referral_step`
  → step cleared, next message treated as a fresh conversation

## Out of scope / explicitly deferred

- Voice and USSD integration (separate plans).
- Multilingual translation of the three new templates.
- Any language-tracking change for SMS (it already tracks language; no
  change needed here).
- Broadening partner matching when no district-specific match exists — the
  fallback is always "give the raw phone number," per the foundation
  design.
