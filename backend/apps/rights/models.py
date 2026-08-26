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
    VERIFICATION_STATUS_CHOICES = [
        ("verified", "Verified"),
        ("review_required", "Review Required"),
        ("expired", "Expired"),
        ("archived", "Archived"),
    ]

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=150)

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

class IssueOutcome(models.Model):
    category_slug = models.SlugField()

    issue_slug = models.SlugField()

    heading = models.CharField(
        max_length=255,
    )

    introduction = models.TextField()

    situation = models.ForeignKey(
        Situation,
        on_delete=models.PROTECT,
        related_name="issue_outcomes",
        null=True,
        blank=True,
    )

    rights_topics = models.ManyToManyField(
        RightsTopic,
        related_name="issue_outcomes",
        blank=True,
    )

    evidence_items = models.JSONField(
        default=list,
        blank=True,
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
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "category_slug",
                    "issue_slug",
                ],
                name="unique_issue_outcome",
            )
        ]

    def __str__(self):
        return (
            f"{self.category_slug} → "
            f"{self.issue_slug}"
        )

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