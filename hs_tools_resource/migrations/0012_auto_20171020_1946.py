# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_tools_resource', '0011_toolicon_data_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportedFileTypeChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='SupportedFileTypes',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_supportedfiletypes_related', to='contenttypes.ContentType')),
                ('supported_file_types', models.ManyToManyField(related_name='associated_with', to='hs_tools_resource.SupportedFileTypeChoices', blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='supportedrestypes',
            name='supported_res_types',
            field=models.ManyToManyField(related_name='associated_with', to='hs_tools_resource.SupportedResTypeChoices', blank=True),
        ),
        migrations.AlterField(
            model_name='supportedsharingstatus',
            name='sharing_status',
            field=models.ManyToManyField(related_name='associated_with', to='hs_tools_resource.SupportedSharingStatusChoices', blank=True),
        ),
    ]
