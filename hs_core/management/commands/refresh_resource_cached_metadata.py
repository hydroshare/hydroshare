"""
Management command to refresh the cached metadata for a specific resource or all resources.

This command iterates through all resources and updates their cached metadata 
using the update_all_cached_metadata method.
It tracks failed resources and their errors, and prints success information for 
each successfully updated resource.
"""

import time
from django.core.management.base import BaseCommand

from hs_core.models import BaseResource


class Command(BaseCommand):
    help = "Refresh the cached metadata for all resources or a specific resource"

    def add_arguments(self, parser):
        # Optional verbose flag
        parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="Enable verbose output to show detailed information about the update process"
        )

        # Optional resource ID flag for updating a specific resource
        parser.add_argument(
            "--resource-id",
            type=str,
            help="Optional. Process only the resource with this ID (short_id)"
        )

    def handle(self, *args, **options):
        verbose = options.get("verbose", False)
        resource_id = options.get("resource_id")
        start_time = time.time()

        if resource_id:
            # Process single resource
            try:
                base_resource = BaseResource.objects.get(short_id=resource_id)
                resource = base_resource
                self.stdout.write(f"Processing resource (ID: {resource.short_id})")

                if verbose:
                    self.stdout.write(f"  Current cached metadata: {resource.cached_metadata}")

                # Update cached metadata
                resource.update_all_cached_metadata()
                resource.refresh_from_db()

                self.stdout.write(
                    self.style.SUCCESS(f"Successfully updated resource {resource.short_id}")
                )
                self.stdout.write(f"  Updated cached metadata: {resource.cached_metadata}")

            except BaseResource.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Resource with ID '{resource_id}' not found")
                )
                return
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to update resource {resource_id}: {str(e)}")
                )
                return
        else:
            # Process all resources with confirmation
            total_resources = BaseResource.objects.count()

            # Prompt for confirmation when updating all resources
            prompt_message = "Do you want to continue? (yes/no): "
            confirm = input(f"This will update cached metadata for all {total_resources} resources. {prompt_message}")
            if confirm.lower() not in ['yes', 'y']:
                self.stdout.write("Operation cancelled.")
                return

            # Get all resources using iterator for memory efficiency and performance
            resources = BaseResource.objects.iterator()
            self.stdout.write(f"Processing {total_resources} resources...")

            # Track failed resources and their errors
            failed_resources = {}
            success_count = 0

            for index, base_resource in enumerate(resources, 1):
                try:
                    resource = base_resource

                    if verbose:
                        self.stdout.write(f"[{index}/{total_resources}] Processing resource (ID: {resource.short_id})")
                        self.stdout.write(f"  Current cached metadata: {resource.cached_metadata}")

                    # Update cached metadata
                    resource.update_all_cached_metadata()

                    # Refresh the resource object to get updated cached metadata
                    resource.refresh_from_db()

                    success_count += 1

                    # Print updated metadata for each successful resource
                    self.stdout.write(
                        self.style.SUCCESS(f"[{index}/{total_resources}] Successfully updated resource {resource.short_id}")
                    )
                    self.stdout.write(f"  Updated cached metadata: {resource.cached_metadata}")

                    if verbose:
                        self.stdout.write("")  # Empty line for better readability

                except Exception as e:
                    # Track the failed resource and its error
                    failed_resources[base_resource.short_id] = str(e)
                    err_msg = f"[{index}/{total_resources}] Failed to update resource {base_resource.short_id}: {str(e)}"
                    self.stdout.write(
                        self.style.ERROR(err_msg)
                    )

            # Print summary
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("SUMMARY")
            self.stdout.write("=" * 60)
            self.stdout.write(f"Total resources processed: {total_resources}")
            self.stdout.write(self.style.SUCCESS(f"Successfully updated: {success_count}"))
            self.stdout.write(self.style.ERROR(f"Failed to update: {len(failed_resources)}"))

            # Print details of failed resources
            if failed_resources:
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write("FAILED RESOURCES AND ERRORS")
                self.stdout.write("=" * 60)
                for resource_id, error in failed_resources.items():
                    self.stdout.write(f"Resource ID: {resource_id}")
                    self.stdout.write(f"Error: {error}")
                    self.stdout.write("-" * 40)
            else:
                self.stdout.write(self.style.SUCCESS("\nAll resources were updated successfully!"))

        end_time = time.time()
        self.stdout.write(f"Total time taken: {end_time - start_time:.2f} seconds")
