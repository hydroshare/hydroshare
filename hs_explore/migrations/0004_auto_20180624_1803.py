# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('hs_core', '0037_auto_20180209_0309'),
        ('auth', '0006_require_contenttypes_0002'),
        ('hs_explore', '0003_auto_20180624_1741'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecommendedGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('relevance', models.FloatField(default=0.0, editable=False)),
                ('state', models.IntegerField(default=1, editable=False, choices=[(1, b'New'), (2, b'Viewed'), (3, b'Approved'), (4, b'Dismissed')])),
                ('candidate_group', models.ForeignKey(related_name='group_recommendation', editable=False, to='auth.Group')),
                ('user', models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RecommendedResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('relevance', models.FloatField(default=0.0, editable=False)),
                ('state', models.IntegerField(default=1, editable=False, choices=[(1, b'New'), (2, b'Viewed'), (3, b'Approved'), (4, b'Dismissed')])),
                ('candidate_resource', models.ForeignKey(related_name='resource_recommendation', editable=False, to='hs_core.BaseResource')),
                ('user', models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RecommendedUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('relevance', models.FloatField(default=0.0, editable=False)),
                ('state', models.IntegerField(default=1, editable=False, choices=[(1, b'New'), (2, b'Viewed'), (3, b'Approved'), (4, b'Dismissed')])),
                ('candidate_user', models.ForeignKey(related_name='user_recommendation', editable=False, to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='recommendedgroups',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='recommendedgroups',
            name='candidate_group',
        ),
        migrations.RemoveField(
            model_name='recommendedgroups',
            name='user',
        ),
        migrations.AlterUniqueTogether(
            name='recommendedresources',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='recommendedresources',
            name='candidate_resource',
        ),
        migrations.RemoveField(
            model_name='recommendedresources',
            name='user',
        ),
        migrations.AlterUniqueTogether(
            name='recommendedusers',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='recommendedusers',
            name='candidate_user',
        ),
        migrations.RemoveField(
            model_name='recommendedusers',
            name='user',
        ),
        migrations.DeleteModel(
            name='RecommendedGroups',
        ),
        migrations.DeleteModel(
            name='RecommendedResources',
        ),
        migrations.DeleteModel(
            name='RecommendedUsers',
        ),
        migrations.AlterUniqueTogether(
            name='recommendeduser',
            unique_together=set([('user', 'candidate_user')]),
        ),
        migrations.AlterUniqueTogether(
            name='recommendedresource',
            unique_together=set([('user', 'candidate_resource')]),
        ),
        migrations.AlterUniqueTogether(
            name='recommendedgroup',
            unique_together=set([('user', 'candidate_group')]),
        ),
    ]
