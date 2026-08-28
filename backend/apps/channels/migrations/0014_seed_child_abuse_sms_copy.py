from django.db import migrations


COPY = {
    "lg": {
        "child_abuse_intro": (
            "Sauti Yo: Funa amawulire ku bukuumi bw'omwana "
            "n'obuyambi bw'oyinza okufuna ku nsonga "
            "z'okuyisibwa obubi kw'abaana."
        ),
    },
    "sw": {
        "child_abuse_intro": (
            "Sauti Yo: Pata taarifa kuhusu usalama wa mtoto na "
            "msaada unaoweza kupata kuhusu unyanyasaji wa "
            "watoto."
        ),
    },
    "nyn": {
        "child_abuse_intro": (
            "Sauti Yo: Shanga amakuru aha buteka bw'omwana "
            "n'obuhwezi oburikubaasa kubaho aha kutwarwa kubi "
            "kw'abaana."
        ),
    },
}


def seed_copy(apps, schema_editor):
    ChannelContent = apps.get_model(
        "content",
        "ChannelContent",
    )

    for language, entries in COPY.items():
        for content_key, text in entries.items():
            ChannelContent.objects.get_or_create(
                content_key=content_key,
                language=language,
                channel="sms",
                defaults={
                    "text": text,
                    "is_verified": False,
                    "reviewed_by": "",
                    "last_reviewed": None,
                    "is_active": True,
                },
            )


def remove_copy(apps, schema_editor):
    ChannelContent = apps.get_model(
        "content",
        "ChannelContent",
    )

    ChannelContent.objects.filter(
        language__in=["lg", "sw", "nyn"],
        channel="sms",
        content_key__in={
            key
            for entries in COPY.values()
            for key in entries
        },
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("channels", "0013_update_ussd_back_and_exit_copy"),
        ("content", "0002_alter_channelcontent_unique_together_and_more"),
    ]

    operations = [
        migrations.RunPython(
            seed_copy,
            migrations.RunPython.noop,
        ),
    ]
