# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0006_auto_20170309_1516'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuotaMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('warning_content_prepend', models.TextField(default=b'Your quota for HydroShare resources is {allocated}{unit} in zone {zone}. You currently have resources that consume {used}{unit}, {percent]% of your quota. Once your quota reaches 100% you will no longer be able to create new resources in HydroShare. ')),
                ('enforce_content_prepend', models.TextField(default=b'Your action to add content to HydroShare was refused due to being over your HydroShare quota. Your quota for HydroShare resources is {allocated}{unit} in zone {zone}. You currently have resources that consume {used}{unit}, {percent]% of your quota. ')),
                ('content', models.TextField(default=b'To request additional quota, please contact support@hydroshare.org. We will try accommodate reasonable requests for additional quota. If you have a large quota request you may need to contribute toward the costs of providing the additional space you need. See https://pages.hydroshare.org/about-hydroshare/policies/quota/ for more information about the quota policy.')),
            ],
        ),
    ]
