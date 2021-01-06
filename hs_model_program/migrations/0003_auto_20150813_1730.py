# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0004_auto_20150721_1125'),
        ('hs_modelinstance', '0002_auto_20150813_1345'),
        ('hs_model_program', '0002_auto_20150813_1729'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='modelprogramresource',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='modelprogramresource',
            name='creator',
        ),
        migrations.RemoveField(
            model_name='modelprogramresource',
            name='edit_groups',
        ),
        migrations.RemoveField(
            model_name='modelprogramresource',
            name='edit_users',
        ),
        migrations.RemoveField(
            model_name='modelprogramresource',
            name='last_changed_by',
        ),
        migrations.RemoveField(
            model_name='modelprogramresource',
            name='owners',
        ),
        migrations.RemoveField(
            model_name='modelprogramresource',
            name='page_ptr',
        ),
        migrations.RemoveField(
            model_name='modelprogramresource',
            name='user',
        ),
        migrations.RemoveField(
            model_name='modelprogramresource',
            name='view_groups',
        ),
        migrations.RemoveField(
            model_name='modelprogramresource',
            name='view_users',
        ),
        migrations.DeleteModel(
            name='ModelProgramResource',
        ),
        migrations.CreateModel(
            name='ModelProgramResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Model Program Resource',
                'proxy': True,
            },
            bases=('hs_core.genericresource',),
        ),
    ]
