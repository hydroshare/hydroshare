from django.db import migrations


def migrate_tif_file(apps, schema_editor):
    pass


def undo_migrate_tif_file(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('hs_geo_raster_resource', '0005_auto_20160509_2116'),
    ]

    operations = [
        migrations.RunPython(code=migrate_tif_file, reverse_code=undo_migrate_tif_file),
    ]
