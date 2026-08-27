from apps.rights.services import get_channel_text, get_safety_message
from apps.support.models import SupportService

SMS_SEGMENT_BUDGET = 160

SUPPORTED_SMS_LANGUAGES = ("en", "lg", "sw", "nyn")

LANGUAGE_NAMES = {
    "en": "English",
    "lg": "Luganda",
    "sw": "Kiswahili",
    "nyn": "Runyankole",
}

LANGUAGE_MENU = (
    "Choose language / Londa olulimi / Chagua lugha / "
    "Ronda orurimi:\n"
    "LANG EN - English\n"
    "LANG LG - Luganda\n"
    "LANG SW - Kiswahili\n"
    "LANG NYN - Runyankole"
)

LANGUAGE_SELECTED_REPLIES = {
    "en": (
        "Language set to English. Text HELP for support, "
        "or describe your concern."
    ),
    "lg": (
        "Olulimi lutekeddwa ku Luganda. Wandiika HELP "
        "okufuna obuyambi, oba nnyonnyola ekikweraliikiriza."
    ),
    "sw": (
        "Lugha imewekwa kuwa Kiswahili. Tuma HELP kupata "
        "msaada, au eleza tatizo lako."
    ),
    "nyn": (
        "Orurimi rutairweho Runyankole. Handika HELP "
        "kushaba obuhwezi, nari shoboorora ekikweraliikiriza."
    ),
}

UNMATCHED_REPLIES = {
    "en": (
        "You can text HOME, WORK, LAND or CHILD for help, "
        "or HELP for support."
    ),
    "lg": (
        "Wandiika HOME, WORK, LAND oba CHILD okumanya "
        "obuyambi, oba HELP okufuna obuyambi."
    ),
    "sw": (
        "Tuma HOME, WORK, LAND au CHILD kupata maelezo, "
        "au HELP kupata msaada."
    ),
    "nyn": (
        "Handika HOME, WORK, LAND nari CHILD kumanya "
        "obuhwezi, nari HELP kushaba obuhwezi."
    ),
}

FOLLOWUP_EXPIRED_REPLIES = {
    "en": (
        "Please first text HOME, WORK, LAND or CHILD to tell "
        "us what's going on, then text STEPS or SUPPORT."
    ),
    "lg": (
        "Sooka owandiike HOME, WORK, LAND oba CHILD "
        "otutegeeze ekigenda mu maaso, oluvannyuma "
        "owandiike STEPS oba SUPPORT."
    ),
    "sw": (
        "Kwanza tuma HOME, WORK, LAND au CHILD kutueleza "
        "kinachoendelea, kisha tuma STEPS au SUPPORT."
    ),
    "nyn": (
        "Banza ohandike HOME, WORK, LAND nari CHILD "
        "otugambire ekirikubaho, bwanyima ohandike "
        "STEPS nari SUPPORT."
    ),
}

SAFETY_CHECKIN_QUESTIONS = {
    "en": "Are you safe? Reply YES or NO.",
    "lg": "Oli mu bukuumi? Ddamu YES oba NO.",
    "sw": "Uko salama? Jibu YES au NO.",
    "nyn": "Ori omu buteka? Garukamu YES nari NO.",
}

DISCREET_SAFETY_CHECKIN_QUESTIONS = {
    "en": "Reply YES or NO to continue.",
    "lg": "Ddamu YES oba NO okweyongerayo.",
    "sw": "Jibu YES au NO kuendelea.",
    "nyn": "Garukamu YES nari NO kugumizamu.",
}


def _sms_language(language):
    if language in SUPPORTED_SMS_LANGUAGES:
        return language
    return "en"


def build_language_menu():
    return LANGUAGE_MENU


def build_language_selected_reply(language):
    language = _sms_language(language)
    return LANGUAGE_SELECTED_REPLIES[language]


