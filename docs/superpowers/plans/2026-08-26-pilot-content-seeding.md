# Pilot Content Seeding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Seed Sauti Yo with real, publicly-sourced pilot content across four situations (workplace problems, eviction/housing, domestic violence, sexual harassment) so the USSD channel and frontend have something real to serve, with every claim traceable to a cited source and nothing marked as human-verified.

**Architecture:** One new idempotent Django management command, `seed_pilot_content`, following the exact `update_or_create` + `@transaction.atomic` pattern already established by `apps/core/management/commands/seed_demo.py`. Pure data — no application code changes, no schema changes.

**Tech Stack:** Django's ORM via `manage.py` management commands. No new dependencies.

## Global Constraints

- Every `RightsTopic` gets `verification_status="review_required"` and `reviewed_by=""` — never `"verified"`. This is deliberate, not a placeholder: nothing here has been signed off by a human with legal/NGO authority.
- Every `RightsTopic` gets real `source_name`/`source_url` values citing the actual source used (see spec: `docs/superpowers/specs/2026-08-26-pilot-content-design.md`).
- Every `SupportService` gets `verification_status="review_required"` and `is_active=True`.
- The command must be idempotent — running it twice produces the same rows, not duplicates (`update_or_create` keyed on `slug` for situations/topics, `(rights_topic, trigger_key)` for safety responses, `name` for support services).
- Does not modify `apps/core/management/commands/seed_demo.py` or `backend/seed/*.json`.
- Rights content stays English-only (matches the existing USSD design decision — no translation work here).

---

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `backend/apps/core/management/commands/seed_pilot_content.py` | Create | Seeds all four pilot situations, their topics/steps/safety responses, and four support services |

---

### Task 1: Command scaffold + standard-risk situations (Workplace, Eviction/Housing)

**Files:**
- Create: `backend/apps/core/management/commands/seed_pilot_content.py`

**Interfaces:**
- Consumes: `apps.rights.models.{Situation, RightsTopic, ActionStep, SituationRightsTopic}`, `apps.support.models.SupportService` (all pre-existing, unchanged)
- Produces: a `Command` class with a `_support_service(self, **kwargs) -> SupportService` helper (pops `name` from kwargs, `update_or_create`s on it, defaults `verification_status="review_required"` and `is_active=True` unless overridden) — consumed again by Task 2's methods on the same class.

- [ ] **Step 1: Write the command with the workplace and eviction situations**

Create `backend/apps/core/management/commands/seed_pilot_content.py`:

