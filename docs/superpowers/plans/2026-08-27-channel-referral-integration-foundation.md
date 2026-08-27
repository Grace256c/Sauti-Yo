# Channel-Referral Integration: Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the shared, channel-agnostic foundation — a reusable partner-matching service, a `Referral.contact_phone` field, and a `create_citizen_referral()` service — that the SMS, voice, and USSD integration plans will each call, per `docs/superpowers/specs/2026-08-27-channel-referral-integration-design.md`.

**Architecture:** Two new in-process service modules, no HTTP self-calls, matching the existing pattern where `apps.channels` calls `apps.rights.services` directly. `apps/partners/services.py::find_matching_organisations()` is extracted unchanged from the existing `PublicPartnerMatchAPIView`, so the public `/api/partners/matches/` endpoint keeps its exact current behavior. `apps/referrals/services.py::create_citizen_referral()` is new — it composes `find_matching_organisations()` with a new `Referral.contact_phone` field and a new `Referral.generate_reference()` staticmethod (deduplicating a reference-generation snippet that was already copy-pasted across two views) to create a `Referral` for a citizen contacting via any channel.

**Tech Stack:** Django (existing project), Django's built-in test runner (`manage.py test`), PostgreSQL.

## Global Constraints

- No HTTP self-calls — `create_citizen_referral()` and `find_matching_organisations()` are plain Python functions called in-process, exactly like `apps.rights.services.get_situation_detail()`.
- `find_matching_organisations()` must produce byte-identical output to the current inline `PublicPartnerMatchAPIView` logic — this is an extraction, not a behavior change. `is_test=True` organisations are always excluded.
- `create_citizen_referral()` is risk-agnostic — it has no knowledge of `Situation.risk_level` and does not gate on it. The `high_risk` exclusion is the calling channel's responsibility (enforced in the SMS/voice/USSD integration plans, not here).
- `create_citizen_referral()` trusts its caller on consent — it always sets `citizen_consent_to_share=True` unconditionally. Capturing genuine, explicit consent from the citizen is the calling channel's responsibility, not this function's.
- `Referral.reference` values must always be generated via `Referral.generate_reference()` — no call site should build the `"SY-REF-..."` string itself.

---

## Task 1: Extract `find_matching_organisations` into `apps/partners/services.py`

**Files:**
- Create: `backend/apps/partners/services.py`
- Modify: `backend/apps/partners/views.py:980-1203`
- Test: `backend/apps/partners/tests.py`

**Interfaces:**
- Consumes: `apps.partners.models.PartnerOrganisation`, `apps.partners.serializers.PublicPartnerMatchSerializer` (both already exist).
- Produces: `apps.partners.services.find_matching_organisations(category: str, district: str, language: str, channel: str) -> list[dict]` — each dict shaped like `PublicPartnerMatchSerializer` output (`id`, `organisation_name`, `organisation_type`, `service_description`, `public_phone`, `public_email`, `website`, `districts_served`, `nationwide`, `languages`, `support_channels`, `rights_categories`, `support_types`, `free_services`, `appointment_required`, `availability_note`, `score`, `reasons`), sorted by `score` descending. `channel` accepts either `"in-person"` or `"in_person"` (normalized internally, same as today).

- [ ] **Step 1: Write the failing test**

Add to `backend/apps/partners/tests.py`, right after the existing `PublicPartnerMatchTests` class (which ends around line 296):

