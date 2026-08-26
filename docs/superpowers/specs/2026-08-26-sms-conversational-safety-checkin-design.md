# SMS Conversational Safety Check-In and Reply Rewording — Design

Date: 2026-08-26
Status: Approved
Scope: `backend/apps/channels/sms` — extends the already-shipped SMS channel and its AI classification fallback

## Context

Two things exist today:

1. Keyword/AI-classification match → `templates.build_situation_reply()` sends the exact same fixed text every time someone asks about a given situation.
2. A hard-coded `DANGER_WORDS` list (`match_danger()`) is the *only* way a conversation reaches the human-reviewed `SafetyResponse` message — if someone never types one of those specific words, nothing ever asks whether they're actually safe.

Live testing surfaced two asks: the replies feel repetitive/form-letter, and the system should proactively check in on safety rather than only reacting to specific trigger words. This spec adds both, while keeping the project's core safety principle intact: *AI must never compose or gate safety-critical content* (project brief, "Responsible AI" / "Safety and Immediate-Danger Pathway").

## Non-goals

- No change to `match_danger()`'s unconditional, first-checked position in the match order, and no change to what `build_safety_reply()` returns (still the verbatim `SafetyResponse` row, never AI-touched).
- No open-ended chat capability. The AI only ever engages *after* a real Sauti Yo situation has been resolved (by keyword or by `ai_classifier.classify_situation`) — a message that classifies to `NONE` still gets the exact same fixed `UNMATCHED_REPLY` as today, completely unchanged. This spec adds no new way for an off-topic message to get an AI-generated response.
- No AI composition from raw facts. The rewording step is given the *already-built, already-verified* template string and may only rephrase it — never assemble a reply from scattered DB fields itself. This keeps "which facts appear" entirely governed by the existing, already-reviewed `templates.py` logic.
- No rewording in discreet mode. Discreet mode's whole purpose is minimizing identifying detail (`DISCREET_INTRO`, service-name redaction); paraphrasing that text risks reintroducing identifying language for no benefit. Discreet-mode replies stay byte-identical to today.
- No multi-question conversational memory beyond the one safety check-in. `SmsContext` gains exactly one new field (`pending_safety_check`); this is not a general-purpose dialogue state machine.

## Design

### 1. The safety check-in

**Trigger:** when `_reply_to_situation()` (shared by the keyword-match and AI-classification branches) resolves a situation whose `risk_level == "high_risk"`, **and** the phone number isn't already mid-conversation about that same slug (i.e. `SmsContext.last_situation_slug` doesn't already equal it) — this is a *new* high-risk topic for this conversation. In that case, instead of the normal reply, send only:

```
Are you safe right now? Reply YES or NO.
```

and persist `SmsContext(last_situation_slug=slug, discreet=..., pending_safety_check=True)`. If the situation isn't high-risk, or the phone number is already discussing that same slug (e.g. this is a follow-up in the same thread), skip straight to the normal reply — the check-in fires once per topic, not on every message.

**Resolving the answer — placement matters, and needs two checkpoints, not one.**

The naive approach — intercept the *next* message immediately after the danger-word check, before anything else — has a real gap: if someone answers with something that's actually a fresh, distinct request (e.g. they were mid-check-in about `home-safety`, then send a message that clearly matches `WORK`/`problem-at-work`), that new message would get swallowed as a non-answer to the stale question and they'd receive the *wrong* topic's reply instead of what they just asked for. That argues for checking late, after every other branch has had a chance.

But checking *only* late has its own gap: `"unsafe"` already appears in `home-safety`'s own `SITUATION_KEYWORDS` list (someone's first message might be "I feel unsafe at home"). If the check-in question is answered with exactly `"unsafe"`, and pending-check resolution runs last, `match_situation()` would catch it first as a `home-safety` keyword match — and since that's the *same* slug already in context, no new check-in triggers, and the person who just said "unsafe" gets the normal info reply instead of the safety reply. That's the wrong outcome for someone explicitly saying they're not safe.

So `keywords.match_not_safe_answer(text)` — which reuses `match_danger()` (any danger word counts) plus a small scoped word/phrase list (`no`, `not safe`, `unsafe`, `not okay`, `not ok`; `no` needs a word-boundary check, `\bno\b`, not a substring check, since "know" and "info" both contain the substring "no") — is checked at **two** points:

```
rate-limit -> danger words
    -> [pending check-in: "not safe" signal only, if one is open] -> HELP
    -> situation keyword -> followup keyword -> AI classification
    -> [pending check-in: anything else, if still open] -> unmatched
```

