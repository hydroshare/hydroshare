# management/commands/update_download_counts.py
import csv
import os
from django.core.management.base import BaseCommand, CommandError
from hs_core.models import BaseResource


class Command(BaseCommand):
    help = 'Update resource download counts from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file containing resource IDs and download counts'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='Run without actually saving changes to the database',
        )

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        dry_run = options['dry_run']

        # Validate CSV file exists
        if not os.path.exists(csv_file_path):
            raise CommandError(f"CSV file not found: {csv_file_path}")

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be saved to the database")
            )

        # Pre-validate CSV for duplicates
        self.stdout.write("Validating CSV file for duplicates...")
        self.validate_csv_uniqueness(csv_file_path)
        success_count = 0
        error_count = 0

        try:
            with open(csv_file_path, 'r') as file:
                # Try different delimiters
                sniffer = csv.Sniffer()
                sample = file.read(1024)
                file.seek(0)

                if sniffer.has_header(sample):
                    dialect = sniffer.sniff(sample)
                    reader = csv.reader(file, dialect)
                    # Skip header row
                    next(reader, None)
                else:
                    # Fallback to default CSV format
                    file.seek(0)
                    reader = csv.reader(file)

                for row_number, row in enumerate(reader, 1):
                    short_id = row[0].strip()
                    download_count = int(row[1].strip())

                    try:
                        resource = BaseResource.objects.get(short_id=short_id)

                        if dry_run:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Row {row_number}: Would update {short_id} - "
                                    f"Current: {resource.download_count}, "
                                    f"Adding: {download_count}, "
                                    f"New: {resource.download_count + download_count}"
                                )
                            )
                            success_count += 1
                        else:
                            resource.download_count += download_count
                            resource.save()

                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Row {row_number}: Updated {short_id} - "
                                    f"Added {download_count} downloads, "
                                    f"New total: {resource.download_count}"
                                )
                            )
                            success_count += 1

                    except BaseResource.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(f"Row {row_number}: Resource not found - {short_id}")
                        )
                        error_count += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Row {row_number}: Error processing {short_id} - {str(e)}")
                        )
                        error_count += 1

        except Exception as e:
            raise CommandError(f"Error reading CSV file: {str(e)}")

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("UPDATE SUMMARY")
        self.stdout.write("=" * 50)

        if dry_run:
            self.stdout.write(f"Mode: {self.style.WARNING('DRY RUN')}")

        self.stdout.write(f"Successfully processed: {self.style.SUCCESS(str(success_count))}")
        self.stdout.write(f"Errors: {self.style.ERROR(str(error_count))}")
        self.stdout.write(f"Total rows processed: {row_number}")

        if dry_run:
            self.stdout.write(
                self.style.WARNING("\nThis was a dry run. No changes were saved to the database.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\nDownload counts have been updated successfully!")
            )

    def validate_csv_uniqueness(self, csv_file_path):
        """
        Pre-validate the entire CSV for unique resource IDs before processing
        Returns a set of duplicate resource IDs found
        """
        resource_ids = set()
        duplicates = set()

        try:
            with open(csv_file_path, 'r') as file:
                # Try to detect if there's a header
                sniffer = csv.Sniffer()
                sample = file.read(1024)
                file.seek(0)

                if sniffer.has_header(sample):
                    dialect = sniffer.sniff(sample)
                    reader = csv.reader(file, dialect)
                    # Skip header row for validation
                    next(reader, None)
                else:
                    # Fallback to default CSV format
                    file.seek(0)
                reader = csv.reader(file)

                for _, row in enumerate(reader, 1):
                    if len(row) <= 1:
                        raise CommandError(
                            "CSV file must have at least two columns: resource_id and download_count"
                        )
                    if row[0].strip():  # Only process if we have at least one column with data
                        resource_id = row[0].strip()
                        if resource_id in resource_ids:
                            duplicates.add(resource_id)
                        else:
                            resource_ids.add(resource_id)
                        download_count = int(row[1].strip())
                        if download_count < 0:
                            raise CommandError(
                                f"Invalid download count '{download_count}' for resource ID "
                                f"'{resource_id}': Download count cannot be negative"
                            )
        except Exception as e:
            raise CommandError(f"Error validating CSV file: {str(e)}")

        if duplicates:
            raise CommandError(
                f"Found {len(duplicates)} duplicate resource ID(s): {', '.join(sorted(duplicates))}\n"
            )
