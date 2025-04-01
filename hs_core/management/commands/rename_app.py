"""
A Django Management Command to rename existing Django Applications.

See https://github.com/odwyersoftware/django-rename-app
"""

import logging

from django.core.management.base import BaseCommand
from django.db import connection, ProgrammingError
from django.db.backends.utils import truncate_name
from django.db.transaction import atomic

logger = logging.getLogger(__name__)


def removeprefix(value, prefix):
    if value.startswith(prefix):
        return value[len(prefix):]
    return value


class Command(BaseCommand):
    help = (
        "Renames a Django Application. "
        "Usage rename_app [old_app_name] [new_app_name]"
    )

    def add_arguments(self, parser):
        parser.add_argument("old_app_name", nargs=1, type=str)
        parser.add_argument("new_app_name", nargs=1, type=str)

    @atomic
    def handle(self, old_app_name, new_app_name, *args, **options):
        with connection.cursor() as cursor:
            old_app_name = old_app_name[0]
            new_app_name = new_app_name[0]
            print(f"Renaming {old_app_name} to {new_app_name}, please wait...")
            cursor.execute(
                "SELECT * FROM django_content_type "
                f"where app_label='{new_app_name}'"
            )

            has_already_been_ran = cursor.fetchone()

            if has_already_been_ran:
                logger.info(
                    "Rename has already been done, exiting without "
                    "making any changes"
                )
                print("Nothing to rename. Exiting.")
                return None

            cursor.execute(
                f"UPDATE django_content_type SET app_label='{new_app_name}' "
                f"WHERE app_label='{old_app_name}'"
            )
            cursor.execute(
                f"UPDATE django_migrations SET app='{new_app_name}' "
                f"WHERE app='{old_app_name}'"
            )

            cursor.execute(
                "SELECT sequence_schema, sequence_name "
                "FROM information_schema.sequences "
                f"WHERE sequence_name LIKE '{old_app_name}_%';"
            )
            sequence_entries = cursor.fetchall()

            for entry in sequence_entries:
                suffix = removeprefix(entry[1], f"{old_app_name}_")

                old_sequence_name = truncate_name(
                    f"{old_app_name}_{suffix}",
                    connection.ops.max_name_length(),
                )

                new_sequence_name = truncate_name(
                    f"{new_app_name}_{suffix}",
                    connection.ops.max_name_length(),
                )

                try:
                    query = (
                        f'ALTER SEQUENCE "{old_sequence_name}" '
                        f'RENAME TO "{new_sequence_name}"'
                    )
                    cursor.execute(query)
                    print(
                        f"Renamed sequence from [{old_sequence_name}] "
                        f"to [{new_sequence_name}]."
                    )
                except ProgrammingError:
                    logger.warning(
                        'Rename query failed: "%s"', query, exc_info=True
                    )

            cursor.execute(
                "SELECT table_name FROM information_schema.tables "
                f"WHERE table_name LIKE '{old_app_name}_%';"
            )
            table_names = cursor.fetchall()

            for table_name in table_names:
                suffix = removeprefix(table_name[0], f"{old_app_name}_")

                old_table_name = truncate_name(
                    f"{old_app_name}_{suffix}",
                    connection.ops.max_name_length(),
                )

                new_table_name = truncate_name(
                    f"{new_app_name}_{suffix}",
                    connection.ops.max_name_length(),
                )

                get_all_constraints_query = (
                    "SELECT CONSTRAINT_NAME FROM "
                    "INFORMATION_SCHEMA.TABLE_CONSTRAINTS "
                    f"WHERE TABLE_NAME='{old_table_name}'"
                )

                try:
                    cursor.execute(get_all_constraints_query)
                    constraints = cursor.fetchall()

                    constraints = [
                        constraint[0]
                        for constraint in constraints
                        if constraint[0].startswith(f"{old_app_name}_")
                    ]

                    for constraint in constraints:
                        new_constraint_name = truncate_name(
                            f"{new_table_name}{removeprefix(constraint, old_table_name)}",  # noqa: E501
                            connection.ops.max_name_length(),
                        )

                        if f"_fk_{old_app_name}_" in new_constraint_name:
                            new_constraint_name = new_constraint_name.replace(
                                f"_fk_{old_app_name}_", f"_fk_{new_app_name}_"
                            )

                        query = (
                            f"ALTER TABLE {old_table_name} "
                            f"RENAME CONSTRAINT {constraint} "
                            f"TO {new_constraint_name}"
                        )

                        cursor.execute(query)

                        print(
                            f"Renamed constraint "
                            f"[{constraint}] to [{new_constraint_name}]"
                        )
                except ProgrammingError:
                    logger.warning(
                        "Error occurred while renaming constraints. "
                        'Query: "%s"',
                        query,
                        exc_info=True,
                    )

                get_all_indexes_query = (
                    f"SELECT indexname FROM pg_indexes "
                    f"WHERE tablename='{old_table_name}'"
                )

                try:
                    cursor.execute(get_all_indexes_query)
                    indexes = cursor.fetchall()

                    indexes = [
                        index[0]
                        for index in indexes
                        if index[0].startswith(f"{old_app_name}_")
                    ]

                    for index in indexes:
                        new_name = truncate_name(
                            f"{new_table_name}{index[len(old_table_name):]}",
                            connection.ops.max_name_length(),
                        )
                        query = f"ALTER INDEX {index} " f"RENAME TO {new_name}"

                        cursor.execute(query)

                        print(f"Renamed index [{index}] to [{new_name}]")
                except ProgrammingError:
                    logger.warning(
                        'Error occurred while renaming indexes. Query: "%s"',
                        query,
                        exc_info=True,
                    )

                try:
                    query = (
                        f'ALTER TABLE "{old_table_name}" '
                        f'RENAME TO "{new_table_name}"'
                    )
                    cursor.execute(query)
                    print(
                        f"Renamed table from [{old_table_name}] "
                        f"to [{new_table_name}]."
                    )
                except ProgrammingError:
                    logger.warning(
                        'Rename query failed: "%s"', query, exc_info=True
                    )

            print("Renaming successfully done!")
