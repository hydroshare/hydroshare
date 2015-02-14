# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_rhessys_inst_resource', '0008_auto_20150212_2127'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelRunOptions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('model_run', models.ForeignKey(to='hs_rhessys_inst_resource.ModelRun')),
            ],
            options={
                'verbose_name': 'Model run options',
            },
            bases=(models.Model,),
        ),
    ]