```python
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.rights.models import (
    ActionStep,
    RightsTopic,
    SafetyResponse,
    Situation,
    SituationRightsTopic,
)
from apps.support.models import SupportService


class Command(BaseCommand):
    help = (
        "Seed Sauti Yo with pilot rights content (workplace, housing, "
        "domestic violence, sexual harassment). Idempotent — safe to re-run."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding Sauti Yo pilot content...")

        self._seed_workplace()
        self._seed_eviction()

        self.stdout.write(
            self.style.SUCCESS("Sauti Yo pilot content seeded successfully.")
        )

    def _support_service(self, **kwargs):
        name = kwargs.pop("name")
        service, _ = SupportService.objects.update_or_create(
            name=name,
            defaults={
                "verification_status": "review_required",
                "is_active": True,
                **kwargs,
            },
        )
        return service

    def _seed_action_steps(self, rights_topic, steps):
        for order, title, description, is_safety_critical in steps:
            ActionStep.objects.update_or_create(
                rights_topic=rights_topic,
                order=order,
                defaults={
                    "title": title,
                    "description": description,
                    "is_safety_critical": is_safety_critical,
                    "is_active": True,
                },
            )

    def _seed_workplace(self):
        situation, _ = Situation.objects.update_or_create(
            slug="problem-at-work",
            defaults={
                "title": "I have a problem at work",
                "description": (
                    "Understand your rights and explore practical "
                    "next steps for a workplace problem."
                ),
                "risk_level": "standard",
                "is_active": True,
            },
        )

        rights_topic, _ = RightsTopic.objects.update_or_create(
            slug="workplace-rights",
            defaults={
                "title": "Understanding your workplace rights",
                "summary": (
                    "Sauti Yo can help you understand the issue, "
                    "review relevant rights information, and identify "
                    "possible next steps."
                ),
                "risk_level": "standard",
                "source_name": "Employment Act, 2006 (Cap 226), Laws of Uganda",
                "source_url": (
                    "https://bills.parliament.ug/attachments/Laws%20of%20"
                    "Uganda%20(Acts)%20-%20THE%20EMPLOYMENT%20ACT,%202006.pdf"
                ),
                "reviewed_by": "",
                "verification_status": "review_required",
                "is_active": True,
            },
        )

        SituationRightsTopic.objects.get_or_create(
            situation=situation,
            rights_topic=rights_topic,
        )

        self._seed_action_steps(
            rights_topic,
            [
                (
                    1,
                    "Understand what happened",
                    "Identify the workplace issue and keep a clear "
                    "record of important details.",
                    False,
                ),
                (
                    2,
                    "Understand the relevant right",
                    "Review verified information that may apply to "
                    "your situation.",
                    False,
                ),
                (
                    3,
                    "Keep useful information",
                    "Where safe, keep relevant documents, dates, "
                    "messages, or other records.",
                    False,
                ),
                (
                    4,
                    "Choose a practical next step",
                    "Consider an appropriate next action or connect "
                    "with a verified support service.",
                    False,
                ),
            ],
        )

        legal_aid = self._support_service(
            name="Uganda Law Society Legal Aid Project",
            service_type="Legal Aid",
            description=(
                "Free legal advice, representation, and referrals for "
                "the poor, indigent, and vulnerable."
            ),
            phone_number="0800100150",
            coverage="National",
            is_emergency_service=False,
        )
        rights_topic.support_services.add(legal_aid)

    def _seed_eviction(self):
        situation, _ = Situation.objects.update_or_create(
            slug="facing-eviction",
            defaults={
                "title": "I'm facing eviction or a housing problem",
                "description": (
                    "Understand your rights as a tenant, what a lawful "
                    "eviction looks like, and what to do if you're "
                    "being evicted unfairly."
                ),
                "risk_level": "standard",
                "is_active": True,
            },
        )

        rights_topic, _ = RightsTopic.objects.update_or_create(
            slug="housing-and-eviction-rights",
            defaults={
                "title": "Your rights as a tenant",
                "summary": (
                    "Ugandan law sets minimum notice periods before you "
                    "can be evicted and requires evictions to follow a "
                    "lawful process. If you're evicted unlawfully, you "
                    "have a right to seek relief."
                ),
                "risk_level": "standard",
                "source_name": (
                    "Landlord and Tenant Act, 2022 (Chapter 238), "
                    "Laws of Uganda"
                ),
                "source_url": (
                    "https://ulii.org/en/akn/ug/act/2022/9/"
                    "eng@2023-12-31/source"
                ),
                "reviewed_by": "",
                "verification_status": "review_required",
                "is_active": True,
            },
        )

        SituationRightsTopic.objects.get_or_create(
            situation=situation,
            rights_topic=rights_topic,
        )

        self._seed_action_steps(
            rights_topic,
            [
                (
                    1,
                    "Check your notice period",
                    "By law you must be given written notice before "
                    "eviction: at least 7 days for a weekly tenancy, "
                    "30 days for a monthly tenancy, or 60 days for a "
                    "yearly tenancy. A shorter period in your tenancy "
                    "agreement is not valid.",
                    False,
                ),
                (
                    2,
                    "Know what a lawful eviction looks like",
                    "For non-payment of rent, your landlord can only "
                    "re-enter after your payment is more than 30 days "
                    "overdue, and the eviction must happen with the "
                    "Local Council and Police present.",
                    False,
                ),
                (
                    3,
                    "Keep your records",
                    "Keep your tenancy agreement and proof of rent "
                    "payments — these matter if you need to show an "
                    "eviction was unlawful.",
                    False,
                ),
                (
                    4,
                    "Get help if you're evicted unlawfully",
                    "If your landlord evicts you without following the "
                    "law, you can seek relief from court, including "
                    "compensation. Free legal aid is available.",
                    False,
                ),
            ],
        )

        legal_aid = self._support_service(
            name="Uganda Law Society Legal Aid Project",
            service_type="Legal Aid",
            description=(
                "Free legal advice, representation, and referrals for "
                "the poor, indigent, and vulnerable."
            ),
            phone_number="0800100150",
            coverage="National",
            is_emergency_service=False,
        )
        rights_topic.support_services.add(legal_aid)
```

