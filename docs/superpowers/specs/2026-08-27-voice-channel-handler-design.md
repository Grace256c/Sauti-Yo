# Voice Channel Handler — Design

Date: 2026-08-27
Status: Approved
Scope: `backend/apps/channels` — Voice only

## Context

Sauti Yo is a phone-first rights-to-action platform. USSD and SMS are both
built end-to-end:

- USSD (`docs/superpowers/specs/2026-08-25-ussd-channel-handler-design.md`)
  drives a DB-backed, numbered-menu state machine (`UssdSession`).
- SMS (`docs/superpowers/specs/2026-08-26-sms-channel-handler-design.md`,
  `docs/superpowers/specs/2026-08-26-sms-ai-classification-fallback-design.md`,
  `docs/superpowers/specs/2026-08-26-sms-conversational-safety-checkin-design.md`)
  layers deterministic keyword matching, a Claude-based free-text
  classification fallback, a DTMF-equivalent (YES/NO text) safety
  check-in for high-risk situations, and Claude-based reply rewording on
  top of `SmsContext` (deliberately not a screen/state tracker).

Voice is architecturally closest to SMS's free-text intent-matching, but
delivered over a live phone call instead of a message exchange:

- Africa's Talking's Voice webhook gives a call `sessionId` (like USSD)
  but the interaction happens over several webhook round-trips within one
  call, each returning XML (`<Say>`, `<Record>`, `<GetDigits>`) rather
  than one `CON`/`END` string.
- There is no typed text from the caller — the caller's intent arrives as
  a voice recording that must be transcribed before anything in
  `apps.channels.sms.keywords` or `apps.channels.sms.ai_classifier` can
  run against it.
- A phone call is a single continuous session, so there's no equivalent
  of SMS's 10-minute `SmsContext` follow-up window — all follow-up
  navigation (repeat, support contacts, end) happens as DTMF turns within
  the same call.

This spec reuses SMS's already-built and reviewed pieces directly:
`apps.channels.sms.keywords` (danger/situation/discreet matching),
`apps.channels.sms.ai_classifier` (`classify_situation`, `reword_reply`),
`apps.channels.sms.templates` (`build_situation_reply`,
`build_safety_reply`, `build_support_reply`, `build_steps_reply`,
`build_unmatched_reply`), and `apps.rights.services.get_situation_detail`.
None of that code changes — Voice only adds a transcription step in front
of it and an XML/DTMF layer around it.

## Non-goals

- Non-English languages. Africa's Talking TTS voice quality and Whisper
  transcription accuracy are both markedly weaker for Luganda/
  Kiswahili/Runyankole than English; shipping that untested on a
  safety-critical path is worse than not shipping it. USSD remains the
  multilingual channel for now.
- Sending a follow-up SMS with the spoken reply's text/phone numbers.
  Spoken-only for v1 — keeps this build decoupled from the SMS send path.
  A caller who wants a number to keep already has SMS's own channel.
  Revisit if user feedback says numbers are hard to retain from speech
  alone.
