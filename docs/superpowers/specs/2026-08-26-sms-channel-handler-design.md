# SMS Channel Handler — Design

Date: 2026-08-26
Status: Approved
Scope: `backend/apps/channels` — SMS only

## Context

Sauti Yo is a phone-first rights-to-action platform (see `Sauti Yo Project
Brief`). USSD is already built end-to-end: a DB-backed session
(`UssdSession`) drives a numbered-menu state machine through language
selection, situations, rights topics, action steps and support contacts
(`docs/superpowers/specs/2026-08-25-ussd-channel-handler-design.md`).

SMS is architecturally different from USSD, not just a smaller version of
it:

- Africa's Talking doesn't give SMS a session id — only a phone number.
- A reply is not returned synchronously in the webhook's HTTP body (unlike
  USSD's `CON`/`END` response) — the handler must call Africa's Talking's
  Send SMS API to reply.
- Messages are ~160 GSM-7 characters per segment; concatenation is possible
  but costly, so replies should be tight.
- The project brief's own minimum data model lists `InteractionSession` as
  "Minimal USSD/Voice state **where required**" — SMS is deliberately not
  included, signaling SMS should not carry a USSD-style multi-screen state
  machine.

This spec covers building the SMS channel: inbound keyword-triggered
replies, normal/discreet templates, and outbound sending. It reuses
patterns from the USSD build (per-channel `ChannelContent` copy lookup with
hardcoded fallback, plain Django view for the telco webhook) where they
fit, and diverges where SMS's constraints require it.

### Dependencies on unmerged branches

This design assumes two pieces of in-progress work land first:

- `origin/backend/rights-service-layer` — adds `apps/rights/services.py`
  with `get_situation_detail(slug)`, `get_channel_text(slug, channel,
  language)`, `get_safety_message(slug, trigger_key)`,
  `list_active_situations()`. Its docstring explicitly says these exist to
  be called by `apps.channels`.
- `origin/backend/seed-rights-to-action-data` — real `Situation`/
  `RightsTopic` seed content (`home-safety`, `land-property`, more
  presumably to follow).

SMS should depend on `apps.rights.services` rather than duplicate direct
ORM queries the way `ussd/menus.py` currently does (built before the
service layer existed) — it's the cleaner fit for the brief's "one shared
Rights-to-Action Engine" architecture, and avoids two channels each
re-implementing the same lookups.

**Known inconsistency, not fixed here:** `get_safety_message()` on
`rights-service-layer` defaults to `trigger_key="immediate_danger"`, while
the already-merged `ussd/menus.py` uses `trigger_key="default"`. SMS will
follow the service layer's `"immediate_danger"` convention since it calls
`get_safety_message()` directly; reconciling USSD's convention is out of
scope for this spec.

## Non-goals

- Wiring a "Send by SMS" trigger into the USSD menu or a future Voice IVR
  (brief's Development Priority #6, "connect all three channels" — a
  separate follow-up once this channel exists to call into).
- A USSD-style numbered menu or persisted multi-screen state machine for
  SMS.
- Language selection on SMS (no session to hold a choice in) — replies are
  English-only for v1, matching the brief's "English: complete core
  journey" language table.
- Sauti Campaigns / bulk outbound SMS — future partner capability, unrelated.
- Community Voice anonymous feedback over SMS — separate feature.

## Architecture

New/changed files, all under `backend/apps/channels/`:

- **`models.py`** — add `SmsContext` (deliberately not `SmsSession`, to
  signal this is not a state machine):
  - `phone_number` (unique)
  - `last_situation_slug`
  - `updated_at` (auto-now)

  Holds just enough memory for one natural follow-up turn (`STEPS`,
  `SUPPORT`) without requiring the user to repeat the topic keyword. Not a
  screen/state tracker like `UssdSession`.

