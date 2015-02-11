# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_docker_processes', '0001_initial'),
        ('hs_rhessys_inst_resource', '0003_auto_20150210_1911'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelRun',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('model_command_line_parameters', models.CharField(max_length=1024, null=True, blank=True)),
                ('docker_process', models.ForeignKey(to='django_docker_processes.DockerProcess')),
                ('model_instance', models.ForeignKey(to='hs_rhessys_inst_resource.InstResource')),
            ],
            options={
                'verbose_name': 'RHESSys Model Run',
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='instresource',
            name='model_command_line_parameters',
        ),
    ]
