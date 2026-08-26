# Pilot Content Seeding — Design

Date: 2026-08-26
Status: Approved
Scope: `backend/apps/core/management/commands/seed_pilot_content.py` (new) — data only, no application code changes

## Context

Sauti Yo's USSD channel (and the existing citizen-facing frontend) is fully built but has nothing to show: `backend/seed/*.json` are empty, and the only content in the system is a single minimal demo situation ("I have a problem at work") seeded by `apps/core/management/commands/seed_demo.py`, explicitly labeled as unverified demo filler.

This spec covers seeding a focused pilot of real, publicly-sourced content across four situations, following the review workflow the data model already has built in (`verification_status`, `reviewed_by`, `source_name`, `source_url`, `last_reviewed`, `next_review_due` on `RightsTopic`).

## Sourcing policy (binding for this and future content work)

- Content is drawn from real, citable public sources: Ugandan legislation (via ulii.org / bills.parliament.ug) and the published contact details of real, operating support organizations.
- **Nothing seeded here is marked `verification_status="verified"`.** Everything is `"review_required"`, `reviewed_by=""`. This is not a placeholder state — it's the correct, honest state for AI-researched legal content that a person with actual legal/NGO authority has not yet signed off on.
- Every `RightsTopic` gets `source_name` and `source_url` populated with the actual source used, so a reviewer can check the claim against the original.
- Support-service phone numbers are the highest-stakes detail in this content (a wrong emergency number is a real-world harm) and get the same `review_required` treatment — they are real, publicly published numbers as of the research date (2026-08-26), not verified live by calling them.

## Non-goals

- Marking anything as reviewed/verified — that's a human, out-of-band step.
- Translating this content into Luganda/Kiswahili/Runyankole — matches the existing USSD design decision that rights content stays English-only for v1.
- Touching `seed_demo.py` or `backend/seed/*.json` — this is a new, separately-runnable command.
- Any change to application code (models, views, USSD menus) — this is pure data.

## Architecture

One new idempotent management command, `seed_pilot_content.py`, following the exact pattern already established by `seed_demo.py`: `@transaction.atomic`, `update_or_create` keyed on `slug` (situations, topics) or `(rights_topic, trigger_key)` (safety responses) or `name` (support services), safe to re-run.

```python
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.rights.models import (
    ActionStep, RightsTopic, SafetyResponse, Situation, SituationRightsTopic,
)
from apps.support.models import SupportService


class Command(BaseCommand):
    help = "Seed Sauti Yo with pilot rights content (workplace, housing, GBV, sexual harassment)."

    @transaction.atomic
    def handle(self, *args, **options):
        ...
```

## Content

### 1. Workplace Problems (extends the existing situation)

`Situation(slug="problem-at-work")` already exists from `seed_demo.py` — this command updates it via the same slug, does not duplicate it. `risk_level="standard"` (unchanged).

