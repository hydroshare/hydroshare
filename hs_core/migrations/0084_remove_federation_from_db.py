# Generated by Django 3.2.25 on 2024-07-15 16:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0083_auto_20240702_2038'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
            ],
            # Operations to be performed on the database.
            database_operations=[
                migrations.RunSQL(
                    sql='ALTER TABLE "hs_core_genericresource" DROP COLUMN "resource_federation_path" CASCADE;',
                ),
                migrations.RunSQL(
                    sql='DROP INDEX IF EXISTS "hs_core_resourcefile_object_id_fed_resource_file_15f4618e_idx";',
                ),
                migrations.RunSQL(
                    sql='ALTER TABLE "hs_core_resourcefile" DROP COLUMN "fed_resource_file" CASCADE;',
                ),
            ],
        ),
    ]