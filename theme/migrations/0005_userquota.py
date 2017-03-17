# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('theme', '0004_userprofile_create_irods_user_account'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserQuota',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('allocated_value', models.BigIntegerField(default=20)),
                ('used_value', models.BigIntegerField(default=0)),
                ('unit', models.CharField(default=b'GB', max_length=10)),
                ('zone', models.CharField(default=b'hydroshare_internal', max_length=100)),
                ('user', models.ForeignKey(related_query_name=b'quotas', related_name='quotas', editable=False, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User quota',
                'verbose_name_plural': 'User quotas',
            },
        ),
        migrations.CreateModel(
            name='QuotaMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('warning_content_prepend', models.TextField(
                    default=b'Your quota for HydroShare resources is {allocated}{unit} in zone {zone}. You currently have resources that consume {used}{unit}, {percent}% of your quota. Once your quota reaches 100% you will no longer be able to create new resources in HydroShare. ')),
                ('enforce_content_prepend', models.TextField(
                    default=b'Your action to add content to HydroShare was refused due to being over your HydroShare quota. Your quota for HydroShare resources is {allocated}{unit} in zone {zone}. You currently have resources that consume {used}{unit}, {percent}% of your quota. ')),
                ('content', models.TextField(
                    default=b'To request additional quota, please contact support@hydroshare.org. We will try accommodate reasonable requests for additional quota. If you have a large quota request you may need to contribute toward the costs of providing the additional space you need. See https://pages.hydroshare.org/about-hydroshare/policies/quota/ for more information about the quota policy.')),
                ('soft_limit_percent', models.IntegerField(default=80)),
            ],
        ),
    ]
