# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_modelinstance', '0006_auto_20151216_1511'),
        ('hs_core', '0026_merge'),
        ('hs_modflow_modelinstance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MODFLOWModelInstanceMetaData',
            fields=[
                ('modelinstancemetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_modelinstance.ModelInstanceMetaData')),
            ],
            bases=('hs_modelinstance.modelinstancemetadata',),
        ),
        migrations.CreateModel(
            name='ExecutedBy',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('hs_modelinstance.executedby',),
        ),
        migrations.CreateModel(
            name='ModelOutput',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('hs_modelinstance.modeloutput',),
        ),
        migrations.CreateModel(
            name='MODFLOWModelInstanceResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'MODFLOW Model Instance Resource',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
    ]
