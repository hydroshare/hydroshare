# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('hs_explore', '0008_auto_20180702_0418'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupPreferences',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group', models.ForeignKey(editable=False, to='auth.Group')),
            ],
        ),
        migrations.CreateModel(
            name='GroupPrefToPair',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group_pref', models.ForeignKey(editable=False, to='hs_explore.GroupPreferences')),
                ('pair', models.ForeignKey(editable=False, to='hs_explore.KeyValuePair')),
            ],
        ),
        migrations.AddField(
            model_name='grouppreferences',
            name='preferences',
            field=models.ManyToManyField(related_name='for_group_pref', editable=False, through='hs_explore.GroupPrefToPair', to='hs_explore.KeyValuePair'),
        ),
        migrations.AlterUniqueTogether(
            name='grouppreftopair',
            unique_together=set([('group_pref', 'pair')]),
        ),
    ]
