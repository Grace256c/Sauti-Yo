from django.db import models


class SupportService(models.Model):
    VERIFICATION_STATUS_CHOICES = [
        ("verified", "Verified"),
        ("review_required", "Review Required"),
        ("expired", "Expired"),
        ("archived", "Archived"),
    ]

    name = models.CharField(max_length=255)

    service_type = models.CharField(
        max_length=150,
    )

    description = models.TextField(
        blank=True,
    )

    phone_number = models.CharField(
        max_length=50,
        blank=True,
    )

    alternate_phone_number = models.CharField(
        max_length=50,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    website = models.URLField(
        blank=True,
    )

    availability = models.CharField(
        max_length=150,
        blank=True,
    )

    coverage = models.CharField(
        max_length=255,
        blank=True,
    )

    verification_status = models.CharField(
        max_length=30,
        choices=VERIFICATION_STATUS_CHOICES,
        default="review_required",
    )

    last_verified = models.DateField(
        null=True,
        blank=True,
    )

    next_verification_due = models.DateField(
        null=True,
        blank=True,
    )

    is_emergency_service = models.BooleanField(
        default=False,
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

    def __str__(self):
        return self.name