```python
from apps.partners.services import find_matching_organisations


class FindMatchingOrganisationsServiceTests(TestCase):
    def setUp(self):
        service = SupportService.objects.create(
            name="Service Layer Test Partner",
            service_type="Legal Aid",
            verification_status="verified",
            is_active=True,
        )

        self.organisation = PartnerOrganisation.objects.create(
            support_service=service,
            organisation_type="legal_aid",
            is_active=True,
            is_test=False,
        )

        PartnerServiceConfiguration.objects.create(
            organisation=self.organisation,
            rights_categories=["work-employment"],
            languages=["English"],
            support_channels=["phone"],
            districts_served=["Kampala"],
            accepting_referrals=True,
        )

        PartnerVerificationRequest.objects.create(
            organisation=self.organisation,
            status="verified",
        )

    def test_matching_organisation_is_returned_and_scored(self):
        matches = find_matching_organisations(
            category="work-employment",
            district="Kampala",
            language="English",
            channel="phone",
        )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["id"], self.organisation.id)
        self.assertEqual(matches[0]["score"], 90)

    def test_non_matching_category_is_excluded(self):
        matches = find_matching_organisations(
            category="eviction-housing",
            district="Kampala",
            language="English",
            channel="phone",
        )

        self.assertEqual(matches, [])

    def test_in_person_channel_alias_is_normalized(self):
        PartnerServiceConfiguration.objects.filter(
            organisation=self.organisation,
        ).update(support_channels=["in_person"])

        matches = find_matching_organisations(
            category="work-employment",
            district="Kampala",
            language="English",
            channel="in-person",
        )

        self.assertEqual(len(matches), 1)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend && python manage.py test apps.partners.tests.FindMatchingOrganisationsServiceTests -v 2`
Expected: FAIL with `ModuleNotFoundError: No module named 'apps.partners.services'`

- [ ] **Step 3: Create `apps/partners/services.py` with the extracted logic**

Create `backend/apps/partners/services.py`:

```python
"""
Partner-matching service layer.

find_matching_organisations() is called directly by apps.referrals.services
(for citizen referrals originating from USSD/SMS/voice) and by
PublicPartnerMatchAPIView (for the web citizen-support picker) - kept as a
single function so both callers see identical matching/scoring behavior.
"""

from apps.partners.models import PartnerOrganisation
from apps.partners.serializers import PublicPartnerMatchSerializer


def find_matching_organisations(category, district, language, channel):
    # Frontend uses "in-person"; backend stores "in_person".
    normalized_channel = (
        "in_person" if channel == "in-person" else channel
    )

    organisations = (
        PartnerOrganisation.objects
        .filter(
            is_active=True,
            is_test=False,
            service_configuration__accepting_referrals=True,
            verification_requests__status="verified",
        )
        .select_related(
            "support_service",
            "service_configuration",
        )
        .distinct()
    )

    matches = []

    for organisation in organisations:
        config = organisation.service_configuration

        if category not in (config.rights_categories or []):
            continue

        if not (
            config.nationwide
            or district in (config.districts_served or [])
        ):
            continue

        if language not in (config.languages or []):
            continue

        if normalized_channel not in (config.support_channels or []):
            continue

        score = 0
        reasons = []

        if category in (config.rights_categories or []):
            score += 30
            reasons.append("Supports this type of rights issue")

        if (
            config.nationwide
            or district in (config.districts_served or [])
        ):
            score += 25
            reasons.append(
                "Provides support nationally"
                if config.nationwide
                else f"Provides support in {district}"
            )

        if language in (config.languages or []):
            score += 20
            reasons.append(f"Provides support in {language}")

        if normalized_channel in (config.support_channels or []):
            score += 15

            channel_reason = {
                "remote": "Offers remote support",
                "phone": "Offers telephone support",
                "in_person": "Offers in-person support",
            }.get(
                normalized_channel,
                "Offers the preferred support method",
            )

            reasons.append(channel_reason)

        support_service = organisation.support_service

        data = {
            "id": organisation.id,
            "organisation_name": support_service.name,
            "organisation_type": organisation.organisation_type,
            "service_description": (
                config.service_description
                or support_service.description
                or ""
            ),
            "public_phone": organisation.public_phone,
            "public_email": organisation.public_email,
            "website": support_service.website,
            "districts_served": config.districts_served or [],
            "nationwide": config.nationwide,
            "languages": config.languages or [],
            "support_channels": config.support_channels or [],
            "rights_categories": config.rights_categories or [],
            "support_types": config.support_types or [],
            "free_services": config.free_services,
            "appointment_required": config.appointment_required,
            "availability_note": config.availability_note,
            "score": score,
            "reasons": reasons,
        }

        matches.append(PublicPartnerMatchSerializer(data).data)

    matches.sort(key=lambda item: item["score"], reverse=True)

    return matches
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd backend && python manage.py test apps.partners.tests.FindMatchingOrganisationsServiceTests -v 2`
Expected: PASS (3 tests)

