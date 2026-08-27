# USSD Global Exit Option — Design

Date: 2026-08-27
Status: Approved
Scope: `backend/apps/channels/ussd/menus.py` — USSD channel only

## Context

`ussd.main_menu` is currently the only screen offering "0. Exit" (`ussd.main_menu` = `"1. Find my rights\n2. Get help now\n0. Exit"`). Every other screen (situation list, situation/topic detail, safety gate, action steps, support contacts, emergency list, language select) uses "0" to mean "Back," so a user can only end the session immediately from the main menu — from anywhere deeper in the flow they have to press "0" repeatedly to walk back out. The user wants to be able to close the session from any screen, at any point.

## Approach

"0" becomes a global Exit shortcut, valid and labeled on every screen (including `language_select`, which currently has no Back/Exit option at all), and always ends the session immediately regardless of how deep the user is in the flow. "Back" moves from digit "0" to digit "9" everywhere it currently appears, since "9" is unused on every existing screen (numbered lists cap at 7 items + "8. More").

**Transition side (single choke point):** `menus.transition_state`, the one function `handler.py` calls to advance state, intercepts `user_input == "0"` for any state other than `"goodbye"` and returns `("goodbye", {})` directly, before dispatching to the per-screen `TRANSITION_HANDLERS` entry:

```python
def transition_state(state, session, user_input):
    if user_input == "0" and state != "goodbye":
        return "goodbye", {}
    return TRANSITION_HANDLERS[state](session, user_input)
```

This makes Exit work everywhere by construction — no per-screen transition function needs its own Exit-handling branch. Every existing `if user_input == "0": return <back-target>` branch in the per-screen handlers becomes unreachable dead code once this lands, so each one is changed to check `"9"` instead, restoring Back at its new digit.

**Render side (budget-sensitive, no single choke point):** screen text is capped at `SCREEN_BUDGET` (160 chars), and every screen that paginates already reserves room for its trailing options (Back/More/Continue) *before* wrapping the body via `_wrap_words`/`chunk_text`. Appending "0. Exit" to rendered text after the fact — e.g. by wrapping `render_state` — would not be accounted for in that reservation and could push a screen over budget. So the exit line has to be baked into each screen's existing trailing-text construction, at the same point Back's digit changes from 0 to 9:

- `_chunked_screen`: its `more_back` (shown on non-final chunks) and the final-chunk trailing text both gain a "0. {exit}" line alongside "9. {back}". Its `reserved` calculation, already `max(len(trailing_options), len(more_back))`, automatically accounts for the longer text since both strings grow at the same call site. This single function covers `situation_detail`, `topic_detail`, `safety_gate`, `action_steps`, `support_contacts`, and `emergency_list` in one change.
- `_situation_list_page` / `_situation_topics_page`: their manual `reserved` calculation and the `screen_lines` they build gain the "0. Exit" line alongside "9. Back".
- `render_main_menu`: unchanged wording (`ussd.main_menu` already ends in "0. Exit"), since 0 already meant exit here.
- `render_language_select`: gains a new trailing "0. Exit" line — this screen currently has no Back/Exit option at all.
- The four "no items" fallback screens (`ussd.no_situations`, `ussd.no_action_steps`, `ussd.no_support_contacts`, `ussd.no_emergency_contacts`), which each currently hardcode `f"{body}\n\n0. {back}"`, change to `f"{body}\n\n9. {back}\n0. {exit_label}"`.

## Copy

New `DEFAULT_COPY` key, following the existing `get_copy` pattern (per-language override via `ChannelContent`, English fallback):

```python
"ussd.exit": "Exit",
```

Matching how `"ussd.back"` / `"ussd.more"` / `"ussd.next"` are already stored as bare labels and assembled with their digit at each call site (`f"0. {get_copy('ussd.exit', language)}"`), rather than baking the digit into the copy string itself. `ussd.main_menu`, `ussd.topic_menu`, `ussd.safety_continue`, and `ussd.continue` are the exception — they're already stored as complete pre-formatted menu blocks, so those three get their `"0."` back-digit changed to `"9."` in place (`ussd.main_menu` needs no change, since it never had a "0. Back").

## Data migration for existing translations

`get_copy` prefers an active `ChannelContent` database row over `DEFAULT_COPY`. Migration `backend/apps/channels/migrations/0007_seed_multilingual_ussd_copy.py` already seeded `lg`/`sw`/`nyn` rows for `ussd.topic_menu`, `ussd.safety_continue`, and `ussd.continue` with "0." as the back digit, and there is no seeded row for `ussd.exit` in any language (English has no seeded rows at all — it runs entirely on `DEFAULT_COPY`). Changing `DEFAULT_COPY` alone therefore only fixes English; the other three languages need a new forward-only data migration (following the `0007` migration's own `RunPython` pattern) that:

- Updates the existing `lg`/`sw`/`nyn` rows for `ussd.topic_menu`, `ussd.safety_continue`, and `ussd.continue` so their embedded back digit reads "9." instead of "0." (find by `content_key`/`language`/`channel`, set `text` to the corrected string — not `get_or_create`, since these rows already exist).
- Creates new `ussd.exit` rows for `lg`/`sw`/`nyn`, reusing the bare exit labels already embedded in each language's `ussd.main_menu` string: `lg` → "Fuluma", `sw` → "Toka", `nyn` → "Rugamu".

## Non-goals

- No change to the 3-strikes invalid-input flow (`MAX_INVALID_ATTEMPTS` in `handler.py`) — Exit is always a valid, recognized input, so it never contributes to that counter.
- No change to `goodbye` itself — it stays terminal and doesn't grow an Exit option (there's nothing left to exit from).
- No localization of the new `ussd.exit` copy key beyond the existing `get_copy`/`ChannelContent` mechanism.
- No change to the DRF API, SMS, or Voice channels.

## Testing implications (flagging now, resolving in the plan)

- Every existing assertion of the form `"0. Back" in text` needs updating to `"9. Back"`.
- Reserved-budget growth (one extra trailing line on every paginated screen) shifts exactly how many characters of body text fit per chunk, which can shift chunk boundaries in tests that iterate `chunk_index` against a fixed input length (e.g. `test_long_unbreakable_token_never_exceeds_screen_cap`, `test_token_longer_than_body_budget_is_split_and_stays_within_cap`). These need to be re-run and any hardcoded chunk-count/length expectations adjusted — the 182-char screen cap itself does not change.
- New tests are needed for: pressing "0" from a representative set of mid-flow states (e.g. `situation_list`, `topic_detail`, `action_steps`) transitions straight to `"goodbye"`; and "0. Exit" appears in rendered text for `language_select`, `main_menu`, and at least one screen from each render family (`_chunked_screen`-based, list-paging-based, no-items-fallback-based).
