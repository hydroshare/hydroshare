# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0004_auto_20150721_1125'),
        ('ref_ts', '0002_auto_20150813_1336'),
    ]

    operations = [
        migrations.CreateModel(
            name='RefTimeSeries',
            fields=[
                ('baseresource_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_core.BaseResource')),
                ('reference_type', models.CharField(default='', max_length=4, blank=True)),
                ('url', models.URLField(default='', verbose_name='Web Services Url', blank=True)),
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'HIS Referenced Time Series',
                'proxy': False,
            },
            bases=('hs_core.genericresource',),
        ),
    ]