- [ ] **Step 5: Replace the inline logic in `PublicPartnerMatchAPIView` with a call to the service**

In `backend/apps/partners/views.py`, replace lines 980-1203 (from `from rest_framework.permissions import AllowAny` through the end of the file) with:

```python
from rest_framework.permissions import AllowAny

from .services import find_matching_organisations


class PublicPartnerMatchAPIView(APIView):
    """
    Public endpoint for matching citizens with eligible
    verified partner organisations.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        category = (
            request.query_params.get("category")
            or ""
        ).strip()

        district = (
            request.query_params.get("district")
            or ""
        ).strip()

        language = (
            request.query_params.get("language")
            or ""
        ).strip()

        channel = (
            request.query_params.get("channel")
            or ""
        ).strip()

        if not all(
            [
                category,
                district,
                language,
                channel,
            ]
        ):
            return Response(
                {
                    "detail": (
                        "category, district, language and "
                        "channel are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        matches = find_matching_organisations(
            category=category,
            district=district,
            language=language,
            channel=channel,
        )

        return Response(
            matches,
            status=status.HTTP_200_OK,
        )
```

- [ ] **Step 6: Run the full partners test suite to confirm no regression**

Run: `cd backend && python manage.py test apps.partners -v 2`
Expected: PASS, including the pre-existing `PublicPartnerMatchTests` class (behavior must be unchanged)

- [ ] **Step 7: Commit**

```bash
git add backend/apps/partners/services.py backend/apps/partners/views.py backend/apps/partners/tests.py
git commit -m "refactor: extract partner matching into apps.partners.services"
```

---

## Task 2: Add `Referral.contact_phone`

**Files:**
- Modify: `backend/apps/referrals/models.py`
- Create: `backend/apps/referrals/migrations/0002_referral_contact_phone.py` (via `makemigrations`)
- Test: `backend/apps/referrals/tests.py`

**Interfaces:**
- Consumes: `apps.referrals.models.Referral` (existing).
- Produces: `Referral.contact_phone` — `CharField(max_length=50, blank=True)`, default `""`.

- [ ] **Step 1: Write the failing test**

Add to `backend/apps/referrals/tests.py`, after the `ReferralAPITests` class (which ends around line 224, right before `class CitizenReferralTestOrganisationTests`):

```python
class ReferralContactPhoneFieldTests(TestCase):
    def test_contact_phone_defaults_to_blank(self):
        service = SupportService.objects.create(
            name="Contact Phone Field Test Partner",
            service_type="Legal Aid",
            verification_status="verified",
            is_active=True,
        )

        organisation = PartnerOrganisation.objects.create(
            support_service=service,
            organisation_type="legal_aid",
            is_active=True,
        )

        referral = Referral.objects.create(
            reference="SY-REF-CONTACT-PHONE-TEST",
            organisation=organisation,
            citizen_consent_to_share=True,
            status="new",
        )

        self.assertEqual(referral.contact_phone, "")

    def test_contact_phone_can_be_set(self):
        service = SupportService.objects.create(
            name="Contact Phone Field Test Partner Two",
            service_type="Legal Aid",
            verification_status="verified",
            is_active=True,
        )

        organisation = PartnerOrganisation.objects.create(
            support_service=service,
            organisation_type="legal_aid",
            is_active=True,
        )

        referral = Referral.objects.create(
            reference="SY-REF-CONTACT-PHONE-TEST-2",
            organisation=organisation,
            contact_phone="+256700000000",
            citizen_consent_to_share=True,
            status="new",
        )

        self.assertEqual(referral.contact_phone, "+256700000000")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend && python manage.py test apps.referrals.tests.ReferralContactPhoneFieldTests -v 2`
