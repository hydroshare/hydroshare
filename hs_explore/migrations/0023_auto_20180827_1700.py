# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('hs_core', '0037_auto_20180209_0309'),
        ('hs_explore', '0022_resourcepreftopair_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='PropensityPreferences',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='PropensityPrefToPair',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('weight', models.FloatField(editable=False)),
                ('state', models.CharField(default=b'Seen', max_length=8, choices=[(b'Seen', b'Seen'), (b'Rejected', b'Rejected')])),
                ('pref_for', models.CharField(max_length=8, choices=[(b'Resource', b'Resource'), (b'User', b'User'), (b'Group', b'Group')])),
                ('pair', models.ForeignKey(editable=False, to='hs_explore.KeyValuePair')),
                ('prop_pref', models.ForeignKey(editable=False, to='hs_explore.PropensityPreferences')),
            ],
        ),
        migrations.CreateModel(
            name='UserInteractedResources',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('interacted_resources', models.ManyToManyField(related_name='interacted_resources', editable=False, to='hs_core.BaseResource')),
                ('user', models.OneToOneField(editable=False, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserNeighbors',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('neighbors', models.ManyToManyField(related_name='user_neighbors', editable=False, to=settings.AUTH_USER_MODEL)),
                ('user', models.OneToOneField(editable=False, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RemoveField(
            model_name='resourcepreftopair',
            name='time',
        ),
        migrations.AddField(
            model_name='propensitypreferences',
            name='preferences',
            field=models.ManyToManyField(related_name='for_prop_pref', editable=False, through='hs_explore.PropensityPrefToPair', to='hs_explore.KeyValuePair'),
        ),
        migrations.AddField(
            model_name='propensitypreferences',
            name='user',
            field=models.OneToOneField(editable=False, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='propensitypreftopair',
            unique_together=set([('prop_pref', 'pref_for', 'pair')]),
        ),
    ]
