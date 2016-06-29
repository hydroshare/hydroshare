# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0009_remove_freeform_states_and_countries'),
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1024)),
            ],
        ),
        migrations.AddField(
            model_name='userprofile',
            name='_organization',
            field=models.ForeignKey(blank=True, to='theme.Organization', help_text=b'The organization you work for.', null=True),
        ),
    ]
