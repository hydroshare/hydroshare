# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_tools_resource', '0018_auto_20180530_2246'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportedFileExtensions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(default=b'', max_length=1024, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_supportedfileextensions_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='supportedfileextensions',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