Note: `_seed_eviction` calls `self._support_service(...)` with the same `name="Uganda Law Society Legal Aid Project"` as `_seed_workplace` — this is deliberate, not a copy-paste bug. `update_or_create` keyed on `name` means the second call finds and reuses the same row rather than creating a duplicate, so each `_seed_*` method stays independently correct regardless of call order.

- [ ] **Step 2: Run the command**

Run: `cd backend && /Users/admin/Desktop/Sauti\ Yo/Sauti-Yo/.venv/bin/python manage.py seed_pilot_content`
Expected:
```
Seeding Sauti Yo pilot content...
Sauti Yo pilot content seeded successfully.
```

- [ ] **Step 3: Verify via Django shell**

Run: `cd backend && /Users/admin/Desktop/Sauti\ Yo/Sauti-Yo/.venv/bin/python manage.py shell -c "
from apps.rights.models import Situation, RightsTopic
from apps.support.models import SupportService

s = Situation.objects.get(slug='facing-eviction')
print('situation:', s.title, s.risk_level)

t = RightsTopic.objects.get(slug='housing-and-eviction-rights')
print('topic verification_status:', t.verification_status)
print('topic source:', t.source_name)
print('action steps:', t.action_steps.count())
print('support services:', [sv.name for sv in t.support_services.all()])

legal_aid = SupportService.objects.get(name='Uganda Law Society Legal Aid Project')
print('legal aid phone:', legal_aid.phone_number, legal_aid.verification_status)
"`

Expected output:
```
situation: I'm facing eviction or a housing problem standard
topic verification_status: review_required
topic source: Landlord and Tenant Act, 2022 (Chapter 238), Laws of Uganda
action steps: 4
support services: ['Uganda Law Society Legal Aid Project']
legal aid phone: 0800100150 review_required
```

- [ ] **Step 4: Verify idempotency — run the command again**

Run: `cd backend && /Users/admin/Desktop/Sauti\ Yo/Sauti-Yo/.venv/bin/python manage.py shell -c "
from apps.rights.models import Situation, ActionStep
from apps.support.models import SupportService
print('situations before second run:', Situation.objects.filter(slug__in=['problem-at-work', 'facing-eviction']).count())
print('support services before second run:', SupportService.objects.count())
"`
Then re-run: `cd backend && /Users/admin/Desktop/Sauti\ Yo/Sauti-Yo/.venv/bin/python manage.py seed_pilot_content`
Then re-run the same shell check — counts must be identical (2 situations, 1 support service so far), confirming no duplicates were created.

- [ ] **Step 5: Commit**

```bash
git add backend/apps/core/management/commands/seed_pilot_content.py
git commit -m "feat: seed workplace and eviction pilot content"
```

---

### Task 2: Safety-critical situations (Domestic Violence, Sexual Harassment) + remaining support services

**Files:**
- Modify: `backend/apps/core/management/commands/seed_pilot_content.py`

**Interfaces:**
- Consumes: `self._support_service`, `self._seed_action_steps` (Task 1), `apps.rights.models.SafetyResponse` (pre-existing, unchanged)
- Produces: `_seed_domestic_violence`, `_seed_sexual_harassment` methods, both called from `handle()`

This is the safety-critical half of the seed data — the two situations that drive the USSD safety gate. Double-check `risk_level` and the `SafetyResponse.trigger_key="default"` value against the spec exactly; a typo in either silently disables the gate for that topic (this exact bug class broke the feature once already during the USSD build).

