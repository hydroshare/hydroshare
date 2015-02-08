# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contributor',
            name='researchGateID',
        ),
        migrations.RemoveField(
            model_name='contributor',
            name='researcherID',
        ),
        migrations.RemoveField(
            model_name='creator',
            name='researchGateID',
        ),
        migrations.RemoveField(
            model_name='creator',
            name='researcherID',
        ),
        migrations.AlterField(
            model_name='contributor',
            name='content_type',
            field=models.ForeignKey(related_name='hs_core_contributor_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='coverage',
            name='content_type',
            field=models.ForeignKey(related_name='hs_core_coverage_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='creator',
            name='content_type',
            field=models.ForeignKey(related_name='hs_core_creator_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='date',
            name='content_type',
            field=models.ForeignKey(related_name='hs_core_date_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='description',
            name='content_type',
            field=models.ForeignKey(related_name='hs_core_description_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='format',
            name='content_type',
            field=models.ForeignKey(related_name='hs_core_format_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='genericresource',
            name='content',
            field=models.TextField(),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='identifier',
            name='content_type',
            field=models.ForeignKey(related_name='hs_core_identifier_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='language',
            name='content_type',
            field=models.ForeignKey(related_name='hs_core_language_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='publisher',
            name='content_type',
            field=models.ForeignKey(related_name='hs_core_publisher_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='relation',
            name='content_type',
            field=models.ForeignKey(related_name='hs_core_relation_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rights',
            name='content_type',
            field=models.ForeignKey(related_name='hs_core_rights_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='source',
            name='content_type',
            field=models.ForeignKey(related_name='hs_core_source_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='subject',
            name='content_type',
            field=models.ForeignKey(related_name='hs_core_subject_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='title',
            name='content_type',
            field=models.ForeignKey(related_name='hs_core_title_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='type',
            name='content_type',
            field=models.ForeignKey(related_name='hs_core_type_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='externalprofilelink',
            unique_together=set([('type', 'url', 'object_id')]),
        ),
    ]
