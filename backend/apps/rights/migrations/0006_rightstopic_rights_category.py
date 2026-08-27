from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rights', '0005_merge_20260827_1305'),
    ]

    operations = [
        migrations.AddField(
            model_name='rightstopic',
            name='rights_category',
            field=models.CharField(
                blank=True,
                choices=[
                    ('work-employment', 'Work & Employment'),
                    ('safety-protection', 'Safety & Protection'),
                    ('land-housing', 'Land & Housing'),
                    ('family-inheritance', 'Family & Inheritance'),
                    ('public-services', 'Public Services'),
                    (
                        'community-discrimination',
                        'Community & Discrimination',
                    ),
                ],
                max_length=30,
            ),
        ),
    ]
