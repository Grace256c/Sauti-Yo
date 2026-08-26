# USSD Channel Handler — Design

Date: 2026-08-25
Status: Approved
Scope: `backend/apps/channels` — USSD only (SMS and Voice are separate, future design cycles)

## Context

Sauti Yo is a phone-first rights-to-action platform. The `rights` app already
models the canonical content citizens navigate:

```
Situation --M2M(SituationRightsTopic)--> RightsTopic --1:N--> ActionStep
                                              |--1:N--> SafetyResponse (keyed by trigger_key)
                                              |--M2M--> SupportService
```

`apps/support.SupportService` has an `is_emergency_service` flag. `apps/content`
has a `ChannelContent` model (`content_key`, `language`, `channel` → `text`) for
per-channel, per-language UI copy, currently empty and unused.

`apps/channels/{sms,ussd,voice}/*.py` are all empty stub files. `africastalking`
SDK is already in `requirements.txt`. No Redis/Celery — Postgres is the only
available store. Seed data (`backend/seed/*.json`) is currently empty.

This spec covers building the USSD channel end to end: session handling, menu
flow, and the Africa's Talking webhook integration. SMS and Voice will get
their own design docs later, reusing patterns established here where they fit.

## Non-goals

- SMS and Voice handlers (separate specs).
- Translating actual rights content (situation descriptions, action steps,
  safety responses) into Luganda/Kiswahili/Runyankole — see "Language
  handling" below.
- `apps/campaigns` and `apps/analytics` — unrelated, still empty stubs.
- Scheduled cleanup of abandoned USSD sessions (noted as a future nice-to-have,
  not required for v1).

## Architecture

New/changed files, all under `backend/apps/channels/`:

