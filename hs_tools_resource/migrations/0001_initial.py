# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings
import hs_core.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('pages', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
        ('hs_core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Fee',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('description', models.TextField()),
                ('value', models.DecimalField(max_digits=10, decimal_places=2)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_fee_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RequestUrlBase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(max_length='500', null=True)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_requesturlbase_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ToolMetaData',
            fields=[
                ('coremetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, on_delete=models.CASCADE, to='hs_core.CoreMetaData')),
            ],
            options={
            },
            bases=('hs_core.coremetadata',),
        ),
        migrations.CreateModel(
            name='ToolResource',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, on_delete=models.CASCADE, to='pages.Page')),
                ('comments_count', models.IntegerField(default=0, editable=False)),
                ('rating_count', models.IntegerField(default=0, editable=False)),
                ('rating_sum', models.IntegerField(default=0, editable=False)),
                ('rating_average', models.FloatField(default=0, editable=False)),
                ('public', models.BooleanField(default=True, help_text='If this is true, the resource is viewable and downloadable by anyone')),
                ('frozen', models.BooleanField(default=False, help_text='If this is true, the resource should not be modified')),
                ('do_not_distribute', models.BooleanField(default=False, help_text='If this is true, the resource owner has to designate viewers')),
                ('discoverable', models.BooleanField(default=True, help_text='If this is true, it will turn up in searches.')),
                ('published_and_frozen', models.BooleanField(default=False, help_text='Once this is true, no changes can be made to the resource')),
                ('content', models.TextField()),
                ('short_id', models.CharField(default=hs_core.models.short_id, max_length=32, db_index=True)),
                ('doi', models.CharField(help_text=b"Permanent identifier. Never changes once it's been set.", max_length=1024, null=True, db_index=True, blank=True)),
                ('object_id', models.PositiveIntegerField(null=True, blank=True)),
                ('content_type', models.ForeignKey(blank=True, on_delete=models.CASCADE, to='contenttypes.ContentType', null=True)),
                ('creator', models.ForeignKey(related_name='creator_of_hs_tools_resource_toolresource', on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL, help_text='This is the person who first uploaded the resource')),
                ('edit_groups', models.ManyToManyField(help_text='This is the set of Hydroshare Groups who can edit the resource', related_name='group_editable_hs_tools_resource_toolresource', null=True, to='auth.Group', blank=True)),
                ('edit_users', models.ManyToManyField(help_text='This is the set of Hydroshare Users who can edit the resource', related_name='user_editable_hs_tools_resource_toolresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('last_changed_by', models.ForeignKey(related_name='last_changed_hs_tools_resource_toolresource', on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL, help_text='The person who last changed the resource', null=True)),
                ('owners', models.ManyToManyField(help_text='The person who has total ownership of the resource', related_name='owns_hs_tools_resource_toolresource', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(related_name='toolresources', verbose_name='Author', on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('view_groups', models.ManyToManyField(help_text='This is the set of Hydroshare Groups who can view the resource', related_name='group_viewable_hs_tools_resource_toolresource', null=True, to='auth.Group', blank=True)),
                ('view_users', models.ManyToManyField(help_text='This is the set of Hydroshare Users who can view the resource', related_name='user_viewable_hs_tools_resource_toolresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Tool Resource',
            },
            bases=('pages.page', models.Model),
        ),
        migrations.CreateModel(
            name='ToolResourceType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('tool_res_type', models.CharField(max_length='500', null=True)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_toolresourcetype_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ToolVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(max_length='500', null=True)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_toolversion_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
