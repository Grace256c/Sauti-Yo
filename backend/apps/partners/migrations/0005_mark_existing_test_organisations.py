from django.db import migrations


TEST_ORGANISATION_NAMES = [
    "Sauti Yo Test Legal Aid Partner",
    "Sauti Yo Test Partner Two",
]


def mark_test_organisations(apps, schema_editor):
    PartnerOrganisation = apps.get_model(
        "partners",
        "PartnerOrganisation",
    )

    PartnerOrganisation.objects.filter(
        support_service__name__in=TEST_ORGANISATION_NAMES,
    ).update(
        is_test=True,
    )


def unmark_test_organisations(apps, schema_editor):
    PartnerOrganisation = apps.get_model(
        "partners",
        "PartnerOrganisation",
    )

    PartnerOrganisation.objects.filter(
        support_service__name__in=TEST_ORGANISATION_NAMES,
    ).update(
        is_test=False,
    )


class Migration(migrations.Migration):

    dependencies = [
        (
            "partners",
            "0004_partnerorganisation_is_test",
        ),
    ]

    operations = [
        migrations.RunPython(
            mark_test_organisations,
            unmark_test_organisations,
        ),
    ]