`RightsTopic(slug="workplace-rights")` already exists — this command adds real sourcing and links a support service; action steps are left as `seed_demo.py` created them (they're already generic-safe, non-legal-claim text).

- `source_name`: "Employment Act, 2006 (Cap 226), Laws of Uganda"
- `source_url`: `https://bills.parliament.ug/attachments/Laws%20of%20Uganda%20(Acts)%20-%20THE%20EMPLOYMENT%20ACT,%202006.pdf`
- `verification_status`: `"review_required"`

Linked support service: **Uganda Law Society Legal Aid Project** (see §5).

### 2. Eviction / Housing Rights (new)

`Situation`:
- `slug`: `"facing-eviction"`
- `title`: "I'm facing eviction or a housing problem"
- `description`: "Understand your rights as a tenant, what a lawful eviction looks like, and what to do if you're being evicted unfairly."
- `risk_level`: `"standard"`

`RightsTopic`:
- `slug`: `"housing-and-eviction-rights"`
- `title`: "Your rights as a tenant"
- `summary`: "Ugandan law sets minimum notice periods before you can be evicted and requires evictions to follow a lawful process. If you're evicted unlawfully, you have a right to seek relief."
- `source_name`: "Landlord and Tenant Act, 2022 (Chapter 238), Laws of Uganda"
- `source_url`: `https://ulii.org/en/akn/ug/act/2022/9/eng@2023-12-31/source`
- `verification_status`: `"review_required"`

Action steps:
1. **Check your notice period** — "By law you must be given written notice before eviction: at least 7 days for a weekly tenancy, 30 days for a monthly tenancy, or 60 days for a yearly tenancy. A shorter period in your tenancy agreement is not valid."
2. **Know what a lawful eviction looks like** — "For non-payment of rent, your landlord can only re-enter after your payment is more than 30 days overdue, and the eviction must happen with the Local Council and Police present."
3. **Keep your records** — "Keep your tenancy agreement and proof of rent payments — these matter if you need to show an eviction was unlawful."
4. **Get help if you're evicted unlawfully** — "If your landlord evicts you without following the law, you can seek relief from court, including compensation. Free legal aid is available." (`is_safety_critical=False`)

Linked support service: **Uganda Law Society Legal Aid Project**.

### 3. Domestic Violence / GBV (new — high risk, safety gate)

`Situation`:
- `slug`: `"domestic-violence"`
- `title`: "I'm experiencing domestic violence"
- `description`: "Information on your legal protections and how to get immediate help if you or someone you know is experiencing domestic violence."
- `risk_level`: `"high_risk"`

`RightsTopic`:
- `slug`: `"domestic-violence-protection"`
- `title`: "Your right to protection under the law"
- `summary`: "Uganda's Domestic Violence Act lets you apply for a protection order against an abuser, including without them being present, and courts can order an abuser to leave the home."
- `risk_level`: `"high_risk"` (drives the USSD safety gate)
- `source_name`: "Domestic Violence Act, 2010 (Act No. 3 of 2010), Laws of Uganda"
- `source_url`: `https://ulii.org/en/akn/ug/act/2010/3/eng@2023-12-31`
- `verification_status`: `"review_required"`

`SafetyResponse` (`trigger_key="default"`, `is_active=True`) — shown before anything else:
> "If you are in immediate danger, get to a safe place if you can and call the Uganda Police GBV Helpline on 0800 199 195 (toll-free) or go to the nearest police station now. This is not a substitute for emergency help — it's here so you know your rights once you're safe: Ugandan law lets you apply for a protection order against an abuser, and a court can order them to leave your home."

Action steps:
1. **Get to safety first** — "If you're in danger right now, prioritise getting somewhere safe over anything else on this list." (`is_safety_critical=True`)
2. **Report to the Police Family & Child Protection desk** — "You can report at any police station, or call the GBV helpline on 0800 199 195."
3. **Ask about a protection order** — "You or someone on your behalf can apply to a magistrate's court for a protection order — this can be done without your abuser present."
4. **Reach out for ongoing support** — "Organisations like MIFUMI and FIDA-Uganda offer confidential help, counselling, and further legal support." (`is_safety_critical=False`)

Linked support services: **Uganda Police GBV Helpline** (emergency), **MIFUMI Domestic Violence Helpline**, **FIDA-Uganda**.

### 4. Sexual Harassment (new — sensitive, safety gate)

`Situation`:
- `slug`: `"sexual-harassment"`
- `title`: "I'm experiencing sexual harassment"
- `description`: "Information on your rights if you're facing sexual harassment, particularly at work, and how to report it safely."
- `risk_level`: `"sensitive"`

`RightsTopic`:
- `slug`: `"sexual-harassment-rights"`
- `title`: "Your rights against sexual harassment"
- `summary`: "Ugandan law requires workplaces to have a sexual harassment policy and gives you the right to report confidentially, including to a Labour Officer."
- `risk_level`: `"sensitive"` (drives the USSD safety gate)
- `source_name`: "Employment Act, 2006, s.7(1) and Employment (Sexual Harassment) Regulations, 2012"
- `source_url`: `https://ulii.org/akn/ug/act/2006/6/eng@2023-12-31/source`
- `verification_status`: `"review_required"`

`SafetyResponse` (`trigger_key="default"`, `is_active=True`):
> "This section covers sexual harassment, which can be difficult to read about. Confidential help is available if you'd rather talk to someone first — FIDA-Uganda (0800 111 511) offers free, confidential legal support."

Action steps:
1. **Write down what happened** — "Note the date, what happened, and any witnesses, as soon as you safely can."
2. **Report it internally first, if safe to do so** — "Workplaces with 25+ staff are legally required to have a sexual harassment policy and committee — you can report to them or your supervisor."
3. **Report to a Labour Officer if needed** — "If it's unresolved or you don't feel safe reporting internally, a Labour Officer must keep your report confidential."
4. **Get free legal advice** — "FIDA-Uganda and the Uganda Law Society Legal Aid Project both offer free, confidential support." (`is_safety_critical=False`)

Linked support services: **FIDA-Uganda**, **Uganda Law Society Legal Aid Project**.

### 5. Support services (all `verification_status`-equivalent: `is_active=True`, sourced 2026-08-26, not independently verified by calling)

| Name | Phone | Emergency? | Source |
|---|---|---|---|
| Uganda Police GBV Helpline | 0800 199 195 | Yes | Uganda Police Force, Dept. of Child & Family Protection ([X/Twitter](https://x.com/PoliceUg/status/1835625067910230101)) |
| MIFUMI Domestic Violence Helpline | 0800 200 250 | No | [mifumi.org/contact-us](https://mifumi.org/contact-us/) |
| FIDA-Uganda (free legal aid) | 0800 111 511 | No | [fidauganda.or.ug/contact-us](https://fidauganda.or.ug/contact-us) |
| Uganda Law Society Legal Aid Project | 0800 100 150 | No | [Contact info PDF](https://sird.ealawsociety.org/wp-content/uploads/2023/02/Contact-info-for-Uganda-Law-Society.pdf) |

Each gets `coverage="National"`, `availability` left blank (not confidently sourced — a reviewer should fill this in), `verification_status` field doesn't exist on `SupportService` (only on `RightsTopic`) — instead `is_active=True` and the source is recorded in this spec doc for the reviewer, since the model has no `source_url` field of its own for support services. **Gap noted below.**

## Known model gap (not fixed in this pass)

`SupportService` has no `source_name`/`source_url`/`verification_status` fields — only `RightsTopic` does. This spec's citations for phone numbers live in this document, not in the database, so a future reviewer checking the admin panel won't see where a number came from. Flagged as a follow-up (either add those fields to `SupportService`, or record sourcing in its existing `description` field as a stopgap) — out of scope for this content-seeding pass since it's a schema change, not a content one.

## Testing

This is a data-seeding management command, not application logic — no new automated tests. Verification is: run `manage.py seed_pilot_content`, confirm no errors, then spot-check via `manage.py shell` or the admin that all four situations, their topics, action steps, safety responses, and support-service links exist with `verification_status="review_required"` and the cited sources attached. Re-running the command should be a no-op (idempotent via `update_or_create`).
