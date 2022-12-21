# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_core', '0020_baseresource_collections'),
    ]

    operations = [
        migrations.CreateModel(
            name='FundingAgency',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('agency_name', models.TextField()),
                ('award_title', models.TextField(null=True, blank=True)),
                ('award_number', models.TextField(null=True, blank=True)),
                ('agency_url', models.URLField(null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_core_fundingagency_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
