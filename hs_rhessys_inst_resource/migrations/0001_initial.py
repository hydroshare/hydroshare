# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import hs_core.models
import mezzanine.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('pages', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstResource',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='pages.Page')),
                ('comments_count', models.IntegerField(default=0, editable=False)),
                ('content', mezzanine.core.fields.RichTextField(verbose_name='Content')),
                ('public', models.BooleanField(default=True, help_text=b'If this is true, the resource is viewable and downloadable by anyone')),
                ('frozen', models.BooleanField(default=False, help_text=b'If this is true, the resource should not be modified')),
                ('do_not_distribute', models.BooleanField(default=False, help_text=b'If this is true, the resource owner has to designate viewers')),
                ('discoverable', models.BooleanField(default=True, help_text=b'If this is true, it will turn up in searches.')),
                ('published_and_frozen', models.BooleanField(default=False, help_text=b'Once this is true, no changes can be made to the resource')),
                ('short_id', models.CharField(default=hs_core.models.short_id, max_length=32, db_index=True)),
                ('doi', models.CharField(help_text=b"Permanent identifier. Never changes once it's been set.", max_length=1024, null=True, db_index=True, blank=True)),
                ('object_id', models.PositiveIntegerField(null=True, blank=True)),
                ('name', models.CharField(max_length=50)),
                ('git_repo', models.URLField()),
                ('git_username', models.CharField(max_length=50)),
                ('git_password', models.CharField(max_length=50)),
                ('commit_id', models.CharField(max_length=50)),
                ('model_desc', models.CharField(max_length=500)),
                ('git_branch', models.CharField(max_length=50)),
                ('study_area_bbox', models.CharField(max_length=50)),
                ('model_command_line_parameters', models.CharField(max_length=500)),
                ('project_name', models.CharField(max_length=100)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('creator', models.ForeignKey(related_name='creator_of_hs_rhessys_inst_resource_instresource', to=settings.AUTH_USER_MODEL, help_text=b'This is the person who first uploaded the resource')),
                ('edit_groups', models.ManyToManyField(help_text=b'This is the set of Hydroshare Groups who can edit the resource', related_name='group_editable_hs_rhessys_inst_resource_instresource', null=True, to='auth.Group', blank=True)),
                ('edit_users', models.ManyToManyField(help_text=b'This is the set of Hydroshare Users who can edit the resource', related_name='user_editable_hs_rhessys_inst_resource_instresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('last_changed_by', models.ForeignKey(related_name='last_changed_hs_rhessys_inst_resource_instresource', to=settings.AUTH_USER_MODEL, help_text=b'The person who last changed the resource', null=True)),
                ('owners', models.ManyToManyField(help_text=b'The person who uploaded the resource', related_name='owns_hs_rhessys_inst_resource_instresource', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(related_name='instresources', verbose_name='Author', to=settings.AUTH_USER_MODEL)),
                ('view_groups', models.ManyToManyField(help_text=b'This is the set of Hydroshare Groups who can view the resource', related_name='group_viewable_hs_rhessys_inst_resource_instresource', null=True, to='auth.Group', blank=True)),
                ('view_users', models.ManyToManyField(help_text=b'This is the set of Hydroshare Users who can view the resource', related_name='user_viewable_hs_rhessys_inst_resource_instresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'RHESSys Instance Resource',
            },
            bases=('pages.page', models.Model),
        ),
    ]