- [ ] **Step 1: Add the domestic violence and sexual harassment methods**

In `backend/apps/core/management/commands/seed_pilot_content.py`, update `handle()` to also call the two new methods:

```python
    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding Sauti Yo pilot content...")

        self._seed_workplace()
        self._seed_eviction()
        self._seed_domestic_violence()
        self._seed_sexual_harassment()

        self.stdout.write(
            self.style.SUCCESS("Sauti Yo pilot content seeded successfully.")
        )
```

Then append these two new methods to the `Command` class (after `_seed_eviction`):

```python
    def _seed_domestic_violence(self):
        situation, _ = Situation.objects.update_or_create(
            slug="domestic-violence",
            defaults={
                "title": "I'm experiencing domestic violence",
                "description": (
                    "Information on your legal protections and how to "
                    "get immediate help if you or someone you know is "
                    "experiencing domestic violence."
                ),
                "risk_level": "high_risk",
                "is_active": True,
            },
        )

        rights_topic, _ = RightsTopic.objects.update_or_create(
            slug="domestic-violence-protection",
            defaults={
                "title": "Your right to protection under the law",
                "summary": (
                    "Uganda's Domestic Violence Act lets you apply for "
                    "a protection order against an abuser, including "
                    "without them being present, and courts can order "
                    "an abuser to leave the home."
                ),
                "risk_level": "high_risk",
                "source_name": (
                    "Domestic Violence Act, 2010 (Act No. 3 of 2010), "
                    "Laws of Uganda"
                ),
                "source_url": (
                    "https://ulii.org/en/akn/ug/act/2010/3/eng@2023-12-31"
                ),
                "reviewed_by": "",
                "verification_status": "review_required",
                "is_active": True,
            },
        )

        SituationRightsTopic.objects.get_or_create(
            situation=situation,
            rights_topic=rights_topic,
        )

        SafetyResponse.objects.update_or_create(
            rights_topic=rights_topic,
            trigger_key="default",
            defaults={
                "message": (
                    "If you are in immediate danger, get to a safe "
                    "place if you can and call the Uganda Police GBV "
                    "Helpline on 0800 199 195 (toll-free) or go to the "
                    "nearest police station now. This is not a "
                    "substitute for emergency help — it's here so you "
                    "know your rights once you're safe: Ugandan law "
                    "lets you apply for a protection order against an "
                    "abuser, and a court can order them to leave your "
                    "home."
                ),
                "is_active": True,
            },
        )

        self._seed_action_steps(
            rights_topic,
            [
                (
                    1,
                    "Get to safety first",
                    "If you're in danger right now, prioritise getting "
                    "somewhere safe over anything else on this list.",
                    True,
                ),
                (
                    2,
                    "Report to the Police Family & Child Protection desk",
                    "You can report at any police station, or call the "
                    "GBV helpline on 0800 199 195.",
                    False,
                ),
                (
                    3,
                    "Ask about a protection order",
                    "You or someone on your behalf can apply to a "
                    "magistrate's court for a protection order — this "
                    "can be done without your abuser present.",
                    False,
                ),
                (
                    4,
                    "Reach out for ongoing support",
                    "Organisations like MIFUMI and FIDA-Uganda offer "
                    "confidential help, counselling, and further legal "
                    "support.",
                    False,
                ),
            ],
        )

        police_gbv = self._support_service(
            name="Uganda Police GBV Helpline",
            service_type="Emergency / GBV Response",
            description=(
                "Toll-free helpline run by the Uganda Police Force "
                "Department of Child and Family Protection for "
                "reporting gender-based violence and getting help."
            ),
            phone_number="0800199195",
            coverage="National",
            is_emergency_service=True,
        )
        mifumi = self._support_service(
            name="MIFUMI Domestic Violence Helpline",
            service_type="Counselling & Shelter",
            description=(
                "Confidential helpline and support services for "
                "women, children, and youth affected by domestic "
                "violence."
            ),
            phone_number="0800200250",
            coverage="National",
            is_emergency_service=False,
        )
        fida = self._support_service(
            name="FIDA-Uganda",
            service_type="Legal Aid",
            description=(
                "Free legal aid and support from the Uganda "
                "Association of Women Lawyers."
            ),
            phone_number="0800111511",
            coverage="National",
            is_emergency_service=False,
        )
        rights_topic.support_services.add(police_gbv, mifumi, fida)

    def _seed_sexual_harassment(self):
        situation, _ = Situation.objects.update_or_create(
            slug="sexual-harassment",
            defaults={
                "title": "I'm experiencing sexual harassment",
                "description": (
                    "Information on your rights if you're facing "
                    "sexual harassment, particularly at work, and how "
                    "to report it safely."
                ),
                "risk_level": "sensitive",
                "is_active": True,
            },
        )

        rights_topic, _ = RightsTopic.objects.update_or_create(
            slug="sexual-harassment-rights",
            defaults={
                "title": "Your rights against sexual harassment",
                "summary": (
                    "Ugandan law requires workplaces to have a sexual "
                    "harassment policy and gives you the right to "
                    "report confidentially, including to a Labour "
                    "Officer."
                ),
                "risk_level": "sensitive",
                "source_name": (
                    "Employment Act, 2006, s.7(1) and Employment "
                    "(Sexual Harassment) Regulations, 2012"
                ),
                "source_url": (
                    "https://ulii.org/akn/ug/act/2006/6/eng@2023-12-31/source"
                ),
                "reviewed_by": "",
                "verification_status": "review_required",
                "is_active": True,
            },
        )

        SituationRightsTopic.objects.get_or_create(
            situation=situation,
            rights_topic=rights_topic,
        )

        SafetyResponse.objects.update_or_create(
            rights_topic=rights_topic,
            trigger_key="default",
            defaults={
                "message": (
                    "This section covers sexual harassment, which can "
                    "be difficult to read about. Confidential help is "
                    "available if you'd rather talk to someone first "
                    "— FIDA-Uganda (0800 111 511) offers free, "
                    "confidential legal support."
                ),
                "is_active": True,
            },
        )

        self._seed_action_steps(
            rights_topic,
            [
                (
                    1,
                    "Write down what happened",
                    "Note the date, what happened, and any witnesses, "
                    "as soon as you safely can.",
                    False,
                ),
                (
                    2,
                    "Report it internally first, if safe to do so",
                    "Workplaces with 25+ staff are legally required to "
                    "have a sexual harassment policy and committee — "
                    "you can report to them or your supervisor.",
                    False,
                ),
                (
                    3,
                    "Report to a Labour Officer if needed",
                    "If it's unresolved or you don't feel safe reporting "
                    "internally, a Labour Officer must keep your report "
                    "confidential.",
                    False,
                ),
                (
                    4,
                    "Get free legal advice",
                    "FIDA-Uganda and the Uganda Law Society Legal Aid "
                    "Project both offer free, confidential support.",
                    False,
                ),
            ],
        )

        fida = self._support_service(
            name="FIDA-Uganda",
            service_type="Legal Aid",
            description=(
                "Free legal aid and support from the Uganda "
                "Association of Women Lawyers."
            ),
            phone_number="0800111511",
            coverage="National",
            is_emergency_service=False,
        )
        legal_aid = self._support_service(
            name="Uganda Law Society Legal Aid Project",
            service_type="Legal Aid",
            description=(
                "Free legal advice, representation, and referrals for "
                "the poor, indigent, and vulnerable."
            ),
            phone_number="0800100150",
            coverage="National",
            is_emergency_service=False,
        )
        rights_topic.support_services.add(fida, legal_aid)
```

