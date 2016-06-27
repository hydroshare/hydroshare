# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import localflavor.us.models
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0006_normalize_user_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='new_country',
            field=django_countries.fields.CountryField(default=b'', blank=True, max_length=2),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='new_state',
            field=localflavor.us.models.USStateField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='create_irods_user_account',
            field=models.BooleanField(default=False, help_text=b'Check to create an iRODS user account in HydroShare user iRODS space for staging large files (>2GB) using iRODS clients such as Cyberduck (https://cyberduck.io/) and icommands (https://docs.irods.org/master/icommands/user/). Uncheck to delete your iRODS user account. Note that deletion of your iRODS user account deletes all of your files under this account as well.'),
        ),
    ]
