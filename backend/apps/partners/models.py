from django.conf import settings
from django.db import models

from apps.support.models import SupportService


class PartnerOrganisation(models.Model):
    """
    Represents an organisation participating in the Sauti Yo
    partner network.

    The public-facing service entry remains SupportService.
    This model stores partner-specific operational and
    administrative information.
    """

    ORGANISATION_TYPE_CHOICES = [
        ("legal_aid", "Legal Aid Organisation"),
        ("ngo", "Non-Governmental Organisation"),
        ("cbo", "Community-Based Organisation"),
        ("government", "Government Institution"),
        ("law_firm", "Law Firm"),
        ("protection_service", "Protection / Safeguarding Service"),
        ("mediation_service", "Mediation / Dispute Resolution Service"),
        ("other", "Other"),
    ]

    support_service = models.OneToOneField(
        SupportService,
        on_delete=models.CASCADE,
        related_name="partner_organisation",
    )

    organisation_type = models.CharField(
        max_length=50,
        choices=ORGANISATION_TYPE_CHOICES,
        blank=True,
    )

    registration_number = models.CharField(
        max_length=150,
        blank=True,
    )

    year_established = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    headquarters_district = models.CharField(
        max_length=100,
        blank=True,
    )

    physical_address = models.TextField(
        blank=True,
    )

    public_email = models.EmailField(
        blank=True,
    )

    public_phone = models.CharField(
        max_length=50,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    is_test = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.support_service.name


class PartnerMember(models.Model):
    """
    Connects authenticated Django users to partner organisations.
    """

    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Administrator"),
        ("case_worker", "Case Worker"),
        ("viewer", "Viewer"),
    ]

    organisation = models.ForeignKey(
        PartnerOrganisation,
        on_delete=models.CASCADE,
        related_name="members",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="partner_memberships",
    )

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default="viewer",
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
                fields=["organisation", "user"],
                name="unique_partner_member_per_organisation",
            )
        ]

    def __str__(self):
        return f"{self.user} — {self.organisation}"


class PartnerServiceConfiguration(models.Model):
    """
    Stores the operational referral-matching configuration
    for a partner organisation.
    """

    SUPPORT_CHANNEL_CHOICES = [
        ("in_person", "In Person"),
        ("phone", "Phone"),
        ("remote", "Online / Remote"),
    ]

    organisation = models.OneToOneField(
        PartnerOrganisation,
        on_delete=models.CASCADE,
        related_name="service_configuration",
    )

    service_description = models.TextField(
        blank=True,
    )

    rights_categories = models.JSONField(
        default=list,
        blank=True,
    )

    support_types = models.JSONField(
        default=list,
        blank=True,
    )

    languages = models.JSONField(
        default=list,
        blank=True,
    )

    support_channels = models.JSONField(
        default=list,
        blank=True,
    )

    districts_served = models.JSONField(
        default=list,
        blank=True,
    )

    nationwide = models.BooleanField(
        default=False,
    )

    free_services = models.BooleanField(
        default=False,
    )

    appointment_required = models.BooleanField(
        default=False,
    )

    accepting_referrals = models.BooleanField(
        default=False,
    )

    weekly_referral_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    availability_note = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"Service configuration — {self.organisation}"


class PartnerVerificationRequest(models.Model):
    """
    Represents one submitted verification request.

    Verification is deliberately separate from SupportService's
    current verification_status so that we preserve review history.
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("under_review", "Under Review"),
        ("changes_requested", "Changes Requested"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
        ("withdrawn", "Withdrawn"),
    ]

    organisation = models.ForeignKey(
        PartnerOrganisation,
        on_delete=models.CASCADE,
        related_name="verification_requests",
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="draft",
    )

    declaration_accurate = models.BooleanField(
        default=False,
    )

    declaration_authorised = models.BooleanField(
        default=False,
    )

    declaration_consent = models.BooleanField(
        default=False,
    )

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_partner_verifications",
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_partner_verifications",
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    review_notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.organisation} — {self.status}"


class PartnerVerificationDocument(models.Model):
    """
    Stores metadata for documents attached to a verification request.

    The actual file storage mechanism can be configured later.
    """

    DOCUMENT_TYPE_CHOICES = [
        ("registration", "Registration Evidence"),
        ("organisation_identification", "Organisation Identification"),
        ("service_evidence", "Service Evidence"),
        ("authorised_representative", "Authorised Representative Evidence"),
        ("other", "Other"),
    ]

    verification_request = models.ForeignKey(
        PartnerVerificationRequest,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPE_CHOICES,
    )

    title = models.CharField(
        max_length=255,
    )

    file = models.FileField(
        upload_to="partner_verification/",
        blank=True,
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_partner_verification_documents",
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return f"{self.verification_request} — {self.title}"


class PartnerPreferences(models.Model):
    """
    Partner workspace preferences that are not part of the
    organisation profile or service configuration.
    """

    organisation = models.OneToOneField(
        PartnerOrganisation,
        on_delete=models.CASCADE,
        related_name="preferences",
    )

    email_notifications = models.BooleanField(
        default=True,
    )

    sms_notifications = models.BooleanField(
        default=False,
    )

    referral_notifications = models.BooleanField(
        default=True,
    )

    verification_notifications = models.BooleanField(
        default=True,
    )

    product_updates = models.BooleanField(
        default=False,
    )

    show_public_phone = models.BooleanField(
        default=False,
    )

    show_public_email = models.BooleanField(
        default=False,
    )

    allow_remote_referrals = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"Preferences — {self.organisation}"