1. **Early**, right after `match_danger()`: if a check-in is pending *and* `match_not_safe_answer(text)` is true, send `build_safety_reply(detail)` immediately and clear the flag — this is what makes "unsafe" resolve correctly regardless of it also being a situation keyword.
2. **Late**, second-to-last: if a check-in is *still* pending at this point (meaning the early check didn't fire, and nothing else — `HELP`, a situation keyword, a follow-up word, or AI classification — matched either), treat the message as a generic non-answer ("yes", "ok", or anything else) and send the normal (now possibly reworded) situation reply for the remembered slug, clearing the flag.

Because the early check only fires on the narrow, explicit "not safe" word/phrase set — not general free text — a genuine topic-switch message (which by definition doesn't contain any of those words) still passes through untouched to the normal keyword/AI-classification branches in between, exactly as intended. Only messages that are *either* an explicit "not safe" signal *or* generic enough to match nothing else ever get intercepted by the check-in logic.

Either way, `pending_safety_check` is cleared once interpreted — it's a one-shot question, not a lock. If `match_danger()` itself fires (an explicit danger word, not routed through the check-in interpretation at all), that path already sends the safety reply and returns *before either* pending-check checkpoint would run — so the flag must be explicitly cleared there too, or a later unrelated message would be wrongly re-interpreted as answering a question that was, in effect, already answered.

### 2. Reply rewording

**What gets reworded:** only the normal-mode situation reply (`templates.build_situation_reply(detail, "normal")`) — the exact string that would be sent today. A new `ai_classifier.reword_reply(template_text) -> str | None` asks Claude to rephrase that string more warmly, with an explicit instruction not to add, remove, or change any fact, name, or phone number — only how it's said.

**Validation, not trust:** every phone number in the original template text (extracted via `re.findall(r"\d{3,}", template_text)`, which reliably catches this codebase's phone-number formatting since `templates.py` never inserts spaces inside a number) must still appear verbatim in the reworded text. If any is missing, or the API call fails for any reason, or the reworded text comes back empty, `reword_reply()` returns `None` and the caller falls back to sending the original, unmodified template text — the user never receives a broken or fact-dropped reply, and never receives no reply at all.

**Where it plugs in:** a new `_compose_situation_reply(detail, mode)` helper in `handler.py` wraps `templates.build_situation_reply()`: for `mode == "discreet"` it returns the template text unchanged (Non-goals); for `mode == "normal"` it calls `reword_reply()` and returns that if non-`None`, else the original template text. `_reply_to_situation()` calls this instead of `templates.build_situation_reply()` directly wherever it sends the normal reply (both the immediate-reply path and the resolved-pending-check path).

### Data model change

`backend/apps/channels/models.py`, `SmsContext`:

```python
pending_safety_check = models.BooleanField(default=False)
```

One migration, `AddField` only — same caution as prior `SmsContext` migrations about not accepting an unrelated `UssdSession.id` `AlterField` Django might propose alongside it.

### Testing

All AI-touching tests mock the Anthropic client — no automated test calls the real API, matching every prior spec's constraint in this codebase.

- `keywords.match_not_safe_answer`: matches "no", "NOT SAFE", "unsafe", every existing `DANGER_WORDS` entry; does **not** match "yes", "I'm okay", or — the specific regression this design calls out — "I don't know what to do" (must not false-positive on the substring "no" inside "know").
- `ai_classifier.reword_reply`: a mocked response that preserves the phone number returns the reworded text; a mocked response that drops it returns `None`; the client raising returns `None`; empty `LLM_API_KEY` returns `None` without a network call attempted (asserted the same way prior classifier tests proved this).
- `handler.py`: a new high-risk situation match sends only the check-in question and sets `pending_safety_check=True` (not the full reply); a non-high-risk match is unaffected (no check-in); a repeat message about the same already-pending-free high-risk slug doesn't re-trigger the check-in; a pending check answered with `"unsafe"` sends the verbatim safety reply, not the `home-safety` info reply — the specific overlap-with-`SITUATION_KEYWORDS` case the two-checkpoint design exists to fix; a pending check answered with another "not safe" signal (e.g. plain "no") also sends the verbatim safety reply; a pending check answered with a generic reply ("yes"/"ok") sends the (mocked-reworded) situation reply and clears the flag; a pending check answered with a message that matches a *different* real situation keyword (e.g. `WORK`) is handled as that new topic, not swallowed as a stale answer; a danger word arriving while a check-in is pending still gets the safety reply *and* clears the flag (proven by a follow-up message in the same test not being mis-interpreted as answering a stale question); when `reword_reply` returns `None`, the exact original template text is sent unchanged.
