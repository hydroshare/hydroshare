from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0088_re_populate_resource_cached_metadata'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResourceSizeCache',
            fields=[
                ('resource', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                                  primary_key=True, related_name='size_cache',
                                                  serialize=False, to='hs_core.baseresource')),
                ('size', models.BigIntegerField()),
                ('quota_size', models.BigIntegerField()),
                ('has_unknown', models.BooleanField()),
            ],
        ),
    ]
