# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0020_baseresource_collections'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CollectionDeletedResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resource_title', models.TextField()),
                ('date_deleted', models.DateTimeField(auto_now_add=True)),
                ('resource_id', models.CharField(max_length=32)),
                ('resource_type', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='CollectionResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Collection Resource',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
        migrations.AddField(
            model_name='collectiondeletedresource',
            name='collection',
            field=models.ForeignKey(on_delete=models.CASCADE, to='hs_core.BaseResource'),
        ),
        migrations.AddField(
            model_name='collectiondeletedresource',
            name='deleted_by',
            field=models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
