# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0009_auto_remove_original_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupresourceprivilege',
            name='grantornew',
            field=models.ForeignKey(related_name='x2grp', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, help_text='grantor of privilege', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='groupresourceprivilege',
            name='groupnew',
            field=models.ForeignKey(related_name='g2grp', editable=False, on_delete=models.CASCADE, to='auth.Group', help_text='group to be granted privilege', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='groupresourceprivilege',
            name='resourcenew',
            field=models.ForeignKey(related_name='r2grp', editable=False, on_delete=models.CASCADE, to='hs_core.BaseResource', help_text='resource to which privilege applies', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='usergroupprivilege',
            name='grantornew',
            field=models.ForeignKey(related_name='x2ugp', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, help_text='grantor of privilege', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='usergroupprivilege',
            name='groupnew',
            field=models.ForeignKey(related_name='g2ugp', editable=False, on_delete=models.CASCADE, to='auth.Group', help_text='group to which privilege applies', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='usergroupprivilege',
            name='usernew',
            field=models.ForeignKey(related_name='u2ugp', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, help_text='user to be granted privilege', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userresourceprivilege',
            name='grantornew',
            field=models.ForeignKey(related_name='x2urp', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, help_text='grantor of privilege', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userresourceprivilege',
            name='resourcenew',
            field=models.ForeignKey(related_name='r2urp', editable=False, on_delete=models.CASCADE, to='hs_core.BaseResource', help_text='resource to which privilege applies', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userresourceprivilege',
            name='usernew',
            field=models.ForeignKey(related_name='u2urp', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, help_text='user to be granted privilege', null=True),
            preserve_default=True,
        ),
    ]
