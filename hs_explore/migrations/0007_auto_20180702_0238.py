# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('hs_explore', '0006_auto_20180628_1903'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupPreferences',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('preferences', models.TextField(null=True)),
                ('group', models.ForeignKey(editable=False, to='auth.Group')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='grouppreferences',
            unique_together=set([('group', 'preferences')]),
        ),
    ]
