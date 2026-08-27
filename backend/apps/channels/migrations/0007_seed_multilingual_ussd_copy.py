from django.db import migrations


COPY = {
    "lg": {
        "ussd.welcome": "Tukwaniriza ku Sauti Yo",
        "ussd.main_menu": (
            "1. Noonya eddembe lyange\n"
            "2. Funa obuyambi kati\n"
            "0. Fuluma"
        ),
        "ussd.invalid_choice": "Ky'olonze tekikkirizibwa.",
        "ussd.too_many_invalid": (
            "Olondese ebitali bituufu emirundi mingi. "
            "Ddayo okubeera ku Sauti Yo."
        ),
        "ussd.goodbye": "Webale okukozesa Sauti Yo.",
        "ussd.not_found": (
            "Tusonyiwe, amawulire ago tegakyaliwo."
        ),
        "ussd.no_situations": (
            "Tewali mbeera ziriwo kati."
        ),
        "ussd.choose_situation": "Londa embeera:",
        "ussd.related_rights": "Eddembe erikwatagana:",
        "ussd.topic_menu": (
            "1. Emitendera gy'okukola\n"
            "2. Enkola z'obuyambi\n"
            "0. Ddayo"
        ),
        "ussd.safety_continue": (
            "1. Weyongereyo\n"
            "0. Ddayo"
        ),
        "ussd.continue": (
            "1. Weyongereyo\n"
            "0. Ddayo"
        ),
        "ussd.no_action_steps": (
            "Tewali mitendera gitegekeddwa ku nsonga eno."
        ),
        "ussd.no_support_contacts": (
            "Tewali nkola z'obuyambi ziriwo."
        ),
        "ussd.no_emergency_contacts": (
            "Tewali nkola z'obuyambi obw'amangu ziriwo kati."
        ),
        "ussd.more": "Ebisingawo",
        "ussd.back": "Ddayo",
        "ussd.next": "Ekiddako",
        "ussd.unreviewed_notice": (
            "Weetegereze: bino tebinnakeberwa."
        ),
    },

    "sw": {
        "ussd.welcome": "Karibu Sauti Yo",
        "ussd.main_menu": (
            "1. Tafuta haki zangu\n"
            "2. Pata msaada sasa\n"
            "0. Toka"
        ),
        "ussd.invalid_choice": "Chaguo si sahihi.",
        "ussd.too_many_invalid": (
            "Umeweka chaguo lisilo sahihi mara nyingi. "
            "Tafadhali piga tena."
        ),
        "ussd.goodbye": "Asante kwa kutumia Sauti Yo.",
        "ussd.not_found": (
            "Samahani, taarifa hiyo haipatikani tena."
        ),
        "ussd.no_situations": (
            "Hakuna hali zinazopatikana sasa."
        ),
        "ussd.choose_situation": "Chagua hali:",
        "ussd.related_rights": "Haki zinazohusiana:",
        "ussd.topic_menu": (
            "1. Hatua za kuchukua\n"
            "2. Mawasiliano ya msaada\n"
            "0. Rudi"
        ),
        "ussd.safety_continue": (
            "1. Endelea\n"
            "0. Rudi"
        ),
        "ussd.continue": (
            "1. Endelea\n"
            "0. Rudi"
        ),
        "ussd.no_action_steps": (
            "Hakuna hatua maalum zinazopatikana kwa mada hii."
        ),
        "ussd.no_support_contacts": (
            "Hakuna mawasiliano ya msaada yanayopatikana."
        ),
        "ussd.no_emergency_contacts": (
            "Hakuna mawasiliano ya dharura yanayopatikana sasa."
        ),
        "ussd.more": "Zaidi",
        "ussd.back": "Rudi",
        "ussd.next": "Ifuatayo",
        "ussd.unreviewed_notice": (
            "Kumbuka: taarifa hii bado haijakaguliwa."
        ),
    },

    "nyn": {
        "ussd.welcome": "Tukwanirize aha Sauti Yo",
        "ussd.main_menu": (
            "1. Ronda obugabe bwangye\n"
            "2. Shanga obuhwezi hati\n"
            "0. Rugamu"
        ),
        "ussd.invalid_choice": "Eki otooraine tikihikire.",
        "ussd.too_many_invalid": (
            "Otooraine ebitarikuhika emirundi mingi. "
            "Garuka ohamagare."
        ),
        "ussd.goodbye": "Webare kukoresa Sauti Yo.",
        "ussd.not_found": (
            "Nitukushaba otusaasire, amakuru ago tigariho hati."
        ),
        "ussd.no_situations": (
            "Tihariho mbeera eziriho hati."
        ),
        "ussd.choose_situation": "Toorana embeera:",
        "ussd.related_rights": "Obugabe oburikukwataho:",
        "ussd.topic_menu": (
            "1. Emitendera y'okukora\n"
            "2. Ahu orikubaasa kushanga obuhwezi\n"
            "0. Garuka"
        ),
        "ussd.safety_continue": (
            "1. Gumizamu\n"
            "0. Garuka"
        ),
        "ussd.continue": (
            "1. Gumizamu\n"
            "0. Garuka"
        ),
        "ussd.no_action_steps": (
            "Tihariho mitendera eteekateekirwe ahabw'ensonga egi."
        ),
        "ussd.no_support_contacts": (
            "Tihariho mikutu y'obuhwezi eriho."
        ),
        "ussd.no_emergency_contacts": (
            "Tihariho mikutu y'obuhwezi bw'amangu eriho hati."
        ),
        "ussd.more": "Ebindi",
        "ussd.back": "Garuka",
        "ussd.next": "Ekikurataho",
        "ussd.unreviewed_notice": (
            "Manya: amakuru aga tigakashwijumwe."
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
                channel="ussd",
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

    for language, entries in COPY.items():
        for content_key, text in entries.items():
            ChannelContent.objects.filter(
                content_key=content_key,
                language=language,
                channel="ussd",
                text=text,
                is_verified=False,
                reviewed_by="",
                last_reviewed=None,
                is_active=True,
            ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("channels", "0006_alter_smscontext_id"),
        ("content", "0002_alter_channelcontent_unique_together_and_more"),
    ]

    operations = [
        migrations.RunPython(
            seed_copy,
            migrations.RunPython.noop,
        ),
    ]