- [ ] **Step 2: Run the command**

Run: `cd backend && /Users/admin/Desktop/Sauti\ Yo/Sauti-Yo/.venv/bin/python manage.py seed_pilot_content`
Expected:
```
Seeding Sauti Yo pilot content...
Sauti Yo pilot content seeded successfully.
```

- [ ] **Step 3: Verify the safety-critical content specifically**

Run: `cd backend && /Users/admin/Desktop/Sauti\ Yo/Sauti-Yo/.venv/bin/python manage.py shell -c "
from apps.rights.models import Situation, RightsTopic, SafetyResponse

for slug, topic_slug in [
    ('domestic-violence', 'domestic-violence-protection'),
    ('sexual-harassment', 'sexual-harassment-rights'),
]:
    s = Situation.objects.get(slug=slug)
    t = RightsTopic.objects.get(slug=topic_slug)
    sr = SafetyResponse.objects.get(rights_topic=t, trigger_key='default')
    print(slug, '-> situation.risk_level:', s.risk_level, '| topic.risk_level:', t.risk_level, '| safety_response.is_active:', sr.is_active)
    print('  support services:', [sv.name for sv in t.support_services.all()])
"`

Expected output:
```
domestic-violence -> situation.risk_level: high_risk | topic.risk_level: high_risk | safety_response.is_active: True
  support services: ['Uganda Police GBV Helpline', 'MIFUMI Domestic Violence Helpline', 'FIDA-Uganda']
sexual-harassment -> situation.risk_level: sensitive | topic.risk_level: sensitive | safety_response.is_active: True
  support services: ['FIDA-Uganda', 'Uganda Law Society Legal Aid Project']
```

