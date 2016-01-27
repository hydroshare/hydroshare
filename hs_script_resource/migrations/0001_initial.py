# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0014_auto_20151123_1451'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScriptMetaData',
            fields=[
                ('coremetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_core.CoreMetaData')),
            ],
            options={
            },
            bases=('hs_core.coremetadata',),
        ),
        migrations.CreateModel(
            name='ScriptSpecificMetadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('scriptLanguage', models.CharField(default=b'R', help_text=b'The programming language that the script is written in', max_length=100, verbose_name=b'Programming Language', blank=True)),
                ('languageVersion', models.CharField(help_text=b'The software version of the script', max_length=255, verbose_name=b'Programming Language Version', blank=True)),
                ('scriptVersion', models.CharField(default=b'1.0', help_text=b'The software version or build number of the script', max_length=255, verbose_name=b'Script Version', blank=True)),
                ('scriptDependencies', models.CharField(help_text=b'Dependencies for the script (externally-imported packages)', max_length=400, verbose_name=b'Dependencies', blank=True)),
                ('scriptReleaseDate', models.DateTimeField(help_text=b'The date that this version of the script was released', null=True, verbose_name=b'Release Date', blank=True)),
                ('scriptCodeRepository', models.CharField(help_text=b'A URL to the source code repository (e.g. git, mercurial, svn)', max_length=255, verbose_name=b'Script Repository', blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_script_resource_scriptspecificmetadata_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='scriptspecificmetadata',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.CreateModel(
            name='ScriptResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Script Resource',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
    ]
