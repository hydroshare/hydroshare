# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_rhessys_inst_resource', '0011_modelrunoptions_value'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResourceOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('value', models.CharField(max_length=4096)),
                ('resource', models.ForeignKey(to='hs_rhessys_inst_resource.InstResource')),
            ],
            options={
                'verbose_name': 'Resource option',
            },
            bases=(models.Model,),
        ),
        migrations.AlterModelOptions(
            name='modelrunoptions',
            options={'verbose_name': 'Model run option'},
        ),
    ]
