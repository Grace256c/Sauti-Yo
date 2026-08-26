# USSD Unreviewed-Content Disclaimer — Design

Date: 2026-08-26
Status: Approved
Scope: `backend/apps/channels/ussd/menus.py` — USSD channel only

## Context

Sauti Yo's `RightsTopic` model tracks `verification_status` (`verified` / `review_required` / `expired` / `archived`), and the pilot content seeded into the platform (workplace, eviction, domestic violence, sexual harassment) is deliberately `review_required` — real, publicly-sourced legal content that no human with legal/NGO authority has reviewed yet. A final whole-branch review of that seeding work found that nothing in the running application actually reads this field: `review_required` content renders identically to `verified` content everywhere, including the USSD channel, which is the only channel currently serving live database content to real users.

This spec closes that gap for USSD specifically. It does not touch the DRF API (already exposes `verification_status` in `RightsTopicSerializer`, just isn't consumed by anything yet) or the citizen frontend (currently runs entirely on static local data in `frontend/src/data/`, not the live API — wiring that up is a separate, larger integration task). It does not touch SMS or Voice, which don't exist yet (`apps/channels/sms/` and `apps/channels/voice/` are empty stubs) — whichever gets built first will design this in from the start rather than retrofit it.

## Approach

Show a short, fixed disclaimer as the leading text of a topic's content, for any `verification_status` other than `"verified"` (`review_required`, `expired`, and `archived` all get it — silence is earned by an explicit "verified" status, not assumed for anything else).

**Mechanism:** prepend the disclaimer text to the *raw* body text before it reaches `_chunked_screen`/`chunk_text`, rather than treating it as a special first-chunk case. Since `chunk_text` already word-wraps and paginates whatever text it's given against the screen budget, a prepended notice naturally lands in chunk 0 and is never repeated in later chunks — no changes needed to `_chunked_screen`'s budget math (which already correctly reserves room for `trailing_options`; the notice is now just more body text going through the same accounting). This is simpler than the field-level approach discussed during brainstorming and carries the same overflow-safety guarantee for free.

Applies to the two screens that render `RightsTopic` content directly:
- `render_topic_detail` / `transition_topic_detail` (the topic's `summary`)
- `render_safety_gate` / `transition_safety_gate` (the safety message, or its `summary`/`title` fallback)

Both the `render_*` and `transition_*` half of each pair must prepend identically — this project's established discipline (the reason `_is_last_chunk` was removed earlier) is that render and transition must derive `is_last` from calling `_chunked_screen` with the exact same input text, or they can silently disagree about chunk boundaries.

Does **not** apply to `render_action_steps` or `render_support_contacts` — both are reached only after a screen that already showed the notice once for that topic, so repeating it would just cost budget for no new information. `ActionStep` and `SupportService` have no `verification_status` of their own to check here (`SupportService` does have the field, but gating support-contact display on it is a separate, not-yet-scoped decision — this spec covers `RightsTopic` content only).

## Copy

New `DEFAULT_COPY` key in `menus.py`, following the exact pattern every other USSD string already uses (`get_copy`, per-language override via `ChannelContent`, English fallback):

```python
"ussd.unreviewed_notice": "Note: not yet reviewed.",
```

~24 characters — small enough that it never meaningfully displaces real content out of chunk 0 for realistic summary lengths, while still being unambiguous. Prepended with a blank-line separator before the real body text, matching the visual separation `_chunked_screen` already uses between body and trailing options.

## Data flow

```
topic.verification_status != "verified"?
  no  → text unchanged
  yes → text = f"{get_copy('ussd.unreviewed_notice', language)}\n\n{text}"
             → chunk_text(text, budget) as before, no other change
```

A single helper, `_prepend_unreviewed_notice(text, verification_status, language)`, implements this and is called from all four sites listed above, so the condition is written once.

## Testing implications (flagging now, resolving in the plan)

`RightsTopic.verification_status` defaults to `"review_required"` at the model level. Every existing USSD test fixture that creates a `RightsTopic` without explicitly setting `verification_status="verified"` will, after this change, start rendering the new notice — which shifts where `chunk_text` places chunk boundaries for short test fixtures using tight budgets. The implementation plan needs to either set `verification_status="verified"` explicitly on fixtures that don't care about this behavior, or update the affected assertions — this is a real, expected consequence of the fix working correctly, not a bug to route around.

## Non-goals

- No change to `is_active` filtering or which topics are queryable — this is purely a rendering-layer notice, not a gate.
- No change to the DRF API or frontend.
- No change to `SupportService`'s own `verification_status` handling.
- No localization of the new copy key beyond the existing `get_copy`/`ChannelContent` mechanism already in place (translating it is a future content task, same as everything else in this file).