Expected: FAIL with `TypeError: 'contact_phone' is an invalid keyword argument for this function`

- [ ] **Step 3: Add the field**

In `backend/apps/referrals/models.py`, add `contact_phone` to `Referral` right after the `district` field:

```python
    district = models.CharField(
        max_length=100,
        blank=True,
    )

    contact_phone = models.CharField(
        max_length=50,
        blank=True,
    )

    language = models.CharField(
        max_length=100,
        blank=True,
    )
```

- [ ] **Step 4: Generate and apply the migration**

Run: `cd backend && python manage.py makemigrations referrals`
Expected: Creates `backend/apps/referrals/migrations/0002_referral_contact_phone.py`

Run: `cd backend && python manage.py migrate referrals`
Expected: `Applying referrals.0002_referral_contact_phone... OK`

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd backend && python manage.py test apps.referrals.tests.ReferralContactPhoneFieldTests -v 2`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/apps/referrals/models.py backend/apps/referrals/migrations/0002_referral_contact_phone.py backend/apps/referrals/tests.py
git commit -m "feat: add Referral.contact_phone for asynchronous-channel referrals"
```

---

## Task 3: `Referral.generate_reference()` staticmethod

**Files:**
- Modify: `backend/apps/referrals/models.py`
- Modify: `backend/apps/referrals/views.py:1, 170-199, 470-499`
- Test: `backend/apps/referrals/tests.py`

**Interfaces:**
- Consumes: `apps.referrals.models.Referral` (existing, now with `contact_phone` from Task 2).
- Produces: `Referral.generate_reference() -> str` (staticmethod), returning `f"SY-REF-{uuid.uuid4().hex.upper()}"`.

- [ ] **Step 1: Write the failing test**

Add to `backend/apps/referrals/tests.py`, inside the new `ReferralContactPhoneFieldTests` class area — as its own class right after it:

```python
class ReferralGenerateReferenceTests(TestCase):
    def test_generate_reference_has_expected_prefix_and_length(self):
        reference = Referral.generate_reference()

        self.assertTrue(reference.startswith("SY-REF-"))
        self.assertEqual(len(reference), len("SY-REF-") + 32)

    def test_generate_reference_is_unique_across_calls(self):
        first = Referral.generate_reference()
        second = Referral.generate_reference()

        self.assertNotEqual(first, second)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend && python manage.py test apps.referrals.tests.ReferralGenerateReferenceTests -v 2`
Expected: FAIL with `AttributeError: type object 'Referral' has no attribute 'generate_reference'`

- [ ] **Step 3: Add the staticmethod**

In `backend/apps/referrals/models.py`, add `import uuid` at the top of the file:

```python
import uuid

from django.conf import settings
from django.db import models
```

Then add the staticmethod to `Referral`, right after its `__str__` method:

```python
    def __str__(self):
        return f"{self.reference} — {self.organisation}"

    @staticmethod
    def generate_reference():
        return f"SY-REF-{uuid.uuid4().hex.upper()}"
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd backend && python manage.py test apps.referrals.tests.ReferralGenerateReferenceTests -v 2`
Expected: PASS (2 tests)

- [ ] **Step 5: Update the two existing call sites to use it**

In `backend/apps/referrals/views.py`, remove the now-unused import on line 1:

```python
from uuid import uuid4
```

In `ReferralCreateAPIView` (around line 170), change:

```python
        referral = serializer.save(
            reference=self._generate_reference(),
            status="new",
            shared_at=timezone.now(),
        )
```

to:

```python
        referral = serializer.save(
            reference=Referral.generate_reference(),
            status="new",
            shared_at=timezone.now(),
        )
```

and delete its `_generate_reference` method (around line 196-199):

```python
    def _generate_reference(self):
        return (
            f"SY-REF-{uuid4().hex.upper()}"
        )
```

Repeat the same two changes in `CitizenReferralCreateAPIView` (around lines 470 and 496-499): replace `reference=self._generate_reference()` with `reference=Referral.generate_reference()`, and delete that class's `_generate_reference` method too.

