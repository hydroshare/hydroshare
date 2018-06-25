# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_explore', '0004_auto_20180624_1803'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupToPair',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='KeyValuePair',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(default=b'subject', max_length=255, editable=False)),
                ('value', models.CharField(default=b'value', max_length=255, editable=False)),
            ],
        ),
        migrations.CreateModel(
            name='ResourceToPair',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pair', models.ForeignKey(editable=False, to='hs_explore.KeyValuePair')),
            ],
        ),
        migrations.CreateModel(
            name='UserToPair',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pair', models.ForeignKey(editable=False, to='hs_explore.KeyValuePair')),
            ],
        ),
        migrations.AlterField(
            model_name='recommendedgroup',
            name='state',
            field=models.IntegerField(default=1, editable=False, choices=[(1, b'New'), (2, b'Shown'), (3, b'Explored'), (4, b'Approved'), (5, b'Dismissed')]),
        ),
        migrations.AlterField(
            model_name='recommendedresource',
            name='state',
            field=models.IntegerField(default=1, editable=False, choices=[(1, b'New'), (2, b'Shown'), (3, b'Explored'), (4, b'Approved'), (5, b'Dismissed')]),
        ),
        migrations.AlterField(
            model_name='recommendeduser',
            name='state',
            field=models.IntegerField(default=1, editable=False, choices=[(1, b'New'), (2, b'Shown'), (3, b'Explored'), (4, b'Approved'), (5, b'Dismissed')]),
        ),
        migrations.AddField(
            model_name='usertopair',
            name='recommendation',
            field=models.ForeignKey(editable=False, to='hs_explore.RecommendedUser'),
        ),
        migrations.AddField(
            model_name='resourcetopair',
            name='recommendation',
            field=models.ForeignKey(editable=False, to='hs_explore.RecommendedResource'),
        ),
        migrations.AlterUniqueTogether(
            name='keyvaluepair',
            unique_together=set([('key', 'value')]),
        ),
        migrations.AddField(
            model_name='grouptopair',
            name='pair',
            field=models.ForeignKey(editable=False, to='hs_explore.KeyValuePair'),
        ),
        migrations.AddField(
            model_name='grouptopair',
            name='recommendation',
            field=models.ForeignKey(editable=False, to='hs_explore.RecommendedGroup'),
        ),
        migrations.AddField(
            model_name='recommendedgroup',
            name='keys',
            field=models.ManyToManyField(related_name='for_group_rec', editable=False, through='hs_explore.GroupToPair', to='hs_explore.KeyValuePair'),
        ),
        migrations.AddField(
            model_name='recommendedresource',
            name='keys',
            field=models.ManyToManyField(related_name='for_resource_rec', editable=False, through='hs_explore.ResourceToPair', to='hs_explore.KeyValuePair'),
        ),
        migrations.AddField(
            model_name='recommendeduser',
            name='keys',
            field=models.ManyToManyField(related_name='for_user_rec', editable=False, through='hs_explore.UserToPair', to='hs_explore.KeyValuePair'),
        ),
    ]
