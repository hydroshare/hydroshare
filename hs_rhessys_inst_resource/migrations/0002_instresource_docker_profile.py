# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_docker_processes', '0001_initial'),
        ('hs_rhessys_inst_resource', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='instresource',
            name='docker_profile',
            field=models.ForeignKey(blank=True, to='django_docker_processes.DockerProfile', null=True),
            preserve_default=True,
        ),
    ]
