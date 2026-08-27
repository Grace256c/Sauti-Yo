from django.db import migrations


UPDATED_BACK_COPY = {
    "lg": {
        "ussd.topic_menu": (
            "1. Emitendera gy'okukola\n"
            "2. Enkola z'obuyambi\n"
            "9. Ddayo"
        ),
        "ussd.safety_continue": "1. Weyongereyo\n9. Ddayo",
        "ussd.continue": "1. Weyongereyo\n9. Ddayo",
    },
    "sw": {
        "ussd.topic_menu": (
            "1. Hatua za kuchukua\n"
            "2. Mawasiliano ya msaada\n"
            "9. Rudi"
        ),
        "ussd.safety_continue": "1. Endelea\n9. Rudi",
        "ussd.continue": "1. Endelea\n9. Rudi",
    },
    "nyn": {
        "ussd.topic_menu": (
            "1. Emitendera y'okukora\n"
            "2. Ahu orikubaasa kushanga obuhwezi\n"
            "9. Garuka"
        ),
        "ussd.safety_continue": "1. Gumizamu\n9. Garuka",
        "ussd.continue": "1. Gumizamu\n9. Garuka",
    },
}

PREVIOUS_BACK_COPY = {
    "lg": {
        "ussd.topic_menu": (
            "1. Emitendera gy'okukola\n"
            "2. Enkola z'obuyambi\n"
            "0. Ddayo"
        ),
        "ussd.safety_continue": "1. Weyongereyo\n0. Ddayo",
        "ussd.continue": "1. Weyongereyo\n0. Ddayo",
    },
    "sw": {
        "ussd.topic_menu": (
            "1. Hatua za kuchukua\n"
            "2. Mawasiliano ya msaada\n"
            "0. Rudi"
        ),
        "ussd.safety_continue": "1. Endelea\n0. Rudi",
        "ussd.continue": "1. Endelea\n0. Rudi",
    },
    "nyn": {
        "ussd.topic_menu": (
            "1. Emitendera y'okukora\n"
            "2. Ahu orikubaasa kushanga obuhwezi\n"
            "0. Garuka"
        ),
        "ussd.safety_continue": "1. Gumizamu\n0. Garuka",
        "ussd.continue": "1. Gumizamu\n0. Garuka",
    },
}

NEW_EXIT_COPY = {
    "lg": "Fuluma",
    "sw": "Toka",
    "nyn": "Rugamu",
}


def update_back_digit_and_add_exit(apps, schema_editor):
    ChannelContent = apps.get_model("content", "ChannelContent")

    for language, entries in UPDATED_BACK_COPY.items():
        for content_key, text in entries.items():
            ChannelContent.objects.filter(
                content_key=content_key,
                language=language,
                channel="ussd",
            ).update(text=text)

    for language, exit_label in NEW_EXIT_COPY.items():
        ChannelContent.objects.get_or_create(
            content_key="ussd.exit",
            language=language,
            channel="ussd",
            defaults={
                "text": exit_label,
                "is_verified": False,
                "reviewed_by": "",
                "last_reviewed": None,
                "is_active": True,
            },
        )


def revert_back_digit_and_remove_exit(apps, schema_editor):
    ChannelContent = apps.get_model("content", "ChannelContent")

    for language, entries in PREVIOUS_BACK_COPY.items():
        for content_key, text in entries.items():
            ChannelContent.objects.filter(
                content_key=content_key,
                language=language,
                channel="ussd",
            ).update(text=text)

    for language in NEW_EXIT_COPY:
        ChannelContent.objects.filter(
            content_key="ussd.exit",
            language=language,
            channel="ussd",
        ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("channels", "0012_smscontext_pending_referral_step"),
        ("content", "0002_alter_channelcontent_unique_together_and_more"),
    ]

    operations = [
        migrations.RunPython(
            update_back_digit_and_add_exit,
            revert_back_digit_and_remove_exit,
        ),
    ]
