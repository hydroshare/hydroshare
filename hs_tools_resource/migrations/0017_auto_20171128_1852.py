# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_tools_resource', '0016_merge'),
    ]

    operations = [
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
