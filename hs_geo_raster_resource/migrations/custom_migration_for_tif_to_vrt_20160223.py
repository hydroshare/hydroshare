from django.db import migrations


def migrate_tif_file(apps, schema_editor):
    pass


def undo_migrate_tif_file(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('hs_geo_raster_resource', '0004_auto_20151116_2257'),
    ]

    operations = [
        migrations.RunPython(code=migrate_tif_file, reverse_code=undo_migrate_tif_file),
    ]