- A DTMF-driven numbered menu as the primary interaction (i.e. a "voice
  USSD"). The caller describes their situation in their own words; DTMF
  is used only for the two places a wrong read is unacceptable or where
  the interaction is naturally a menu (the safety check-in, and
  post-reply navigation).
- Any change to `apps.channels.sms.*` itself — Voice is purely additive.

## Architecture

New files under `backend/apps/channels/voice/`, plus one model addition:

- **`models.py`** — add `VoiceSession`:
  - `session_id` (unique, from Africa's Talking)
  - `phone_number`
  - `state` — `"awaiting_recording"`, `"awaiting_safety_digit"`,
    `"post_reply_menu"`, `"ended"`
  - `context` (JSONField) — `{"slug": ..., "discreet": bool}` once a
    situation is matched; empty until then. Also briefly holds
    `{"attempts": N}` while `state == "awaiting_recording"`, to cap the
    unmatched/transcription-failure retry at one extra attempt before
    closing the call (mirrors `UssdSession.context`'s invalid-attempt
    counter).
  - `is_active` (bool, set `False` when the call ends)
  - `created_at` / `updated_at`

  Needed (unlike SMS) because a single call is multiple webhook
  round-trips that must agree on where the call is in the flow — the
  same reason `UssdSession` exists. Kept separate from `UssdSession`
  since the state values and meaning are call-specific, not menu-specific.

- **`voice/sessions.py`** — thin CRUD wrapper around `VoiceSession`,
  mirroring `ussd/sessions.py`: `get_or_create_session(session_id,
  phone_number)`, `update_session(session, **fields)`, `end_session(session)`.

- **`voice/transcription.py`** — `transcribe_recording(recording_url) ->
  str | None`. Downloads the audio from Africa's Talking's `recordingUrl`
  (a plain authenticated HTTP GET) and posts it to OpenAI's Whisper
  transcription endpoint. Returns `None` on any failure (download error,
  API error, timeout, empty result) — every failure mode collapses to
  "no transcript," handled by the same not-understood path regardless of
  cause, matching `ai_classifier.classify_situation()`'s
  everything-degrades-to-None discipline.

- **`voice/ivr.py`** — pure functions building each turn's Africa's
  Talking XML response, analogous to `ussd/menus.py`'s screen builders:
  `build_greeting_xml()`, `build_safety_checkin_xml(discreet)`,
  `build_reply_xml(spoken_text)`, `build_post_reply_menu_xml()`,
  `build_unmatched_xml()`, `build_closing_xml()`. Each wraps plain text
  in `<Say>`, and where a caller response is expected, nests the
  appropriate `<Record>`/`<GetDigits>` action. Exact Africa's Talking XML
  attribute names (`finishOnKey`, `maxLength`, `trimSilence`,
  `numDigits`, timeout values) are verified against Africa's Talking's
  Voice API reference during implementation, not guessed here.

- **`voice/handler.py`** — `handle_voice_request(session_id,
  phone_number, is_active, dtmf_digits, recording_url) -> str` (the XML
  body). The orchestrator; see Call flow below for the state machine.

- **`voice/views.py`** — plain Django view (same reasoning as USSD/SMS:
  Africa's Talking POSTs form-encoded data and expects an XML body, not
  JSON). Parses `sessionId`/`phoneNumber`/`isActive`/`dtmfDigits`/
  `recordingUrl` from `request.POST`, calls `handle_voice_request`,
  returns `HttpResponse(result, content_type="text/xml")`.

- **`apps/channels/urls.py`** — add `path("voice/",
  voice_views.voice_callback, name="voice-callback")`.

- **`config/settings.py`** — add `OPENAI_API_KEY` (new env var,
  transcription only; Claude classification/rewording continue to use
  the existing `LLM_API_KEY`).

- **`requirements.txt`** — add the `openai` package (Whisper
  transcription client only — no other OpenAI usage anywhere in this
  project; Claude remains the only model used for any classification,
  rewording, or generated user-facing text).

## Call flow

State transitions on `VoiceSession.state`, one turn per webhook hit:

1. **Call connects** (`isActive="1"`, no digits, no recording) → create
   session (`state="awaiting_recording"`) → respond with
   `build_greeting_xml()`: a short spoken instruction ("Describe what's
   happening, then go quiet or press pound") followed by a `<Record>`
   action.

2. **Recording ready** (`recordingUrl` present, `state ==
   "awaiting_recording"`) → `transcription.transcribe_recording()`.
   - Transcription fails or returns empty → `build_unmatched_xml()`
     (apologetic message, one retry via another `<Record>`, or a
     graceful close if this is the second failure) — no different from
     the no-match path in step 3.
   - Otherwise, run the transcript through the same order SMS uses:
     `keywords.match_danger()` first, unconditionally. If it matches,
     speak `templates.build_safety_reply()` (no situation context yet,
     so the general safety reply) and end the call immediately — no
     DTMF check-in, no classification. A caller who's already signaling
     danger in their own words doesn't need a second question to
     confirm it.
   - No danger words → `keywords.match_situation()`, then
     `ai_classifier.classify_situation()` fallback if no keyword hit
     (identical two-stage order to `sms/handler.py`). Also run
     `keywords.match_discreet()` on the same transcript; the result is
     carried in `context["discreet"]` for the rest of the call.
   - No slug from either stage → `build_unmatched_xml()`.

3. **Slug matched**, `state` still `"awaiting_recording"` →
   `get_situation_detail(slug)`.
   - `risk_level == "high_risk"` → store `context = {"slug": slug,
     "discreet": discreet}`, `state = "awaiting_safety_digit"`, respond
     with `build_safety_checkin_xml(discreet)` — *"Press 1 if you're
     safe right now, press 2 if you're not"* (discreet mode uses neutral
     phrasing here too, matching SMS's `DISCREET_SAFETY_CHECKIN_QUESTION`
     pattern, since the DTMF prompt itself is spoken aloud). This is the
     one binary decision in the whole flow where a wrong read is
     dangerous, which is why it's DTMF instead of parsed from speech.
   - Otherwise → speak the reply (step 5) directly.

4. **Safety digit received** (`state == "awaiting_safety_digit"`):
   - `"2"` (not safe) → speak `templates.build_safety_reply(detail)` for
     the matched situation, end the call.
   - `"1"` (safe), or no/invalid digit after one re-prompt → proceed to
     the situation reply (step 5). Erring toward continuing rather than
     stalling the call matches SMS's late-checkpoint behavior, which
     also treats an unclear answer as fine-to-proceed rather than
     re-asking indefinitely.

5. **Speak the situation reply** → build via `templates.build_
   situation_reply(detail, mode)`, where `mode = "discreet" if
   context["discreet"] else "normal"`. In normal mode, run it through
   `ai_classifier.reword_reply()` for warmth (same fallback-to-template-
   on-failure rule as SMS); discreet mode is never reworded, matching
   SMS exactly. Store `context = {"slug": slug, "discreet": discreet}`,
   `state = "post_reply_menu"`, respond with `build_reply_xml(spoken_
   text)` followed immediately by the post-reply `<GetDigits>` prompt.

6. **Post-reply digit received** (`state == "post_reply_menu"`):
   - `"1"` → speak `templates.build_support_reply(detail, mode)`,
     remain in `"post_reply_menu"`.
   - `"2"` → repeat step 5's spoken reply, remain in `"post_reply_menu"`.
   - `"0"`, no digit, or the caller hangs up → `build_closing_xml()`,
     `state = "ended"`, `is_active = False`.

7. **Call ends** (`isActive="0"`, from any state) → mark
   `is_active = False` if not already ended. No XML response is needed
   for a hangup notification, matching Africa's Talking's own handling
   of this event.

## Safety handling

- `keywords.match_danger()` is checked before any classification, on
  every transcribed recording, no exceptions — identical guarantee to
  SMS's `match_danger()` placement, applied to the voice transcript.
- `templates.build_safety_reply()` is the only source of crisis-response
  wording, called the same way SMS calls it — never composed or
  reworded by Claude, never by `ivr.py`.
- The safety check-in answer is DTMF, not transcribed speech, precisely
  because SMS's own postmortem (per the SMS safety check-in design doc)
  found that free-text matching needs care even with a fixed set of
  expected answers — a live call adds background noise and accent
  variance on top, so this is the one place a keypress replaces
  parsing.
- Discreet mode never reaches `ai_classifier.reword_reply()` and never
  states the situation's name/topic identity, matching SMS.
- Rate limiting: reuse the same cache-based per-phone-number limiter
  pattern `sms/handler.py` uses (`_is_rate_limited`), applied once at
  call start (`cache_key = f"voice_rate:{phone_number}"`), to blunt
  webhook abuse without needing Redis.

## Testing

- **Automated**: Django `TestCase` calling `handle_voice_request()`
  directly at each state transition, mocking `transcription.
  transcribe_recording()` (so tests never call the real Whisper API) and
  `ai_classifier.classify_situation()`/`reword_reply()` (already mocked
  this way in `sms/tests.py` — same pattern, same reasoning: no billed
  network calls from the test suite). Cases:
  - Full happy path: connect → record → transcript matches a
    non-high-risk situation → spoken reply → post-reply menu → end.
  - High-risk situation → safety check-in triggered → `"1"` continues
    to the reply, `"2"` returns the safety reply and ends the call.
  - Danger words in the transcript → immediate safety reply, no
    check-in, no classification call made.
  - Discreet keyword in the transcript → reply omits situation/service
    names, reword is never called.
  - Transcription failure/empty transcript → unmatched/retry path.
  - No keyword or AI match → unmatched path.
  - Rate-limited phone number → call is rejected before any transcription
    work happens.
  A thin view-layer test posts Africa's-Talking-shaped voice form data
  and asserts a 200 response with an XML content type.
- **Manual, no telco**: `curl -X POST localhost:8000/api/channels/voice/
  -d "sessionId=...&phoneNumber=+256700000000&isActive=1"` for the
  connect turn, then a second curl simulating the recording-ready turn
  with a `recordingUrl` pointing at a local test audio file — same
  reasoning as USSD/SMS's curl-based manual checks.
- **Africa's Talking Voice sandbox**: sandbox account's test number can
  place a real call against the webhook, exercising the actual XML
  round-trips and Africa's Talking's TTS rendering — closest check to
  the real-phone-call demo moment before going live.
