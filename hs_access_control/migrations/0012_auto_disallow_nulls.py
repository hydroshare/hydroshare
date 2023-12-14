# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0011_auto_rename_new_fields_to_original_names'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupaccess',
            name='group',
            field=models.OneToOneField(related_query_name='gaccess', related_name='gaccess', editable=False, on_delete=models.CASCADE, to='auth.Group', help_text='group object that this object protects'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='groupresourceprivilege',
            name='grantor',
            field=models.ForeignKey(related_name='x2grp', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, help_text='grantor of privilege'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='groupresourceprivilege',
            name='group',
            field=models.ForeignKey(related_name='g2grp', editable=False, on_delete=models.CASCADE, to='auth.Group', help_text='group to be granted privilege'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='groupresourceprivilege',
            name='resource',
            field=models.ForeignKey(related_name='r2grp', editable=False, to='hs_core.BaseResource', on_delete=models.CASCADE, help_text='resource to which privilege applies'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resourceaccess',
            name='resource',
            field=models.OneToOneField(related_query_name='raccess', related_name='raccess', editable=False, on_delete=models.CASCADE, to='hs_core.BaseResource'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='useraccess',
            name='user',
            field=models.OneToOneField(related_query_name='uaccess', related_name='uaccess', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='usergroupprivilege',
            name='grantor',
            field=models.ForeignKey(related_name='x2ugp', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, help_text='grantor of privilege'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='usergroupprivilege',
            name='group',
            field=models.ForeignKey(related_name='g2ugp', editable=False, on_delete=models.CASCADE, to='auth.Group', help_text='group to which privilege applies'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='usergroupprivilege',
            name='user',
            field=models.ForeignKey(related_name='u2ugp', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, help_text='user to be granted privilege'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userresourceprivilege',
            name='grantor',
            field=models.ForeignKey(related_name='x2urp', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, help_text='grantor of privilege'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userresourceprivilege',
            name='resource',
            field=models.ForeignKey(related_name='r2urp', editable=False, on_delete=models.CASCADE, to='hs_core.BaseResource', help_text='resource to which privilege applies'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userresourceprivilege',
            name='user',
            field=models.ForeignKey(related_name='u2urp', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, help_text='user to be granted privilege'),
            preserve_default=True,
        ),
    ]
