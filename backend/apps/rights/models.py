from django.db import models

from apps.support.models import SupportService


class Situation(models.Model):
    RISK_LEVEL_CHOICES = [
        ("standard", "Standard"),
        ("sensitive", "Sensitive"),
        ("high_risk", "High Risk"),
    ]

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    risk_level = models.CharField(
        max_length=20,
        choices=RISK_LEVEL_CHOICES,
        default="standard",
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class RightsTopic(models.Model):
    RISK_LEVEL_CHOICES = [
        ("standard", "Standard"),
        ("sensitive", "Sensitive"),
        ("high_risk", "High Risk"),
    ]

    VERIFICATION_STATUS_CHOICES = [
        ("verified", "Verified"),
        ("review_required", "Review Required"),
        ("expired", "Expired"),
        ("archived", "Archived"),
    ]

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=150)

    risk_level = models.CharField(
        max_length=20,
        choices=RISK_LEVEL_CHOICES,
        default="standard",
    )

    summary = models.TextField()

    source_name = models.CharField(
        max_length=255,
        blank=True,
    )

    source_url = models.URLField(
        blank=True,
    )

    reviewed_by = models.CharField(
        max_length=255,
        blank=True,
    )

    last_reviewed = models.DateField(
        null=True,
        blank=True,
    )

    next_review_due = models.DateField(
        null=True,
        blank=True,
    )

    verification_status = models.CharField(
        max_length=30,
        choices=VERIFICATION_STATUS_CHOICES,
        default="review_required",
    )

    support_services = models.ManyToManyField(
        SupportService,
        related_name="rights_topics",
        blank=True,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class SituationRightsTopic(models.Model):
    situation = models.ForeignKey(
        Situation,
        on_delete=models.CASCADE,
        related_name="rights_links",
    )

    rights_topic = models.ForeignKey(
        RightsTopic,
        on_delete=models.CASCADE,
        related_name="situation_links",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["situation", "rights_topic"],
                name="unique_situation_rights_topic",
            )
        ]

    def __str__(self):
        return f"{self.situation} → {self.rights_topic}"


class ActionStep(models.Model):
    rights_topic = models.ForeignKey(
        RightsTopic,
        on_delete=models.CASCADE,
        related_name="action_steps",
    )

    order = models.PositiveIntegerField(default=1)

    title = models.CharField(max_length=200)

    description = models.TextField()

    is_safety_critical = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.rights_topic} — {self.title}"


class SafetyResponse(models.Model):
    """
    Predefined reviewed responses for sensitive/high-risk situations.

    Safety-critical responses should not depend on an LLM generating
    advice dynamically.
    """

    rights_topic = models.ForeignKey(
        RightsTopic,
        on_delete=models.CASCADE,
        related_name="safety_responses",
    )

    trigger_key = models.CharField(
        max_length=100,
    )

    message = models.TextField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["rights_topic", "trigger_key"],
                name="unique_rights_topic_safety_trigger",
            )
        ]

    def __str__(self):
        return f"{self.rights_topic} — {self.trigger_key}"


class LegalProvision(models.Model):
    """
    Stores a specific legal authority supporting a RightsTopic.

    Legal provisions keep the authoritative legal reference separate
    from the citizen-facing plain-language explanation. This allows
    Sauti Yo to explain a right simply while preserving exactly where
    that information came from.
    """

    SOURCE_TYPE_CHOICES = [
        ("constitution", "Constitution"),
        ("act", "Act of Parliament"),
        ("regulation", "Regulation"),
        ("statutory_instrument", "Statutory Instrument"),
        ("case_law", "Case Law"),
        ("international", "International / Regional Instrument"),
        ("other", "Other"),
    ]

    VERIFICATION_STATUS_CHOICES = [
        ("verified", "Verified"),
        ("review_required", "Review Required"),
        ("expired", "Expired"),
        ("archived", "Archived"),
    ]

    rights_topic = models.ForeignKey(
        RightsTopic,
        on_delete=models.CASCADE,
        related_name="legal_provisions",
    )

    source_type = models.CharField(
        max_length=30,
        choices=SOURCE_TYPE_CHOICES,
        default="act",
    )

    law_title = models.CharField(
        max_length=255,
    )

    provision_reference = models.CharField(
        max_length=150,
        help_text=(
            "Specific legal reference, for example "
            "'Article 21', 'Section 7(1)' or 'Regulation 4'."
        ),
    )

    provision_heading = models.CharField(
        max_length=255,
        blank=True,
    )

    provision_text = models.TextField(
        blank=True,
        help_text=(
            "Reviewed extract or summary of the relevant legal provision. "
            "Do not store unverified AI-generated legal text here."
        ),
    )

    plain_language_explanation = models.TextField(
        help_text=(
            "Citizen-facing explanation of the provision in clear, "
            "simple language."
        ),
    )

    source_url = models.URLField(
        blank=True,
    )

    jurisdiction = models.CharField(
        max_length=100,
        default="Uganda",
    )

    reviewed_by = models.CharField(
        max_length=255,
        blank=True,
    )

    last_reviewed = models.DateField(
        null=True,
        blank=True,
    )

    next_review_due = models.DateField(
        null=True,
        blank=True,
    )

    verification_status = models.CharField(
        max_length=30,
        choices=VERIFICATION_STATUS_CHOICES,
        default="review_required",
    )

    order = models.PositiveIntegerField(
        default=1,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "order",
            "id",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "rights_topic",
                    "law_title",
                    "provision_reference",
                ],
                name="unique_legal_provision_per_topic",
            )
        ]

    def __str__(self):
        return (
            f"{self.law_title} — "
            f"{self.provision_reference}"
        )