def build_safety_checkin_question(
    language="en",
    discreet=False,
):
    language = _sms_language(language)

    replies = (
        DISCREET_SAFETY_CHECKIN_QUESTIONS
        if discreet
        else SAFETY_CHECKIN_QUESTIONS
    )

    return replies[language]


UNMATCHED_REPLY = (
    "You can text HOME, WORK, LAND or CHILD for help, or HELP for support."
)
FOLLOWUP_EXPIRED_REPLY = (
    "Please first text HOME, WORK, LAND or CHILD to tell us what's going "
    "on, then text STEPS or SUPPORT."
)
GENERAL_SAFETY_REPLY = (
    "If you are in immediate danger, call the Police on 999 or 112 now. "
    "Free support: Sauti 116."
)
NO_SUPPORT_SERVICES_REPLY = (
    "No support contacts are available right now. In an emergency, call "
    "the Police on 999 or 112."
)
NO_ACTION_STEPS_REPLY = (
    "No specific steps are available for this yet. Text SUPPORT for help "
    "contacts."
)
DISCREET_INTRO = "Here is some information about your recent inquiry:"
DISCREET_STEPS_REPLY = (
    "Steps were included in an earlier message. Text SUPPORT for help "
    "contacts."
)
SAFETY_CHECKIN_QUESTION = "Are you safe? Reply YES or NO."
DISCREET_SAFETY_CHECKIN_QUESTION = "Reply YES or NO to continue."


def _situation_intro(detail, mode="normal", language="en"):
    if mode == "discreet":
        return DISCREET_INTRO
    language = _sms_language(language)
    text = get_channel_text(detail["slug"], "sms", language)
    if text:
        return text
    return detail["description"] or detail["title"]



