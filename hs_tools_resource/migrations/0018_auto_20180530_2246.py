# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_tools_resource', '0017_auto_20171128_1852'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportedAggTypeChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='SupportedAggTypes',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_supportedaggtypes_related', to='contenttypes.ContentType')),
                ('supported_agg_types', models.ManyToManyField(related_name='associated_with', to='hs_tools_resource.SupportedAggTypeChoices', blank=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='supportedaggtypes',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
