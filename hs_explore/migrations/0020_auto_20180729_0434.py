# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('hs_core', '0037_auto_20180209_0309'),
        ('hs_explore', '0019_auto_20180725_1702'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResourcePreferences',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('interacted_resources', models.ManyToManyField(related_name='interested_resources', editable=False, to='hs_core.BaseResource')),
            ],
        ),
        migrations.CreateModel(
            name='ResourcePrefToPair',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pref_type', models.CharField(max_length=10, null=True, choices=[(b'Ownership', b'Ownership'), (b'Propensity', b'Propensity')])),
                ('weight', models.FloatField(editable=False)),
                ('state', models.CharField(default=b'Seen', max_length=8, choices=[(b'Seen', b'Seen'), (b'Rejected', b'Rejected')])),
                ('pair', models.ForeignKey(editable=False, to='hs_explore.KeyValuePair')),
                ('res_pref', models.ForeignKey(editable=False, to='hs_explore.ResourcePreferences')),
            ],
        ),
        migrations.RemoveField(
            model_name='userpreferences',
            name='interacted_resources',
        ),
        migrations.AddField(
            model_name='resourcepreferences',
            name='preferences',
            field=models.ManyToManyField(related_name='for_res_pref', editable=False, through='hs_explore.ResourcePrefToPair', to='hs_explore.KeyValuePair'),
        ),
        migrations.AddField(
            model_name='resourcepreferences',
            name='user',
            field=models.OneToOneField(editable=False, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='resourcepreftopair',
            unique_together=set([('res_pref', 'pair', 'pref_type')]),
        ),
    ]