- **`models.py`** — add `UssdSession`:
  - `session_id` (unique, from Africa's Talking)
  - `phone_number`
  - `language` (choices matching `ChannelContent.LANGUAGE_CHOICES`, nullable until chosen)
  - `state` (string — current menu node, e.g. `"main_menu"`, `"topic_detail"`)
  - `context` (JSONField — selections in progress: situation slug, topic slug,
    pagination/chunk offset, invalid-attempt counter)
  - `is_active` (bool, set `False` when the session ends)
  - `created_at` / `updated_at`

  Lives in `channels/models.py` (not `ussd/`) so Django's migration discovery
  for the `apps.channels` app picks it up automatically.

- **`ussd/sessions.py`** — thin CRUD wrapper around `UssdSession`:
  `get_or_create_session(session_id, phone_number)`, `update_session(session, **fields)`,
  `end_session(session)`.

- **`ussd/menus.py`** — pure functions that build each screen's text and
  compute the next state, given the session and a user input. Static copy
  (welcome text, menu labels) is looked up via
  `ChannelContent(channel="ussd", content_key=..., language=session.language)`,
  falling back to a hardcoded English string if no row exists, so the menu
  never breaks on unseeded content. Also owns the screen-budget/pagination/
  text-chunking helpers (see "Screen limits" below).

- **`ussd/handler.py`** — `handle_ussd_request(session_id, phone_number, text) -> str`.
  The orchestrator: loads/creates the session via `sessions.py`, takes the
  last `*`-separated segment of Africa's Talking's cumulative `text` field as
  the newest user input, dispatches to the right builder in `menus.py` based
  on `session.state`, persists the updated state/context, and returns the
  `CON `/`END `-prefixed response string.

- **`ussd/views.py`** — a plain Django view (not DRF: Africa's Talking POSTs
  form-encoded data and expects a `text/plain` body, not JSON, so DRF's
  serializer/renderer stack doesn't fit this endpoint). Parses
  `sessionId`/`phoneNumber`/`text` from `request.POST`, calls
  `handle_ussd_request`, returns `HttpResponse(result, content_type="text/plain")`.

- **`apps/channels/urls.py`** (new) — `path("ussd/", views.ussd_callback, name="ussd-callback")`.

- **`config/urls.py`** — add `path("api/channels/", include("apps.channels.urls"))`.

## Session state model

Django's DB-backed `UssdSession` (not the AT-cumulative-text-parsing
alternative), because Postgres is already available, it supports
back-navigation and persisted language choice cleanly, and needs no new
infra (no Redis).

A session is created on the first request (`text == ""`), updated on each
subsequent `CON` turn, and marked `is_active=False` once we return an `END`
response.

## Menu tree

1. **New session** → language picker: `1. English 2. Luganda 3. Kiswahili
   4. Runyankole`. Choice is saved to `session.language`.
2. **Main menu** → `1. Find my rights` / `2. Get help now` / `0. Exit`.
3. **Find my rights** → paginated list of active `Situation`s (ordered by
   title) → pick one → show `Situation.description` + linked `RightsTopic`s.
   If a situation links to exactly one `RightsTopic`, skip straight to that
   topic's detail screen instead of showing a one-item list.
4. **Topic detail**: if `risk_level` is `sensitive` or `high_risk` and an
   active `SafetyResponse(trigger_key="default")` exists for the topic, show
   it as its own screen first (`1. Continue` required to proceed) before the
   normal topic menu. This is a hard gate, not a skippable option — matches
   the model's intent that these are pre-reviewed, must-see messages.
5. **Topic menu** → `1. Action steps` / `2. Support contacts` / `0. Back`.
6. **Action steps** → shown one at a time in `order`, `Step n/total`, with
   `1. Next` / `0. Back`.
7. **Support contacts** → the topic's linked `SupportService`s (name + phone),
   paginated.
8. **Get help now** (main menu) → `SupportService.objects.filter(is_emergency_service=True,
   is_active=True)`, same list/pagination treatment as support contacts,
   reachable without navigating a situation first.
9. **`0. Exit`** anywhere → `END Thank you for using Sauti Yo.`

## Language handling

Rights content (`Situation.description`, `RightsTopic.summary`,
`ActionStep.description`, `SafetyResponse.message`) is English-only in the
data model — there is no per-language field on these models. For v1:

- The language-picker step still exists and is stored on the session.
- It is used only for USSD **chrome** (menu labels, prompts) via
  `ChannelContent(channel="ussd", language=session.language)`.
- The actual rights/action-step/safety text is served in English regardless
  of the selected language.
- Translating that content is a future content task (seeding `ChannelContent`
  rows keyed by e.g. `content_key=f"situation:{slug}"`), not a code change —
  the menu-builder fallback pattern already accommodates it once those rows
  exist.

## Screen limits & pagination

Africa's Talking caps a screen around ~182 characters including the `CON `/
`END ` prefix. Budget: 160 characters to leave margin.

- List menus (situations, topics, support contacts) paginate at a fixed page
  size with a `More` / `Back` option once the budget is exceeded.
- Long free text (`RightsTopic.summary`, `ActionStep.description`,
  `SafetyResponse.message`) is chunked across multiple screens with a
  `1. More` option; the current chunk offset is tracked in
  `session.context`.

## Error handling & session lifecycle

- Invalid input at any state redisplays the same screen prefixed with
  `Invalid choice.`, without advancing state, and increments an
  invalid-attempt counter in `session.context`. After 3 consecutive invalid
  attempts, the session ends (`END Too many invalid attempts. Please dial
  again.`) to avoid stuck loops.
- A continuing request (`text` non-empty) with no matching `session_id` row
  is treated as a fresh session (restarts at the language picker) rather than
  erroring.
- No scheduled cleanup of abandoned (never-`END`ed) sessions in v1. A future
  `prune_ussd_sessions` management command is noted as a nice-to-have, not
  built now.

## Testing

- **Automated**: Django `TestCase` driving `handle_ussd_request()` directly
  through full flows (language → main menu → situation → topic → safety
  response → action steps; and the emergency-contacts shortcut), asserting
  exact `CON`/`END` strings and state transitions. A thin view-layer test
  posts Africa's-Talking-shaped form data and checks the HTTP response.
  Fixtures are created via the ORM in `setUp`, since seed data is currently
  empty — seeding real situations/rights content is a separate follow-up
  task.
- **Manual, no telco**: the endpoint is a plain POST-in/text-out contract, so
  a full session can be walked by hand with `curl`/Postman, reusing the same
  `sessionId` and growing `text` the way Africa's Talking does:
  ```
  curl -X POST localhost:8000/api/channels/ussd/ \
    -d "sessionId=test123&phoneNumber=+256700000000&text="
  curl -X POST localhost:8000/api/channels/ussd/ \
    -d "sessionId=test123&phoneNumber=+256700000000&text=1"
  ```
- **Africa's Talking USSD Simulator**: sandbox account's web-based phone
  simulator dials a test service code and hits the callback URL for real,
  rendering actual CON/END screens. Requires exposing local dev via a tunnel
  (e.g. ngrok) and pointing the sandbox app's callback URL at it — closest
  check to real-phone behavior before going live.
