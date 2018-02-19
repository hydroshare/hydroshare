# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('hs_core', '0037_auto_20180209_0309'),
    ]

    operations = [
        migrations.CreateModel(
            name='Recommend',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('state', models.IntegerField(default=1, choices=[(1, b'New'), (2, b'Viewed'), (3, b'Approved'), (4, b'Dismissed')])),
                ('resource', models.ForeignKey(to='hs_core.BaseResource')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='recommend',
            unique_together=set([('user', 'resource')]),
        ),
    ]
