from django.db import migrations


COPY = {
    "lg": {
        "problem_at_work_intro": (
            "Sauti Yo: Tegeera ensonga yo ku mulimu, "
            "amanya eddembe eriyinza okukukwatako, era omanye "
            "emitendera gy'oyinza okuddako."
        ),
        "facing_eviction_intro": (
            "Sauti Yo: Tegeera eddembe lyo ku nsonga z'okugobebwa "
            "mu nnyumba oba ku ttaka, n'emitendera gy'oyinza okuddako."
        ),
        "domestic_violence_intro": (
            "Sauti Yo: Funa amawulire ku bukuumi n'obuyambi "
            "bw'oyinza okufuna ku nsonga z'obutabanguko awaka."
        ),
        "sexual_harassment_intro": (
            "Sauti Yo: Tegeera eddembe lyo n'engeri y'okunoonya "
            "obuyambi ku nsonga z'okutulugunyizibwa mu by'obusambattuko."
        ),
    },
    "sw": {
        "problem_at_work_intro": (
            "Sauti Yo: Elewa tatizo lako kazini, haki zinazoweza "
            "kuhusika, na hatua unazoweza kuchukua."
        ),
        "facing_eviction_intro": (
            "Sauti Yo: Elewa haki zako kuhusu kufukuzwa kwenye "
            "nyumba au ardhi na hatua unazoweza kuchukua."
        ),
        "domestic_violence_intro": (
            "Sauti Yo: Pata taarifa kuhusu usalama, haki na msaada "
            "unaoweza kupata kuhusu ukatili wa nyumbani."
        ),
        "sexual_harassment_intro": (
            "Sauti Yo: Elewa haki zako na namna ya kutafuta msaada "
            "kuhusu unyanyasaji wa kingono."
        ),
    },
    "nyn": {
        "problem_at_work_intro": (
            "Sauti Yo: Yetegyereze ekizibu kyawe aha murimo, "
            "obugabe oburikubaasa kukukwataho, n'emitendera "
            "ei orikubaasa kukuratira."
        ),
        "facing_eviction_intro": (
            "Sauti Yo: Yetegyereze obugabe bwawe aha kugobibwa "
            "omu nju nari aha itaka, n'emitendera ei orikubaasa kukuratira."
        ),
        "domestic_violence_intro": (
            "Sauti Yo: Shanga amakuru aha buteka n'obuhwezi "
            "oburikubaasa kubaho aha kutabanguka omuka."
        ),
        "sexual_harassment_intro": (
            "Sauti Yo: Yetegyereze obugabe bwawe n'oku orikubaasa "
            "kushaba obuhwezi aha kutwarwa kubi omu by'obushambani."
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
            ChannelContent.objects.update_or_create(
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
        ("channels", "0008_smscontext_language_and_more"),
        ("content", "0002_alter_channelcontent_unique_together_and_more"),
    ]

    operations = [
        migrations.RunPython(
            seed_copy,
            remove_copy,
        ),
    ]