- [ ] **Step 6: Run the full referrals test suite to confirm no regression**

Run: `cd backend && python manage.py test apps.referrals -v 2`
Expected: PASS, including the pre-existing `ReferralAPITests` and `CitizenReferralTestOrganisationTests` classes (reference format is unchanged — same prefix, same length)

- [ ] **Step 7: Commit**

```bash
git add backend/apps/referrals/models.py backend/apps/referrals/views.py backend/apps/referrals/tests.py
git commit -m "refactor: deduplicate referral reference generation into Referral.generate_reference()"
```

---

## Task 4: `apps/referrals/services.py::create_citizen_referral`

**Files:**
- Create: `backend/apps/referrals/services.py`
- Test: `backend/apps/referrals/tests.py`

**Interfaces:**
- Consumes:
  - `apps.partners.services.find_matching_organisations(category, district, language, channel) -> list[dict]` (Task 1)
  - `apps.referrals.models.Referral.generate_reference() -> str` (Task 3)
  - `apps.referrals.models.Referral.contact_phone` (Task 2)
  - `apps.rights.models.Situation`, `apps.rights.models.SituationRightsTopic` (existing)
- Produces: `apps.referrals.services.create_citizen_referral(*, phone_number: str, situation_slug: str, district: str, language: str, origin_channel: str) -> Referral | None`. Returns `None` (no `Referral` created) when the situation doesn't exist/isn't active, has no linked `RightsTopic`, or no partner organisation matches. `origin_channel` is a free-text label (e.g. `"sms"`, `"voice"`, `"ussd"`) recorded in the `ReferralStatusHistory` note and used to build the auto-generated `summary` — it is separate from the support-channel matching value, which is always `"phone"` for these three channels.

- [ ] **Step 1: Write the failing tests**

Add to `backend/apps/referrals/tests.py`. First, extend the existing import block at the top of the file to add the models this task needs:

```python
from apps.rights.models import (
    RightsTopic,
    Situation,
    SituationRightsTopic,
)

from .services import create_citizen_referral
```

Then add a new test class at the end of the file:

```python
class CreateCitizenReferralServiceTests(TestCase):
    def setUp(self):
        self.situation = Situation.objects.create(
            slug="facing-eviction",
            title="Facing eviction",
            risk_level="standard",
        )

        self.topic = RightsTopic.objects.create(
            slug="eviction-housing",
            title="Eviction & Housing Rights",
            summary="Protections around eviction and housing.",
            risk_level="standard",
        )

        SituationRightsTopic.objects.create(
            situation=self.situation,
            rights_topic=self.topic,
        )

        service = SupportService.objects.create(
            name="Eviction Referral Test Partner",
            service_type="Legal Aid",
            verification_status="verified",
            is_active=True,
        )

        self.organisation = PartnerOrganisation.objects.create(
            support_service=service,
            organisation_type="legal_aid",
            is_active=True,
            is_test=False,
        )

        PartnerServiceConfiguration.objects.create(
            organisation=self.organisation,
            rights_categories=["eviction-housing"],
            languages=["en"],
            support_channels=["phone"],
            districts_served=["Kampala"],
            accepting_referrals=True,
        )

        PartnerVerificationRequest.objects.create(
            organisation=self.organisation,
            status="verified",
        )

    def test_creates_referral_when_organisation_matches(self):
        referral = create_citizen_referral(
            phone_number="+256700000001",
            situation_slug="facing-eviction",
            district="Kampala",
            language="en",
            origin_channel="sms",
        )

        self.assertIsNotNone(referral)
        self.assertEqual(referral.organisation, self.organisation)
        self.assertEqual(referral.rights_topic, self.topic)
        self.assertEqual(referral.contact_phone, "+256700000001")
        self.assertEqual(referral.district, "Kampala")
        self.assertEqual(referral.language, "en")
        self.assertEqual(referral.preferred_support_channel, "phone")
        self.assertTrue(referral.citizen_consent_to_share)
        self.assertEqual(referral.status, "new")
        self.assertTrue(referral.reference.startswith("SY-REF-"))
        self.assertIn("Facing eviction", referral.summary)

        history = referral.status_history.get()
        self.assertEqual(history.to_status, "new")
        self.assertIn("sms", history.note)

    def test_returns_none_when_no_organisation_matches(self):
        referral = create_citizen_referral(
            phone_number="+256700000002",
            situation_slug="facing-eviction",
            district="Gulu",
            language="en",
            origin_channel="sms",
        )

        self.assertIsNone(referral)
        self.assertEqual(Referral.objects.count(), 0)

    def test_returns_none_for_unknown_situation(self):
        referral = create_citizen_referral(
            phone_number="+256700000003",
            situation_slug="does-not-exist",
            district="Kampala",
            language="en",
            origin_channel="sms",
        )

        self.assertIsNone(referral)
        self.assertEqual(Referral.objects.count(), 0)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && python manage.py test apps.referrals.tests.CreateCitizenReferralServiceTests -v 2`
