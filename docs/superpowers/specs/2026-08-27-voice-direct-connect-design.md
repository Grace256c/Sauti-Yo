# Voice Direct-Connect to Support — Design

Date: 2026-08-27
Status: Approved
Scope: `backend/apps/channels/voice` — extends the already-built voice channel handler

## Context

The voice channel (`docs/superpowers/specs/2026-08-27-voice-channel-handler-design.md`)
currently only *speaks* support/emergency phone numbers — via
`templates.build_support_reply()` in the post-reply menu, and via
`templates.build_safety_reply()` on the crisis/danger-word path. The caller
has to remember or write down a number and dial it themselves afterward.

Africa's Talking's Voice API has a `<Dial>` verb that connects the live
call directly to another phone number. This spec adds a "press to connect"
option everywhere a number is currently spoken, so a caller can be
connected immediately instead of having to place a second call.

This is purely additive to `apps/channels/voice/*`. No changes to
`apps/channels/sms/*` or `apps/rights/*` — voice continues to only import
from them, per the base voice design's constraint.

## Non-goals

- Recording connected calls. A caller disclosing domestic violence,
  eviction, or workplace abuse hasn't consented to being recorded, and
  storing that audio is a real liability/safety risk with no existing
  consent or retention handling anywhere in this project. `record="false"`
  always.
- Dialing multiple numbers in sequence if the first doesn't answer. Only
  the same "primary" number the existing spoken replies already present
  first is ever dialed — matches what a caller already hears today, no new
  number-selection logic.
- A retry/alternate-options menu on no-answer. Falls back to speaking the
  number and ending the call — never worse off than the call is today
  without this feature.
- Any SIP/WebRTC/call-center distribution use of `<Dial>` (multiple agents,
  `sequential`, `callerId`) — this is a single caller reaching a single
  fixed support number, not a call-routing system.

## Architecture

### New IVR XML (`voice/ivr.py`)

- **`build_dial_xml(phone_number, fallback_text)`** — `<Dial
  phoneNumbers="{phone_number}" record="false" maxDuration="300"/>`
  followed by `<Say>{fallback_text}</Say>` in the same `<Response>`. Per
  Africa's Talking's own documented behavior ("No action will be executed
  after this if the call is picked"), the trailing `<Say>` only plays if
  the dial *isn't* answered — no second webhook round-trip needed to
  detect and handle a no-answer. **Assumption flagged for sandbox
  verification**, matching `ivr.py`'s existing disclaimer for other AT XML
  specifics: this needs confirming against a real sandbox call before
  relying on it, since the file's other verbs were also written from
  documented shapes, not a verified live account.
- **`build_safety_reply_with_connect_xml(safety_text)`** — `<Say>` the
  safety text, then a `<GetDigits>` offering "press 1 to connect now, stay
  on the line to end the call." Same shape as the existing
  `build_reply_xml`, different prompt copy and used on the crisis path
  instead of the post-reply path.
- **`build_menu_with_connect_xml(...)`**: no new function needed here —
  the post-reply menu's prompt copy (`POST_REPLY_MENU_PROMPT`) is updated
  to mention a third option, and `build_reply_xml` is unchanged
  structurally (still `<Say>` + `<GetDigits>`).

### Selecting which number to dial (`voice/handler.py`)

A new private helper, `_primary_support_phone_number(detail)`, mirrors —
without importing or modifying — the exact selection logic
`sms/templates.py` already uses internally:
- If `detail` is given: the first support service with a phone number
  across the situation's linked rights topics (same walk order as
  `templates._first_support_service`).
- If `detail` is `None` (the crisis path with no situation matched yet):
  the first `SupportService` where `is_emergency_service=True,
  is_active=True`, ordered by name — the same direct query
  `templates.build_support_reply()` already makes for its no-detail case,
  and the same "no service-layer helper exists for this lookup" exception
  the base voice design already established for the emergency list.

Returns `None` if no phone number is available either way, in which case
the caller falls back to today's behavior (hearing the number/reply, no
connect option offered) rather than erroring.

### New session state: `awaiting_crisis_connect_digit`

Today, three separate places in `handler.py` speak the safety reply and
immediately end the call in the same turn:
1. The unconditional danger-word short-circuit in `_handle_recording`.
2. Pressing "2" (not safe) in `_handle_safety_digit`.
3. The fail-closed path in `_handle_safety_digit` after the bounded
   re-prompt is exhausted.

All three currently call `end_session(session)` and return
`build_final_message_xml(...)`. Offering a connect option turns this from
a one-turn "speak and hang up" into a two-turn "speak, then wait for a
digit" — so all three are refactored to go through one new shared helper,
`_offer_crisis_connect(session, detail)`:
- Does **not** end the session yet.
- Sets `state = "awaiting_crisis_connect_digit"`, `context = {"slug":
  detail["slug"] if detail else None}`.
