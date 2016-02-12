# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_model_program', '0001_initial'),
        ('hs_core', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExecutedBy',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('model_name', models.CharField(default=None, max_length=500)),
                ('content_type', models.ForeignKey(related_name='hs_modelinstance_executedby_related', to='contenttypes.ContentType')),
                ('model_program_fk', models.ForeignKey(related_name='modelinstance', default=None, blank=True, to='hs_model_program.ModelProgramResource', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ModelInstanceMetaData',
            fields=[
                ('coremetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_core.CoreMetaData')),
            ],
            bases=('hs_core.coremetadata',),
        ),
        migrations.CreateModel(
            name='ModelOutput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('includes_output', models.BooleanField(default=False)),
                ('content_type', models.ForeignKey(related_name='hs_modelinstance_modeloutput_related', to='contenttypes.ContentType')),
            ],
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
            bases=('hs_core.baseresource',),
        ),
        migrations.AlterUniqueTogether(
            name='modeloutput',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='executedby',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
