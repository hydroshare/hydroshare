# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0003_auto_20160302_0453'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='create_irods_user_account',
            field=models.BooleanField(default=False, help_text=b'Check to create an iRODS user account in xDCIShare user iRODS space for staging large files (>2GB) using iRODS clients such as Cyberduck (https://cyberduck.io/) and icommands (https://docs.irods.org/master/icommands/user/).Uncheck to delete your iRODS user account. Note that deletion of your iRODS user account deletes all of your files under this account as well.'),
        ),
    ]
