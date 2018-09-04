# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('hs_explore', '0023_auto_20180827_1700'),
    ]

    operations = [
        migrations.CreateModel(
            name='OwnershipPreferences',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='OwnershipPrefToPair',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pref_for', models.CharField(max_length=8, choices=[(b'Resource', b'Resource'), (b'User', b'User'), (b'Group', b'Group')])),
                ('weight', models.FloatField(editable=False)),
                ('state', models.CharField(default=b'Seen', max_length=8, choices=[(b'Seen', b'Seen'), (b'Rejected', b'Rejected')])),
                ('own_pref', models.ForeignKey(editable=False, to='hs_explore.OwnershipPreferences')),
                ('pair', models.ForeignKey(editable=False, to='hs_explore.KeyValuePair')),
            ],
        ),
        migrations.AddField(
            model_name='ownershippreferences',
            name='preferences',
            field=models.ManyToManyField(related_name='for_own_pref', editable=False, through='hs_explore.OwnershipPrefToPair', to='hs_explore.KeyValuePair'),
        ),
        migrations.AddField(
            model_name='ownershippreferences',
            name='user',
            field=models.OneToOneField(editable=False, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='ownershippreftopair',
            unique_together=set([('own_pref', 'pref_for', 'pair')]),
        ),
    ]