SMS_ACTION_STEP_TRANSLATIONS = {
    "lg": {
        "Identify the workplace issue and keep a clear record of important details.":
            "Tegeera ensonga eri ku mulimu era okuume obubaka obukulu obugikwatako.",
        "Review information that may apply to your situation.":
            "Kebera amawulire agakwata ku ddembe eriyinza okukola ku mbeera yo.",
        "Where safe, keep relevant documents, dates, messages, or other records.":
            "Bwe kiba nga tekikuteeka mu kabi, kuuma ebiwandiiko, ennaku, obubaka n'obujulizi obulala obukwatako.",
        "Consider an appropriate next action or connect with a support service.":
            "Lowooza ku mutendera oguddako ogusaanira oba funa obuyambi okuva mu kitongole ekiwa obuyambi.",

        "If you're in danger right now, prioritise getting somewhere safe over anything else on this list.":
            "Bw'oba oli mu kabi kati, sooka otuuke mu kifo ekirimu obukuumi.",
        "You can report at any police station, or call the GBV helpline on 0800 199 195.":
            "Osobola okuloopa ku poliisi yonna oba okukuba essimu ku 0800 199 195.",
        "You or someone on your behalf can apply to a magistrate's court for a protection order - this can be done without your abuser present.":
            "Ggwe oba omuntu akukiikirira asobola okusaba kkooti ya magistrate ekiragiro ky'obukuumi.",
        "Organisations like MIFUMI and FIDA-Uganda offer confidential help, counselling, and further legal support.":
            "Ebitongole nga MIFUMI ne FIDA-Uganda biwa obuyambi obw'ekyama n'obuwagizi mu mateeka.",

        "By law you must be given written notice before eviction: at least 7 days for a weekly tenancy, 30 days for a monthly tenancy, or 60 days for a yearly tenancy. A shorter period in your tenancy agreement is not valid.":
            "Amateeka geetaaga landlord okukuwandiikira nga tannakugoba: waakiri ennaku 7 ku bupangisa bwa wiiki, 30 ku bwa mwezi, oba 60 ku bwa mwaka.",
        "For non-payment of rent, your landlord can only re-enter after your payment is more than 30 days overdue, and the eviction must happen with the Local Council and Police present.":
            "Ku bbanja ly'obupangisa, okugobebwa kulina okugoberera amateeka era LC ne Poliisi babeewo nga bwe kyetaagisa.",
        "Keep your tenancy agreement and proof of rent payments - these matter if you need to show an eviction was unlawful.":
            "Kuuma endagaano y'obupangisa n'obukakafu bw'ensimbi z'osasula.",
        "If your landlord evicts you without following the law, you can seek relief from court, including compensation. Free legal aid is available.":
            "Bw'ogobebwa nga amateeka tegagobereddwa, osobola okunoonya obuyambi mu kkooti era n'obuyambi bw'amateeka obw'obwereere.",

        "Note the date, what happened, and any witnesses, as soon as you safely can.":
            "Bwe kiba nga kya bukuumi, wandiika olunaku, ekyabaddewo n'abajulizi bonna.",
        "Workplaces with 25+ staff are legally required to have a sexual harassment policy and committee - you can report to them or your supervisor.":
            "Ekifo ky'omulimu ekirimu abakozi 25 oba okusingawo kirina okuba n'enkola n'akakiiko ku kutulugunyizibwa mu by'obusambattuko.",
        "If it's unresolved or you don't feel safe reporting internally, a Labour Officer must keep your report confidential.":
            "Bw'otafuna kuyambibwa oba nga toli bulungi kuloopa munda, osobola okutuukirira Labour Officer mu kyama.",
        "FIDA-Uganda and the Uganda Law Society Legal Aid Project both offer free, confidential support.":
            "FIDA-Uganda ne Uganda Law Society Legal Aid Project biwa obuyambi obw'obwereere era obw'ekyama.",
    },

    "sw": {
        "Identify the workplace issue and keep a clear record of important details.":
            "Tambua tatizo la kazini na uhifadhi kumbukumbu wazi za taarifa muhimu.",
        "Review information that may apply to your situation.":
            "Pitia taarifa kuhusu haki zinazoweza kuhusika na hali yako.",
        "Where safe, keep relevant documents, dates, messages, or other records.":
            "Ikiwa ni salama, hifadhi nyaraka, tarehe, ujumbe na kumbukumbu nyingine muhimu.",
        "Consider an appropriate next action or connect with a support service.":
            "Fikiria hatua inayofaa inayofuata au wasiliana na huduma ya msaada.",

        "If you're in danger right now, prioritise getting somewhere safe over anything else on this list.":
            "Ikiwa uko hatarini sasa, tanguliza kufika mahali salama.",
        "You can report at any police station, or call the GBV helpline on 0800 199 195.":
            "Unaweza kuripoti katika kituo chochote cha polisi au kupiga 0800 199 195.",
        "You or someone on your behalf can apply to a magistrate's court for a protection order - this can be done without your abuser present.":
            "Wewe au mwakilishi wako anaweza kuomba amri ya ulinzi katika mahakama ya hakimu.",
        "Organisations like MIFUMI and FIDA-Uganda offer confidential help, counselling, and further legal support.":
            "Mashirika kama MIFUMI na FIDA-Uganda hutoa msaada wa siri, ushauri na msaada wa kisheria.",

        "By law you must be given written notice before eviction: at least 7 days for a weekly tenancy, 30 days for a monthly tenancy, or 60 days for a yearly tenancy. A shorter period in your tenancy agreement is not valid.":
            "Sheria inahitaji upewe notisi ya maandishi kabla ya kufukuzwa: angalau siku 7 kwa upangaji wa wiki, 30 kwa mwezi, au 60 kwa mwaka.",
        "For non-payment of rent, your landlord can only re-enter after your payment is more than 30 days overdue, and the eviction must happen with the Local Council and Police present.":
            "Kwa kutolipa kodi, kufukuzwa lazima kufuate sheria na masharti yanayohitajika.",
        "Keep your tenancy agreement and proof of rent payments - these matter if you need to show an eviction was unlawful.":
            "Hifadhi mkataba wako wa upangaji na uthibitisho wa malipo ya kodi.",
        "If your landlord evicts you without following the law, you can seek relief from court, including compensation. Free legal aid is available.":
            "Ukifukuzwa bila kufuata sheria, unaweza kutafuta msaada mahakamani, pamoja na fidia inapofaa.",

        "Note the date, what happened, and any witnesses, as soon as you safely can.":
            "Ikiwa ni salama, andika tarehe, kilichotokea na mashahidi wowote.",
        "Workplaces with 25+ staff are legally required to have a sexual harassment policy and committee - you can report to them or your supervisor.":
            "Sehemu za kazi zenye wafanyakazi 25 au zaidi zinapaswa kuwa na sera na kamati ya unyanyasaji wa kingono.",
        "If it's unresolved or you don't feel safe reporting internally, a Labour Officer must keep your report confidential.":
            "Ikiwa tatizo halijatatuliwa au si salama kuripoti ndani, unaweza kuripoti kwa Afisa wa Kazi kwa siri.",
        "FIDA-Uganda and the Uganda Law Society Legal Aid Project both offer free, confidential support.":
            "FIDA-Uganda na Uganda Law Society Legal Aid Project hutoa msaada wa bure na wa siri.",
    },

    "nyn": {
        "Identify the workplace issue and keep a clear record of important details.":
            "Manya ekizibu aha murimo kandi obike gye amakuru makuru agarikukikwataho.",
        "Review information that may apply to your situation.":
            "Shoma amakuru aha bugabe oburikubaasa kukwata aha mbeera yawe.",
        "Where safe, keep relevant documents, dates, messages, or other records.":
            "Ku kiraabe kiri eky'obuteka, bika ebiwandiiko, ebiro, obutumwa n'obuhame obundi.",
        "Consider an appropriate next action or connect with a support service.":
            "Teekateeka omutendera ogurikukurataho nari shaba obuhwezi omu kitongore ekirikuhwera.",

        "If you're in danger right now, prioritise getting somewhere safe over anything else on this list.":
            "Ku oraabe ori omu kabi hati, banza oze omu mwanya ogw'obuteka.",
        "You can report at any police station, or call the GBV helpline on 0800 199 195.":
            "Noobaasa kurahura aha police station yoona nari oteere 0800 199 195.",
        "You or someone on your behalf can apply to a magistrate's court for a protection order - this can be done without your abuser present.":
            "Iwe nari orikukujwekyera noobaasa kushaba court ya magistrate ekiragiro ky'oburinzi.",
        "Organisations like MIFUMI and FIDA-Uganda offer confidential help, counselling, and further legal support.":
            "Ebitongore nka MIFUMI na FIDA-Uganda nibihayo obuhwezi bw'ekihama n'obuhwezi bw'amateeka.",

        "By law you must be given written notice before eviction: at least 7 days for a weekly tenancy, 30 days for a monthly tenancy, or 60 days for a yearly tenancy. A shorter period in your tenancy agreement is not valid.":
            "Amateeka nigenda ngu oheebwe notice ehandikirwe otakagobirwe: nibura ebiro 7 aha wiiki, 30 aha kwezi, nari 60 aha mwaka.",
        "For non-payment of rent, your landlord can only re-enter after your payment is more than 30 days overdue, and the eviction must happen with the Local Council and Police present.":
            "Aha kutashashura rent, okugobibwa kushemereire kukuratira amateeka n'emitendera erikwetengwa.",
        "Keep your tenancy agreement and proof of rent payments - these matter if you need to show an eviction was unlawful.":
            "Bika endagaano ya rent n'obuhame bw'okushashura kwawe.",
        "If your landlord evicts you without following the law, you can seek relief from court, including compensation. Free legal aid is available.":
            "Ku landlord yaakugoba atakuratire mateeka, noobaasa kushaba obuhwezi omu court.",

        "Note the date, what happened, and any witnesses, as soon as you safely can.":
            "Ku kiraabe kiri eky'obuteka, handika ekiro, ekyabaireho n'abajurizi boona.",
        "Workplaces with 25+ staff are legally required to have a sexual harassment policy and committee - you can report to them or your supervisor.":
            "Emyanya y'emirimo erimu abakozi 25 n'okuhingura eshemereire kugira enkora n'akakiiko aha kutwarwa kubi omu by'obushambani.",
        "If it's unresolved or you don't feel safe reporting internally, a Labour Officer must keep your report confidential.":
            "Ku kitakemuka nari otarikuhulira ori omu buteka kurahura omunda, noobaasa kurahura aha Labour Officer omu kihama.",
        "FIDA-Uganda and the Uganda Law Society Legal Aid Project both offer free, confidential support.":
            "FIDA-Uganda na Uganda Law Society Legal Aid Project nibihayo obuhwezi obw'obusa kandi bw'ekihama.",
    },
}