Expected: FAIL with `ModuleNotFoundError: No module named 'apps.referrals.services'`

- [ ] **Step 3: Create `apps/referrals/services.py`**

Create `backend/apps/referrals/services.py`:

```python
"""
Referral service layer for citizens contacting via USSD/SMS/voice.

create_citizen_referral() is called directly by apps.channels (not over
HTTP), matching the existing apps.rights.services pattern. It is
risk-agnostic and trusts its caller on consent: gating out high_risk
situations and capturing genuine citizen consent are both the calling
channel's responsibility, not this function's.
"""

from django.utils import timezone

from apps.partners.services import find_matching_organisations
from apps.referrals.models import Referral, ReferralStatusHistory
from apps.rights.models import Situation


def create_citizen_referral(
    *, phone_number, situation_slug, district, language, origin_channel
):
    try:
        situation = Situation.objects.prefetch_related(
            "rights_links__rights_topic",
        ).get(slug=situation_slug, is_active=True)
    except Situation.DoesNotExist:
        return None

    link = situation.rights_links.order_by("id").first()
    if link is None:
        return None

    topic = link.rights_topic

    matches = find_matching_organisations(
        category=topic.slug,
        district=district,
        language=language,
        channel="phone",
    )

    if not matches:
        return None

    best_match = matches[0]

    referral = Referral.objects.create(
        reference=Referral.generate_reference(),
        organisation_id=best_match["id"],
        rights_topic=topic,
        contact_phone=phone_number,
        district=district,
        language=language,
        preferred_support_channel="phone",
        citizen_consent_to_share=True,
        summary=(
            f"{origin_channel.upper()} referral: citizen reported "
            f"'{situation.title}'."
        ),
        status="new",
        shared_at=timezone.now(),
    )

    ReferralStatusHistory.objects.create(
        referral=referral,
        from_status="",
        to_status="new",
        changed_by=None,
        note=f"Referral created via {origin_channel}.",
    )

    return referral
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd backend && python manage.py test apps.referrals.tests.CreateCitizenReferralServiceTests -v 2`
Expected: PASS (3 tests)

- [ ] **Step 5: Run the full referrals and partners test suites to confirm no regression**

Run: `cd backend && python manage.py test apps.referrals apps.partners -v 2`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/apps/referrals/services.py backend/apps/referrals/tests.py
git commit -m "feat: add create_citizen_referral service for USSD/SMS/voice referrals"
```

---

## What this foundation enables

After this plan lands, each channel integration plan (SMS, voice, USSD) only needs to:
1. Gate on `Situation.risk_level != "high_risk"` (already available from `apps.rights.services.get_situation_detail()`).
2. Capture explicit citizen consent and a district reply through its own state machine.
3. Call `create_citizen_referral(phone_number=..., situation_slug=..., district=..., language=..., origin_channel="sms"|"voice"|"ussd")` and branch on whether it returns a `Referral` or `None`.

No channel plan needs to touch `apps.partners`, `apps.referrals`, or `Referral`/`PartnerOrganisation` model internals directly.
