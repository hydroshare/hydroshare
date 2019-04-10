# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_tools_resource', '0009_auto_20160929_1543'),
    ]

    operations = [
        migrations.AlterField(
            model_name='toolicon',
            name='url',
            field=models.CharField(default=b'', max_length=1024, blank=True),
        ),
        migrations.RenameField(
            model_name='toolicon',
            old_name='url',
            new_name='value'
        ),
        migrations.AlterField(
            model_name='apphomepageurl',
            name='value',
            field=models.CharField(default=b'', max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='requesturlbase',
            name='value',
            field=models.CharField(default=b'', max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='supportedrestypes',
            name='supported_res_types',
            field=models.ManyToManyField(to='hs_tools_resource.SupportedResTypeChoices', blank=True),
        ),
        migrations.AlterField(
            model_name='supportedsharingstatus',
            name='sharing_status',
            field=models.ManyToManyField(to='hs_tools_resource.SupportedSharingStatusChoices', blank=True),
        ),
    ]
