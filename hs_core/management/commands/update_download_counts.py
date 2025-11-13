# management/commands/update_download_counts.py
import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
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
        parser.add_argument(
            '--skip-duplicates',
            action='store_true',
            dest='skip_duplicates',
            help='Skip duplicate resource IDs instead of raising an error',
        )

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        dry_run = options['dry_run']
        skip_duplicates = options['skip_duplicates']

        # Validate CSV file exists
        if not os.path.exists(csv_file_path):
            raise CommandError(f"CSV file not found: {csv_file_path}")

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be saved to the database")
            )

        # Pre-validate CSV for duplicates
        self.stdout.write("Validating CSV file for duplicates...")
        duplicates = self.validate_csv_uniqueness(csv_file_path)

        if duplicates and not skip_duplicates:
            raise CommandError(
                f"Found {len(duplicates)} duplicate resource ID(s): {', '.join(sorted(duplicates))}\n"
                f"Use --skip-duplicates to skip duplicates instead of failing."
            )
        elif duplicates and skip_duplicates:
            self.stdout.write(
                self.style.WARNING(f"Found {len(duplicates)} duplicate resource ID(s) that will be skipped")
            )

        success_count = 0
        error_count = 0
        skipped_count = 0
        duplicate_count = 0

        # Track resource IDs to detect duplicates
        seen_resource_ids = set()

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

                # Process each row
                for row_number, row in enumerate(reader, 1):
                    if len(row) < 2:
                        self.stdout.write(
                            self.style.WARNING(f"Row {row_number}: Skipped - insufficient columns")
                        )
                        skipped_count += 1
                        continue

                    short_id = row[0].strip()

                    # Check for duplicate resource IDs
                    if short_id in seen_resource_ids:
                        if skip_duplicates:
                            self.stdout.write(
                                self.style.WARNING(f"Row {row_number}: Skipped duplicate resource ID - {short_id}")
                            )
                            duplicate_count += 1
                            continue
                        else:
                            # This should not happen if pre-validation passed, but handle it anyway
                            raise CommandError(
                                f"Duplicate resource ID found: {short_id} at row {row_number}. "
                                f"Use --skip-duplicates to skip duplicates instead of failing."
                            )

                    seen_resource_ids.add(short_id)

                    try:
                        download_count = int(row[1].strip())
                        if download_count < 0:
                            raise ValueError("Download count cannot be negative")
                    except ValueError as e:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Row {row_number}: Skipped - invalid download count: "
                                f"{row[1]} ({str(e)})"
                            )
                        )
                        skipped_count += 1
                        continue

                    # Find the resource
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
                            # Update the download count
                            with transaction.atomic():
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

        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("UPDATE SUMMARY")
        self.stdout.write("=" * 50)

        if dry_run:
            self.stdout.write(f"Mode: {self.style.WARNING('DRY RUN')}")

        self.stdout.write(f"Unique resource IDs in CSV: {len(seen_resource_ids)}")
        self.stdout.write(f"Duplicate resource IDs found: {len(duplicates)}")
        self.stdout.write(f"Successfully processed: {self.style.SUCCESS(str(success_count))}")
        self.stdout.write(f"Errors: {self.style.ERROR(str(error_count))}")
        self.stdout.write(f"Skipped (invalid data): {self.style.WARNING(str(skipped_count))}")
        self.stdout.write(f"Skipped (duplicates): {self.style.WARNING(str(duplicate_count))}")
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

                for row_number, row in enumerate(reader, 1):
                    if len(row) >= 1 and row[0].strip():  # Only process if we have at least one column with data
                        resource_id = row[0].strip()
                        if resource_id in resource_ids:
                            duplicates.add(resource_id)
                        else:
                            resource_ids.add(resource_id)
        except Exception as e:
            raise CommandError(f"Error validating CSV file: {str(e)}")

        return duplicates
