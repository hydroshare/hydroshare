# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_core', '0028_baseresource_extra_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcefile',
            name='logical_file_content_type',
            field=models.ForeignKey(related_name='files', blank=True, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='resourcefile',
            name='logical_file_object_id',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='resourcefile',
            name='mime_type',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