- **`sms/keywords.py`** — pure functions matching inbound text to intent:
  - `match_situation(text) -> slug | None` — checks a per-slug word list
    (e.g. `home-safety: [home, abuse, husband, wife, beat, unsafe]`,
    `work: [work, job, salary, fired, boss]`, `land: [land, plot, evict,
    property]`, `child: [child, school, minor, kid]`).
  - `match_danger(text) -> bool` — checks a danger-word list (`danger,
    weapon, threatened, emergency, hurt, "right now"`), independent of
    situation matching — a danger word short-circuits regardless of
    whatever else is in the message.
  - `match_followup(text) -> "steps" | "support" | None`.
  - `match_help(text) -> bool` — text contains `HELP` as a standalone word
    (not as a substring of other matched text). Checked independently of
    `match_situation`/`match_followup` — general help doesn't require a
    situation to already be known, mirroring USSD's "Get help now"
    main-menu shortcut, which is likewise reachable without navigating a
    situation first.
  - `match_discreet(text) -> bool` — text contains `DISCREET`.

- **`sms/templates.py`** — builds reply text from a `situation_detail` dict
  (the shape `get_situation_detail()` returns):
  - `build_situation_reply(detail, mode)` — explanation + first action
    step + one support contact, `mode` = `"normal"` or `"discreet"`.
    Discreet wording omits the situation name/topic and support-service
    name, using neutral phrasing ("a support contact" instead of "Sauti
    116 - Child & GBV Helpline").
  - `build_support_reply(detail)` — support services for the situation
    (name + phone), or the two emergency numbers if none are linked.
  - `build_safety_reply(detail)` — the situation's `get_safety_message()`
    text verbatim, never templated or paraphrased.
  - `build_unmatched_reply()` — fixed hardcoded fallback (see below).
  - `build_followup_expired_reply()` — fixed hardcoded fallback.

  Copy lookup follows USSD's pattern: try `get_channel_text(slug, "sms",
  "en")` first, fall back to a hardcoded English string if unseeded. Stays
  under the SMS segment budget (`SMS_SEGMENT_BUDGET = 160`, matching
  USSD's `SCREEN_BUDGET` pattern); templates are written tight enough that
  the common case is 1 segment, capping at 2 rather than chunking further.

- **`sms/handler.py`** — `handle_sms_request(phone_number, text) ->
  None`. The orchestrator:
  1. `match_danger(text)` → if true, send `build_safety_reply()` for the
     situation in `SmsContext` if one's live, else a general safety reply
     pointing to 999/112 and Sauti 116, and return. Checked first,
     unconditionally.
  2. `match_help(text)` → if true, send `build_support_reply()` using the
     general emergency-services list (no situation context needed —
     matches USSD's "Get help now" shortcut), and return.
  3. `match_situation(text)` → if matched, send
     `build_situation_reply(detail, "discreet" if match_discreet(text)
     else "normal")`, upsert `SmsContext(phone_number,
     last_situation_slug=slug)`, return.
  4. `match_followup(text)` → if matched and `SmsContext` exists and
     `updated_at` is within 10 minutes, send `build_support_reply()` (for
     `"support"`) or re-send the action-steps portion (for `"steps"`);
     if the context is missing/expired, send
     `build_followup_expired_reply()`.
  5. Nothing matched → send `build_unmatched_reply()`.

  Every branch ends by calling `africastalking_client.send_sms(phone_number,
  message)` — the function's return value is unused; failures raise (no
  retry/backoff logic — out of scope for v1, matches USSD's "no Redis/
  Celery" constraint).

- **`sms/views.py`** — plain Django view (DRF doesn't fit for the same
  reason as USSD: form-encoded webhook body, not JSON). Parses `from`/
  `text` from `request.POST`, calls `handle_sms_request`, returns a bare
  `HttpResponse(status=200)` — Africa's Talking's inbound-SMS webhook
  doesn't read the response body.

- **`apps/channels/urls.py`** — add `path("sms/", sms_views.sms_callback,
  name="sms-callback")`.

- **`africastalking_client.py`** — `send_sms(phone_number, message)`, a
  thin wrapper around the `africastalking` SDK's SMS service. Shared
  infrastructure — USSD/Voice will call the same function once cross-channel
  SMS triggers are wired in (Non-goals).

## Keyword matching

Situation keywords are matched as substrings/word-boundaries against the
per-slug word lists in `sms/keywords.py`, case-insensitive. This is a
static list (not derived from `Situation.title`/`slug` at query time)
because the brief specifies concrete discovery keywords (`WORK, LAND,
CHILD, HELP, POLICY`) that don't literally appear in the seeded situation
titles (e.g. `home-safety`'s title is "I don't feel safe at home", not
"HOME"). `HELP` is matched by its own `match_help()` (see Architecture),
independent of situation matching. `POLICY` is not handled in v1
(Policy-to-People is future scope per the brief) — falls through to
unmatched.

If a message matches more than one situation's word list, the first match
in slug-alphabetical order wins — simple and deterministic; ambiguous
real-world phrasing is expected to be rare enough not to warrant a
disambiguation reply for v1.

## Templates and content keys

`build_situation_reply` and friends look up copy via the existing
`get_channel_text(slug, "sms", "en")` convention
(`{slug_with_underscores}_intro`), consistent with
`docs/superpowers/specs/2026-08-25-ussd-channel-handler-design.md`'s
approach and the `docs/channel-content-convention` note. Since no SMS
`ChannelContent` rows are seeded yet, every template has a hardcoded
English fallback so the channel works before content seeding catches up —
same reasoning as USSD's `DEFAULT_COPY`.

Fixed (non-`ChannelContent`) fallback strings:

- Unmatched: `"You can text HOME, WORK, LAND or CHILD for help, or HELP
  for support."`
