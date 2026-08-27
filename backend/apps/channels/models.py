from django.db import models


class UssdSession(models.Model):
    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("lg", "Luganda"),
        ("sw", "Kiswahili"),
        ("nyn", "Runyankole"),
    ]

    session_id = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=50)

    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        blank=True,
    )

    state = models.CharField(max_length=50, default="language_select")

    context = models.JSONField(default=dict, blank=True)

    last_text = models.TextField(blank=True, default="")

    last_response = models.TextField(blank=True, default="")

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.session_id} ({self.state})"


class SmsContext(models.Model):
    id = models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")

    phone_number = models.CharField(max_length=50, unique=True)
    last_situation_slug = models.SlugField()
    discreet = models.BooleanField(default=False)
    pending_safety_check = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.phone_number} -> {self.last_situation_slug}"


class VoiceSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=50)

    state = models.CharField(max_length=50, default="awaiting_recording")

    context = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.session_id} ({self.state})"
