# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('hs_explore', '0005_auto_20180625_1953'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupRecToPair',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('weight', models.FloatField(editable=False)),
                ('pair', models.ForeignKey(editable=False, to='hs_explore.KeyValuePair')),
            ],
        ),
        migrations.CreateModel(
            name='ResourceRecToPair',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('weight', models.FloatField(editable=False)),
                ('pair', models.ForeignKey(editable=False, to='hs_explore.KeyValuePair')),
            ],
        ),
        migrations.CreateModel(
            name='UserPreferences',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('preferences', models.TextField(null=True)),
                ('user', models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserRecToPair',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('weight', models.FloatField(editable=False)),
                ('pair', models.ForeignKey(editable=False, to='hs_explore.KeyValuePair')),
            ],
        ),
        migrations.RemoveField(
            model_name='grouptopair',
            name='pair',
        ),
        migrations.RemoveField(
            model_name='grouptopair',
            name='recommendation',
        ),
        migrations.RemoveField(
            model_name='resourcetopair',
            name='pair',
        ),
        migrations.RemoveField(
            model_name='resourcetopair',
            name='recommendation',
        ),
        migrations.RemoveField(
            model_name='usertopair',
            name='pair',
        ),
        migrations.RemoveField(
            model_name='usertopair',
            name='recommendation',
        ),
        migrations.RemoveField(
            model_name='recommendedgroup',
            name='keys',
        ),
        migrations.RemoveField(
            model_name='recommendedresource',
            name='keys',
        ),
        migrations.RemoveField(
            model_name='recommendeduser',
            name='keys',
        ),
        migrations.DeleteModel(
            name='GroupToPair',
        ),
        migrations.DeleteModel(
            name='ResourceToPair',
        ),
        migrations.DeleteModel(
            name='UserToPair',
        ),
        migrations.AddField(
            model_name='userrectopair',
            name='recommendation',
            field=models.ForeignKey(editable=False, to='hs_explore.RecommendedUser'),
        ),
        migrations.AddField(
            model_name='resourcerectopair',
            name='recommendation',
            field=models.ForeignKey(editable=False, to='hs_explore.RecommendedResource'),
        ),
        migrations.AddField(
            model_name='grouprectopair',
            name='recommendation',
            field=models.ForeignKey(editable=False, to='hs_explore.RecommendedGroup'),
        ),
        migrations.AddField(
            model_name='recommendedgroup',
            name='keywords',
            field=models.ManyToManyField(related_name='for_group_rec', editable=False, through='hs_explore.GroupRecToPair', to='hs_explore.KeyValuePair'),
        ),
        migrations.AddField(
            model_name='recommendedresource',
            name='keywords',
            field=models.ManyToManyField(related_name='for_resource_rec', editable=False, through='hs_explore.ResourceRecToPair', to='hs_explore.KeyValuePair'),
        ),
        migrations.AddField(
            model_name='recommendeduser',
            name='keywords',
            field=models.ManyToManyField(related_name='for_user_rec', editable=False, through='hs_explore.UserRecToPair', to='hs_explore.KeyValuePair'),
        ),
        migrations.AlterUniqueTogether(
            name='userrectopair',
            unique_together=set([('recommendation', 'pair')]),
        ),
        migrations.AlterUniqueTogether(
            name='userpreferences',
            unique_together=set([('user', 'preferences')]),
        ),
        migrations.AlterUniqueTogether(
            name='resourcerectopair',
            unique_together=set([('recommendation', 'pair')]),
        ),
        migrations.AlterUniqueTogether(
            name='grouprectopair',
            unique_together=set([('recommendation', 'pair')]),
        ),
    ]