Both `risk_level` values must be `"sensitive"` or `"high_risk"` (matching `_enter_topic`'s gating check in `apps/channels/ussd/menus.py`) — if either prints `"standard"`, the USSD safety gate will silently not fire for that topic and this step must not be marked passing.

- [ ] **Step 4: Confirm the USSD flow actually gates on this content**

Run: `cd backend && /Users/admin/Desktop/Sauti\ Yo/Sauti-Yo/.venv/bin/python manage.py shell -c "
from apps.channels.ussd import menus
from apps.rights.models import RightsTopic

topic = RightsTopic.objects.get(slug='domestic-violence-protection')
next_state, context = menus._enter_topic('domestic-violence', topic)
print('next_state:', next_state)
"`
Expected: `next_state: safety_gate`

This confirms the seeded content actually reaches the safety gate through the real USSD routing function, not just that the model fields look right in isolation.

- [ ] **Step 5: Verify idempotency — run the full command again**

Run: `cd backend && /Users/admin/Desktop/Sauti\ Yo/Sauti-Yo/.venv/bin/python manage.py shell -c "
from apps.rights.models import Situation, RightsTopic, ActionStep, SafetyResponse
from apps.support.models import SupportService
print('situations:', Situation.objects.count())
print('rights topics:', RightsTopic.objects.count())
print('action steps:', ActionStep.objects.count())
print('safety responses:', SafetyResponse.objects.count())
print('support services:', SupportService.objects.count())
"`
Note the counts, then re-run: `cd backend && /Users/admin/Desktop/Sauti\ Yo/Sauti-Yo/.venv/bin/python manage.py seed_pilot_content`
Then re-run the same shell check — all five counts must be unchanged (expect: 4 situations from this command — note `seed_demo.py`'s own situation may add to the total if it was also run separately, so compare the count before/after this command's second run, not an absolute number — 4 rights topics, 16 action steps, 2 safety responses, 4 support services from this command specifically).

- [ ] **Step 6: Commit**

```bash
git add backend/apps/core/management/commands/seed_pilot_content.py
git commit -m "feat: seed domestic violence and sexual harassment pilot content"
```

---

## Post-plan notes (not part of this implementation, tracked for follow-up)

- `SupportService` has no `source_name`/`source_url` fields to record where a phone number came from — the citations for this task's four support services live in the spec doc, not the database. Noted in the spec as a schema follow-up, not addressed here.
- None of this content is human-reviewed. `verification_status="review_required"` is the correct state, not a bug — a person with real legal/NGO authority should review before this reaches real users in a crisis, especially the domestic violence and sexual harassment content.
- Availability windows (e.g. "24/7" vs business hours) were not confidently sourced for any of the four support services and were left blank — a reviewer should fill these in from direct confirmation with each organization.
