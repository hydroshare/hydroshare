# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0017_auto_add_provenance'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupresourceprovenance',
            name='undone',
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name='usergroupprovenance',
            name='undone',
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name='userresourceprovenance',
            name='undone',
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AlterField(
            model_name='groupresourceprovenance',
            name='grantor',
            field=models.ForeignKey(related_name='x2grq', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, help_text='grantor of privilege', null=True),
        ),
        migrations.AlterField(
            model_name='usergroupprovenance',
            name='grantor',
            field=models.ForeignKey(related_name='x2ugq', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, help_text='grantor of privilege', null=True),
        ),
        migrations.AlterField(
            model_name='userresourceprovenance',
            name='grantor',
            field=models.ForeignKey(related_name='x2urq', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, help_text='grantor of privilege', null=True),
        ),
    ]
