from django.db import models


class ChannelContent(models.Model):
    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("lg", "Luganda"),
        ("sw", "Kiswahili"),
        ("nyn", "Runyankole"),
    ]

    CHANNEL_CHOICES = [
        ("web", "Web"),
        ("ussd", "USSD"),
        ("sms", "SMS"),
        ("voice", "Voice"),
    ]

    content_key = models.CharField(
        max_length=200,
    )

    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
    )

    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
    )

    text = models.TextField()

    is_verified = models.BooleanField(
        default=False,
    )

    reviewed_by = models.CharField(
        max_length=255,
        blank=True,
    )

    last_reviewed = models.DateField(
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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "content_key",
                    "language",
                    "channel",
                ],
                name="unique_channel_content",
            )
        ]

        indexes = [
            models.Index(
                fields=[
                    "content_key",
                    "language",
                    "channel",
                ]
            ),
        ]

    def __str__(self):
        return (
            f"{self.content_key} | "
            f"{self.language} | "
            f"{self.channel}"
        )