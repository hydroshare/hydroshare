# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0004_userprofile_create_irods_user_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='user_type_other',
            field=models.CharField(max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='user_type',
            field=models.CharField(default=b'Unspecified', max_length=1024, choices=[(b'', b'(unspecified)'), (b'University Faculty', b'University Faculty'), (b'University Professional or Research Staff', b'University Professional or Research Staff'), (b'Post-Doctoral Fellow', b'Post-Doctoral Fellow'), (b'University Graduate Student', b'University Graduate Student'), (b'University Undergraduate Student', b'University Undergraduate Student'), (b'Commercial/Professional', b'Commercial/Professional'), (b'Government Official', b'Government Official'), (b'School Student Kindergarten to 12th Grade', b'School Student Kindergarten to 12th Grade'), (b'School Teacher Kindergarten to 12th Grade', b'School Teacher Kindergarten to 12th Grade'), (b'Other', b'Other')]),
        ),
    ]
