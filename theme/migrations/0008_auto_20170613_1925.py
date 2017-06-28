# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0007_auto_20170427_1553'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quotamessage',
            name='content',
            field=models.TextField(default=b'To request additional quota, please contact {email}. We will try to accommodate reasonable requests for additional quota. If you have a large quota request you may need to contribute toward the costs of providing the additional space you need. See https://pages.xdcishare.renci.org/about-xdcishare/policies/quota/ for more information about the quota policy.'),
        ),
        migrations.AlterField(
            model_name='quotamessage',
            name='enforce_content_prepend',
            field=models.TextField(default=b'Your action to add content to xDCIShare was refused because you have exceeded your quota. Your quota for xDCIShare resources is {allocated}{unit} in {zone} zone. You currently have resources that consume {used}{unit}, {percent}% of your quota. '),
        ),
        migrations.AlterField(
            model_name='quotamessage',
            name='grace_period_content_prepend',
            field=models.TextField(default=b'You have exceeded your xDCIShare quota. Your quota for xDCIShare resources is {allocated}{unit} in {zone} zone. You currently have resources that consume {used}{unit}, {percent}% of your quota. You have a grace period until {cut_off_date} to reduce your use to below your quota, or to acquire additional quota, after which you will no longer be able to create new resources in xDCIShare. '),
        ),
        migrations.AlterField(
            model_name='quotamessage',
            name='warning_content_prepend',
            field=models.TextField(default=b'Your quota for xDCIShare resources is {allocated}{unit} in {zone} zone. You currently have resources that consume {used}{unit}, {percent}% of your quota. Once your quota reaches 100% you will no longer be able to create new resources in xDCIShare. '),
        ),
        migrations.AlterField(
            model_name='siteconfiguration',
            name='copyright',
            field=models.TextField(default=b'&copy {% now "Y" %} University of North Carolina Board of Trustees'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='create_irods_user_account',
            field=models.BooleanField(default=False, help_text=b'Check to create an iRODS user account in xDCIShare user iRODS space for staging large files (>2GB) using iRODS clients such as Cyberduck (https://cyberduck.io/) and icommands (https://docs.irods.org/master/icommands/user/).Uncheck to delete your iRODS user account. Note that deletion of your iRODS user account deletes all of your files under this account as well.'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='details',
            field=models.TextField(help_text=b'Tell the xDCIShare community a little about yourself.', null=True, verbose_name=b'Description', blank=True),
        ),
        migrations.AlterField(
            model_name='userquota',
            name='zone',
            field=models.CharField(default='xdcishare_internal', max_length=100),
        ),
    ]