- Returns `build_safety_reply_with_connect_xml(templates.build_safety_reply(detail))`.

A new digit handler, `_handle_crisis_connect_digit(session, digit)`:
- `digit == "1"`: look up `detail` again from `context["slug"]` (may be
  `None`), resolve `_primary_support_phone_number(detail)`. If a number is
  found, `end_session(session)` and return `build_dial_xml(phone,
  fallback_text)` where `fallback_text` is a short "that number isn't
  answering right now, you can reach them directly at `{phone}`" message.
  If no number is available (edge case — no `SupportService` rows at
  all), `end_session(session)` and return `build_closing_xml()` — the
  safety message was already spoken in full in the previous turn, nothing
  further to add.
- Anything else (including empty digit, matching this spec's earlier
  decision): `end_session(session)`, `build_closing_xml()` — the call just
  ends, exactly like it does today without this feature.

The existing GetDigits-timeout state-aware dispatch in
`handle_voice_request` (the check added for `awaiting_safety_digit`/
`post_reply_menu`) is extended to also cover
`awaiting_crisis_connect_digit`, so a timeout here is treated the same as
an explicit non-"1" digit — consistent with how every other DTMF state in
this handler already treats a timeout.

### Post-reply menu: new digit "3"

`_handle_menu_digit` gains a third branch: `digit == "3"` resolves
`_primary_support_phone_number(detail)` the same way, and returns
`build_dial_xml(phone, fallback_text)` if a number is found, or falls back
to today's `digit == "1"` behavior (speaking the support reply) if not.
Digits "1" (speak), "2" (repeat), and "0"/anything else (end) are
unchanged — this is purely additive, no existing behavior changes for a
caller who never presses "3".

`POST_REPLY_MENU_PROMPT` copy is updated to mention the new option (e.g.
"...press 3 to be connected now").

### Discreet mode

No special-casing needed. `_primary_support_phone_number()` returns a bare
phone number, never a service name — the same information discreet-mode
callers already hear today via `build_support_reply(detail, "discreet")`'s
bare-number-only formatting and `GENERAL_SAFETY_REPLY`'s prose. Connecting
the call doesn't reveal anything beyond what's already spoken.

## Safety handling

- The safety reply text itself (`templates.build_safety_reply()`) is
  still always spoken in full, verbatim, before any connect option is
  ever offered — this spec only adds what happens *after* that message,
  never changes it.
- A caller who wants nothing to do with a phone call — including one who
  needs to hang up quickly for their own safety — is never forced through
  an extra step: pressing anything but "1", or simply not pressing
  anything, ends the call exactly as it does today.
- No recording, ever, on any connected call (see Non-goals).
- Rate limiting is unaffected — `<Dial>`/connect digits don't touch
  `_is_rate_limited`, same as every other DTMF-only turn in this handler.

## Testing

- **Automated**: extend `apps/channels/voice/tests.py` with `HandleVoiceRequestTests`-style
  cases (mocking `transcribe_recording` where needed, using the existing
  `_create_home_safety_situation`/`_create_land_situation_without_safety_response`
  fixtures from `apps.channels.sms.tests`):
  - Danger-word path now offers a connect digit instead of ending
    immediately; state becomes `awaiting_crisis_connect_digit`.
  - Pressing "1" after that offer, with a resolvable number, returns
    `<Dial>` + fallback `<Say>`, ends the session.
  - Pressing anything else (or a timeout) after that offer ends the call
    with no `<Dial>`.
  - Same three assertions repeated for the "2" (not safe) and fail-closed
    paths in `_handle_safety_digit`, confirming all three call sites were
    migrated to the shared helper.
  - Post-reply menu digit "3" returns `<Dial>` + fallback when a support
    number exists; falls back to speaking the reply when it doesn't.
  - No-detail crisis case (pure danger-word match, no situation) still
    resolves a dialable number via the direct `SupportService` emergency
    query.
- **Manual, no telco**: same curl-based multi-turn simulation pattern the
  base voice design used, now including a `dtmfDigits=1` turn against a
  session parked in `awaiting_crisis_connect_digit`.
- **Africa's Talking Voice sandbox**: this is the one place in the whole
  voice channel where a real sandbox call is not just a nice-to-have
  check but load-bearing — `<Dial>`'s no-answer/answered branching
  behavior is the core assumption this spec's no-answer fallback design
  depends on, and it should be verified with a real second number (e.g. a
  second sandbox-registered test line) before this ships.
