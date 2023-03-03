# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0003_auto_20150721_1122'),
    ]

    operations = [
        migrations.CreateModel(
            name='GenericResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
        migrations.AlterField(
            model_name='baseresource',
            name='creator',
            field=models.ForeignKey(related_name='creator_of_hs_core_baseresource', on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL, help_text='This is the person who first uploaded the resource'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='baseresource',
            name='edit_groups',
            field=models.ManyToManyField(help_text='This is the set of Hydroshare Groups who can edit the resource', related_name='group_editable_hs_core_baseresource', null=True, to='auth.Group', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='baseresource',
            name='edit_users',
            field=models.ManyToManyField(help_text='This is the set of Hydroshare Users who can edit the resource', related_name='user_editable_hs_core_baseresource', null=True, to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='baseresource',
            name='last_changed_by',
            field=models.ForeignKey(related_name='last_changed_hs_core_baseresource', on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL, help_text='The person who last changed the resource', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='baseresource',
            name='owners',
            field=models.ManyToManyField(help_text='The person who has total ownership of the resource', related_name='owns_hs_core_baseresource', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='baseresource',
            name='user',
            field=models.ForeignKey(related_name='baseresources', verbose_name='Author', on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='baseresource',
            name='view_groups',
            field=models.ManyToManyField(help_text='This is the set of Hydroshare Groups who can view the resource', related_name='group_viewable_hs_core_baseresource', null=True, to='auth.Group', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='baseresource',
            name='view_users',
            field=models.ManyToManyField(help_text='This is the set of Hydroshare Users who can view the resource', related_name='user_viewable_hs_core_baseresource', null=True, to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
        migrations.AlterModelTable(
            name='baseresource',
            table='hs_core_genericresource',
        ),
    ]