- Follow-up expired/missing context: `"Please first text HOME, WORK, LAND
  or CHILD to tell us what's going on, then text STEPS or SUPPORT."`
- General safety (no situation context): `"If you are in immediate
  danger, call the Police on 999 or 112 now. Free support: Sauti 116."`

## Safety handling

`match_danger()` is checked before situation matching, every request, no
exceptions — mirrors the brief's "High-risk trigger -> predefined safe
response" pathway. The safety reply always comes from
`get_safety_message()` (a human-reviewed `SafetyResponse` row) when a
situation context exists, never from `sms/templates.py` composing its own
wording — matching the brief's "Do not let AI override approved high-risk
content" and "AI must not... invent" constraints, even though nothing here
touches AI directly; the same discipline applies to any dynamic composition
of safety-critical text.

No SMS is ever sent automatically as a side effect of danger detection
beyond the one safety reply itself (no auto-contacting police/relatives,
no location implication) — matches the brief's Section 13 constraints
directly.

## Testing

- **Automated**: Django `TestCase` calling `handle_sms_request()` directly,
  mocking `africastalking_client.send_sms` to capture the composed message
  instead of calling the real SDK. Cases:
  - Situation keyword → correct normal-mode reply.
  - Situation keyword + `DISCREET` → discreet-mode reply omits topic/service
    names.
  - Danger word → safety reply, both with and without a live `SmsContext`.
  - `STEPS`/`SUPPORT` within the 10-minute window → correct follow-up
    reply.
  - `STEPS`/`SUPPORT` with no context or an expired one → expired-context
    reply.
  - Unmatched text → unmatched reply.
  - `HELP` alone → emergency support reply.
  A thin view-layer test posts Africa's-Talking-shaped form data and
  asserts a 200 response.
- **Manual, no telco**: `curl -X POST localhost:8000/api/channels/sms/ -d
  "from=+256700000000&text=home"`, inspecting logs/mocked send calls for
  the composed reply — same reasoning as USSD's curl-based manual check.
- **Africa's Talking SMS sandbox**: sandbox account's simulator can send an
  inbound SMS to the configured shortcode and hit the callback URL for
  real, and `send_sms` can be pointed at the sandbox to see a real reply
  arrive on a registered test number — closest check to the "SMS arrives
  on the real phone" demo moment before going live.
