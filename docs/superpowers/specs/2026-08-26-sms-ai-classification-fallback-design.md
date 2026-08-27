# SMS Free-Text AI Classification Fallback — Design

Date: 2026-08-26
Status: Approved
Scope: `backend/apps/channels/sms` — adds one new fallback path to the already-shipped SMS channel handler

## Context

The SMS channel (`docs/superpowers/specs/2026-08-26-sms-channel-handler-design.md`) is built and live: inbound text is matched against fixed keyword lists (danger words, `HELP`, situation keywords, follow-up words), and anything that matches nothing gets a generic "You can text HOME, WORK, LAND or CHILD..." reply. That's a hard requirement — a citizen has to know and type one of a handful of exact English words.

The project brief's "Responsible AI" section describes exactly the gap this closes: `User question -> Classify/retrieve -> Verified legal content -> LLM simplification -> Safety validation -> Rights-to-Action`, with explicit constraints — AI is "an enabling layer, not the centre," must "use retrieval over approved content rather than unrestricted generation," must never "invent Ugandan law or policy," and must never "override predefined high-risk pathways."

This spec adds a Claude-powered classification step as the new last resort before the unmatched-keyword fallback: free text that doesn't match any fixed keyword gets classified against the catalog of real, seeded `Situation` rows, and — if Claude confidently names one — the reply is built by the exact same, already-reviewed template pipeline the keyword path uses.

## Non-goals

- AI does not compose the reply text. It never sees, and never generates, the actual message sent to the user — that stays a strict content-boundary held entirely by `templates.build_situation_reply()`, unchanged.
- No change to the danger-word path, `HELP`, situation keywords, or follow-up keywords — all four still run first, deterministic, unmodified. AI classification only runs when none of them match.
- No embeddings / pgvector / semantic search infrastructure. At the current data scale (a handful of seeded situations), the "retrieval" step is simply listing every active situation's slug and title in the prompt — full-context classification, not a search index. If the situation catalog grows large enough that this stops fitting comfortably in a prompt, that's a future revisit, not a v1 concern.
- No conversation memory for the AI step itself — each classification call is a single, stateless request (title/slug catalog + the one inbound message). If Claude resolves a real slug, the existing `SmsContext` mechanism (already built) is what carries state into a follow-up turn, identically to the keyword path.
- No AI-generated safety/danger content, ever. This path is unreachable from the danger branch — `match_danger()` is checked first, unconditionally, before AI classification ever runs.

## Design

### Why classification, not generation

The alternative design — hand Claude the full verified content (summaries, action steps, support contacts) and ask it to compose an SMS reply — was considered and rejected. It would mean the exact words a vulnerable person receives about, say, a domestic violence situation are LLM-generated rather than the human-reviewed template text already in production. Restricting Claude's output to "which of these N known categories does this most resemble, or none" is a categorically smaller, more bounded task: the only thing that can go wrong is picking the wrong (or no) category, which is trivially checkable (the returned string either is a real active situation slug or it isn't) and degrades safely (falls through to the existing unmatched reply) either way.

### Flow

New match order in `handle_sms_request` (replacing the previous unconditional final fallback):

```
rate limit -> danger words -> HELP -> situation keyword -> follow-up keyword
    -> AI classification (new) -> unmatched reply
```

If AI classification returns a real slug, the reply and `SmsContext` persistence are handled by a new shared helper, `_reply_to_situation(phone_number, slug, text)`, extracted from the existing situation-keyword branch's logic (get detail, guard `None`, compute `discreet` mode from the original free text, send, persist context) — used identically by both the keyword-match branch and the new AI-fallback branch. This is a refactor of existing code, not new behavior on that path.

### `ai_classifier.py`

New module, `backend/apps/channels/sms/ai_classifier.py`, exporting one function:

```python
classify_situation(text: str) -> str | None
```

- Builds the catalog from `apps.rights.services.list_active_situations()` — `slug: title`, one per line. If there are no active situations at all, returns `None` immediately (nothing to classify against).
- If `settings.LLM_API_KEY` is empty, returns `None` immediately without attempting a network call — matches the established pattern of every other optional-integration path in this codebase (Africa's Talking credentials work the same way).
- Calls the Anthropic Messages API (`claude-haiku-4-5` — a bounded "pick 1 of N, or none" classification task doesn't need a larger model) with a strict system prompt instructing Claude to respond with only a slug or the literal word `NONE`, never commentary, never an invented slug.
- A 5-second request timeout (`client.with_options(timeout=5.0)`) — this call sits inline in the webhook request; it should fail fast rather than hang it.
- The response text is stripped and checked against the real set of active slugs. Anything that isn't an exact match — including `NONE`, empty output, or a hallucinated slug not in the catalog — returns `None`.
- Every failure mode (missing key, network error, rate limit, malformed response, unexpected exception) is caught inside this function and returns `None`. This function's whole contract is "tell me a real slug or nothing" — a classification failure has a well-defined, already-tested safe fallback (the unmatched reply), so it should never propagate and crash the request the way a genuine bug elsewhere in the handler still should.

### Settings & dependencies

- `backend/config/settings.py` — wire up the already-present-but-unused env var names from `.env.example`: `LLM_API_KEY = os.getenv("LLM_API_KEY", "")`, `LLM_MODEL = os.getenv("LLM_MODEL") or "claude-haiku-4-5"`. (`LLM_MODEL` is wired up for forward-compatibility/config visibility; `ai_classifier.py` itself hardcodes `claude-haiku-4-5` for this call rather than reading the setting, since a classification task this narrow shouldn't silently change model tier via an env var someone edits for an unrelated reason — if the model needs to change, that's a code change.)
- `backend/requirements.txt` — add `anthropic`.

### Testing

All tests mock the Anthropic client — no automated test calls the real API. Cases for `ai_classifier.classify_situation`:
- A mocked response naming a real active slug → returns that slug.
- A mocked `NONE` response → returns `None`.
- A mocked response naming a slug that doesn't exist in the catalog (hallucination) → returns `None`.
- The Anthropic client raising an exception (any type) → returns `None`, no exception propagates.
- `settings.LLM_API_KEY` empty → returns `None` and the mocked client is never called (asserted via `mock_client.assert_not_called()` or equivalent) — proves the short-circuit actually skips the network call rather than just tolerating a failure from one.

Cases for the refactored `handler.py`:
- A free-text message with no keyword match, where the mocked classifier returns a real slug → routes through `_reply_to_situation`, sends the situation reply, and persists `SmsContext` — same assertions as the existing keyword-match tests, proving the shared helper behaves identically regardless of caller.
- A free-text message where the mocked classifier returns `None` → sends the unmatched reply (the pre-existing behavior, now reached via one extra step).
- Existing keyword-match, danger-word, follow-up, and rate-limit tests continue passing unmodified — the refactor must not change any of their observable behavior.
