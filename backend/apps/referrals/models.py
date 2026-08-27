from django.conf import settings
from django.db import models

from apps.partners.models import PartnerOrganisation
from apps.rights.models import RightsTopic


class Referral(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("reviewing", "Reviewing"),
        ("accepted", "Accepted"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("declined", "Declined"),
        ("cancelled", "Cancelled"),
        ("closed", "Closed"),
    ]

    SUPPORT_CHANNEL_CHOICES = [
        ("in_person", "In Person"),
        ("phone", "Phone"),
        ("remote", "Online / Remote"),
    ]

    reference = models.CharField(
        max_length=50,
        unique=True,
    )

    organisation = models.ForeignKey(
        PartnerOrganisation,
        on_delete=models.PROTECT,
        related_name="referrals",
    )

    rights_topic = models.ForeignKey(
        RightsTopic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referrals",
    )

    summary = models.TextField(
        blank=True,
    )

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

    preferred_support_channel = models.CharField(
        max_length=30,
        choices=SUPPORT_CHANNEL_CHOICES,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="new",
    )

    citizen_consent_to_share = models.BooleanField(
        default=False,
    )

    shared_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_partner_referrals",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["organisation", "status"],
            ),
            models.Index(
                fields=["reference"],
            ),
        ]

    def __str__(self):
        return f"{self.reference} — {self.organisation}"


class ReferralStatusHistory(models.Model):
    referral = models.ForeignKey(
        Referral,
        on_delete=models.CASCADE,
        related_name="status_history",
    )

    from_status = models.CharField(
        max_length=30,
        blank=True,
    )

    to_status = models.CharField(
        max_length=30,
        choices=Referral.STATUS_CHOICES,
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="partner_referral_status_changes",
    )

    note = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return (
            f"{self.referral.reference}: "
            f"{self.from_status or 'start'} → {self.to_status}"
        )