def _translated_action_step(description, language="en"):
    language = _sms_language(language)

    if language == "en":
        return description

    return SMS_ACTION_STEP_TRANSLATIONS.get(
        language,
        {},
    ).get(
        description,
        description,
    )
def _first_action_step(detail, language="en"):
    for topic in detail["rights_topics"]:
        if topic["action_steps"]:
            description = topic["action_steps"][0]["description"]
            return _translated_action_step(
                description,
                language,
            )
    return None


def _first_support_service(detail):
    for topic in detail["rights_topics"]:
        for service in topic["support_services"]:
            if service.get("phone_number"):
                return service
    return None


def build_situation_reply(detail, mode="normal", language="en"):
    intro = _situation_intro(detail, mode, language)
    step = _first_action_step(detail, language)
    service = _first_support_service(detail)

    parts = [intro]
    if step:
        parts.append(f"Next step: {step}")
    if service:
        if mode == "discreet":
            parts.append(f"A support contact is available: {service['phone_number']}")
        else:
            parts.append(f"{service['name']}: {service['phone_number']}")

    return " ".join(parts)


def build_support_reply(detail=None, mode="normal"):
    """
    Builds a support-contacts reply. If `detail` (from get_situation_detail)
    is given, uses that situation's linked support services; otherwise
    falls back to the general emergency-services list.
    """
    if detail is not None:
        services = []
        for topic in detail["rights_topics"]:
            services.extend(topic["support_services"])
    else:
        services = list(
            SupportService.objects.filter(
                is_emergency_service=True, is_active=True
            )
            .order_by("name")
            .values("name", "phone_number")
        )

    if mode == "discreet":
        lines = [s["phone_number"] for s in services if s.get("phone_number")]
    else:
        lines = [
            f"{s['name']}: {s['phone_number']}"
            for s in services
            if s.get("phone_number")
        ]
    return "\n".join(lines) if lines else NO_SUPPORT_SERVICES_REPLY


def build_safety_reply(detail=None, trigger_key="immediate_danger"):
    if detail is not None:
        message = get_safety_message(detail["slug"], trigger_key)
        if message:
            return message
    return GENERAL_SAFETY_REPLY


def build_steps_reply(
    detail,
    mode="normal",
    language="en",
):
    if mode == "discreet":
        return DISCREET_STEPS_REPLY

    steps = []

    for topic in detail["rights_topics"]:
        steps.extend(topic["action_steps"])

    if not steps:
        return NO_ACTION_STEPS_REPLY

    lines = [
        (
            f"{i + 1}. "
            f"{_translated_action_step(step['description'], language)}"
        )
        for i, step in enumerate(steps)
    ]

    return "\n".join(lines)


def build_unmatched_reply(language="en"):
    language = _sms_language(language)
    return UNMATCHED_REPLIES[language]


def build_followup_expired_reply(language="en"):
    language = _sms_language(language)
    return FOLLOWUP_EXPIRED_REPLIES[language]
