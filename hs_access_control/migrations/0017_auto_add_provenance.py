# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
        ('hs_core', '0029_auto_20161123_1858'),
        ('hs_access_control', '0016_auto_enforce_constraints'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupResourceProvenance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privilege', models.IntegerField(default=3, editable=False, choices=[(1, 'Owner'), (2, 'Change'), (3, 'View')])),
                ('start', models.DateTimeField(auto_now_add=True)),
                ('grantor', models.ForeignKey(related_name='x2grq', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, help_text='grantor of privilege')),
                ('group', models.ForeignKey(related_name='g2grq', editable=False, on_delete=models.CASCADE, to='auth.Group', help_text='group to be granted privilege')),
                ('resource', models.ForeignKey(related_name='r2grq', editable=False, on_delete=models.CASCADE, to='hs_core.BaseResource', help_text='resource to which privilege applies')),
            ],
        ),
        migrations.CreateModel(
            name='UserGroupProvenance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privilege', models.IntegerField(default=3, editable=False, choices=[(1, 'Owner'), (2, 'Change'), (3, 'View')])),
                ('start', models.DateTimeField(auto_now_add=True)),
                ('grantor', models.ForeignKey(related_name='x2ugq', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, help_text='grantor of privilege')),
                ('group', models.ForeignKey(related_name='g2ugq', editable=False, on_delete=models.CASCADE, to='auth.Group', help_text='group to which privilege applies')),
                ('user', models.ForeignKey(related_name='u2ugq', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, help_text='user to be granted privilege')),
            ],
        ),
        migrations.CreateModel(
            name='UserResourceProvenance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privilege', models.IntegerField(default=3, editable=False, choices=[(1, 'Owner'), (2, 'Change'), (3, 'View')])),
                ('start', models.DateTimeField(auto_now_add=True)),
                ('grantor', models.ForeignKey(related_name='x2urq', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, help_text='grantor of privilege')),
                ('resource', models.ForeignKey(related_name='r2urq', editable=False, on_delete=models.CASCADE, to='hs_core.BaseResource', help_text='resource to which privilege applies')),
                ('user', models.ForeignKey(related_name='u2urq', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, help_text='user to be granted privilege')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='userresourceprovenance',
            unique_together=set([('user', 'resource', 'start')]),
        ),
        migrations.AlterUniqueTogether(
            name='usergroupprovenance',
            unique_together=set([('user', 'group', 'start')]),
        ),
        migrations.AlterUniqueTogether(
            name='groupresourceprovenance',
            unique_together=set([('group', 'resource', 'start')]),
        ),
    ]
