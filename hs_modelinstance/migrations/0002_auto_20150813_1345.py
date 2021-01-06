# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0004_auto_20150721_1125'),
        ('hs_modelinstance', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='modelinstanceresource',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='modelinstanceresource',
            name='creator',
        ),
        migrations.RemoveField(
            model_name='modelinstanceresource',
            name='edit_groups',
        ),
        migrations.RemoveField(
            model_name='modelinstanceresource',
            name='edit_users',
        ),
        migrations.RemoveField(
            model_name='modelinstanceresource',
            name='last_changed_by',
        ),
        migrations.RemoveField(
            model_name='modelinstanceresource',
            name='owners',
        ),
        migrations.RemoveField(
            model_name='modelinstanceresource',
            name='page_ptr',
        ),
        migrations.RemoveField(
            model_name='modelinstanceresource',
            name='user',
        ),
        migrations.RemoveField(
            model_name='modelinstanceresource',
            name='view_groups',
        ),
        migrations.RemoveField(
            model_name='modelinstanceresource',
            name='view_users',
        ),
        migrations.DeleteModel(
            name='ModelInstanceResource',
        ),
        migrations.CreateModel(
            name='ModelInstanceResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Model Instance Resource',
                'proxy': True,
            },
            bases=('hs_core.genericresource',),
        ),
    ]
