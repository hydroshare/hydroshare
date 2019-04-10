# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_modflow_modelinstance', '0002_executedby_modeloutput_modflowmodelinstancemetadata_modflowmodelinstanceresource'),
    ]

    operations = [
        migrations.AddField(
            model_name='groundwaterflow',
            name='horizontalFlowBarrierPackage',
            field=models.BooleanField(default=False, verbose_name=b'Includes HFB6 package'),
        ),
        migrations.AddField(
            model_name='groundwaterflow',
            name='seawaterIntrusionPackage',
            field=models.BooleanField(default=False, verbose_name=b'Includes SWI2 package'),
        ),
        migrations.AddField(
            model_name='groundwaterflow',
            name='unsaturatedZonePackage',
            field=models.BooleanField(default=False, verbose_name=b'Includes UZF package'),
        ),
        migrations.AlterField(
            model_name='groundwaterflow',
            name='flowPackage',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name=b'Flow package', choices=[(b'BCF6', b'BCF6'), (b'LPF', b'LPF'), (b'HUF2', b'HUF2'), (b'UPW', b'UPW')]),
        ),
    ]
