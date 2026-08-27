# from django.db import models

# Create your models here.
from django.db import models


class LegalDocument(models.Model):
    """
    An authoritative legal source used by the Sauti Yo legal assistant.

    Examples:
    - Constitution of the Republic of Uganda
    - Employment Act
    - Land Act
    - Domestic Violence Act
    """

    DOCUMENT_TYPE_CHOICES = [
        ("constitution", "Constitution"),
        ("act", "Act"),
        ("regulation", "Regulation"),
        ("rule", "Rule"),
        ("other", "Other"),
    ]

    title = models.CharField(
        max_length=255,
    )

    short_title = models.CharField(
        max_length=150,
        blank=True,
    )

    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPE_CHOICES,
        default="act",
    )

    jurisdiction = models.CharField(
        max_length=100,
        default="Uganda",
    )

    source_name = models.CharField(
        max_length=255,
        blank=True,
    )

    source_url = models.URLField(
        blank=True,
    )

    effective_date = models.DateField(
        null=True,
        blank=True,
    )

    version_date = models.DateField(
        null=True,
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

    def __str__(self):
        return self.title


class LegalSection(models.Model):
    """
    A searchable section, article, clause, or provision belonging
    to a LegalDocument.
    """

    document = models.ForeignKey(
        LegalDocument,
        on_delete=models.CASCADE,
        related_name="sections",
    )

    section_type = models.CharField(
        max_length=50,
        default="section",
    )

    section_number = models.CharField(
        max_length=50,
        blank=True,
    )

    heading = models.CharField(
        max_length=255,
        blank=True,
    )

    text = models.TextField()

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
            "document",
            "order",
            "id",
        ]

    def __str__(self):
        reference = (
            self.section_number
            or str(self.id)
        )

        return (
            f"{self.document.short_title or self.document.title} "
            f"- {reference}"
        )