"""Update the MongoDB Discovery Index for changes in resources
Optional argument --force does the update even if the record exists.
Optional argument --debug causes all exceptions to halt execution.
"""
import time

from django.core.management.base import BaseCommand
from django.db.models import Q
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_core.hydroshare_atlas_discovery_collection import MongoDBClient


class Command(BaseCommand):
    help = "Update items in MongoDB Discovery Index based on discoverable resources in Django DB"

    def add_arguments(self, parser):

        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            help='force refresh for unchanged resources',
        )

        parser.add_argument(
            '--debug',
            action='store_true',
            dest='debug',
            help='debug by stopping on any exception',
        )

        parser.add_argument(
            'resource_ids',
            nargs='*',
            type=str,
            help='optional list of resource short_id to update; if not provided, all resources will be checked'
        )

    def create_and_poll_for_item_in_mongodb(self, resource: BaseResource, timeout=120, poll_interval=3):
        """
        Create resource metadata files and poll until the resource appears in MongoDB
        or timeout is reached. Returns True if indexed, False on timeout.
        """
        resource.write_django_metadata_json_files()
        expected_filepath = f"{resource.short_id}/.hsjsonld/dataset_metadata.json"
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            doc = MongoDBClient.get_discovery_collection().find_one(
                {"_s3_filepath": expected_filepath}, {"_id": 1}
            )
            if doc is not None:
                return True
            time.sleep(poll_interval)
        return False

    def handle(self, *args, **options):
        if len(options['resource_ids']) > 0:
            for rid in options['resource_ids']:
                print(f"Updating resource {rid} in Discovery Index...")
                if not options['debug']:
                    try:
                        resource = get_resource_by_shortkey(rid, or_404=False)
                        if resource.show_in_discover:
                            created = self.create_and_poll_for_item_in_mongodb(resource)
                            if not created:
                                print(f"WARNING: {resource.short_id} not indexed in MongoDB within timeout")
                    except BaseResource.DoesNotExist:
                        print(f"resource {rid} does not exist in Django")
                    except Exception as e:
                        print(f"resource {rid} generated exception {str(e)}")
                else:
                    resource = get_resource_by_shortkey(rid, or_404=False)
                    if resource.show_in_discover:
                        created = self.create_and_poll_for_item_in_mongodb(resource)
                        if not created:
                            print(f"WARNING: {resource.short_id} not indexed in MongoDB within timeout")
                print(f"Create/update triggered for resource {rid} in Discovery Index.")
        else:
            discovery_items_iterator = MongoDBClient.get_discovery_collection().find({}, {"identifier": 1})
            django_items = BaseResource.objects.filter(
                Q(raccess__discoverable=True) | Q(raccess__public=True)
            ).select_related('raccess')
            print(f"Django count = {django_items.count()}")

            # Check for resources in Django that aren't in MongoDB Discovery Index
            print("Checking for resources in Django that aren't in Discovery...")
            found_in_discovery = set()
            for item in discovery_items_iterator:
                # Get just the resource ID from the identifier URL and add to set
                found_in_discovery.add(item["identifier"][0].split("/")[-1])
            print(f"Total count of items in MongoDB: {len(found_in_discovery)}")

            discoverable_in_django = 0
            added_to_mongodb = 0
            triggered_refresh_in_mongodb = 0

            for r in django_items.iterator():
                try:
                    resource: BaseResource = get_resource_by_shortkey(r.short_id, or_404=False)
                    resource_is_discoverable = resource.show_in_discover
                    if resource_is_discoverable:
                        discoverable_in_django += 1
                except BaseResource.DoesNotExist:
                    if options["debug"]:
                        raise
                    print(f"resource {r.short_id} no longer found in Django.")
                    continue
                except Exception as e:
                    if options["debug"]:
                        raise
                    print(f"resource {r.short_id} generated exception {str(e)}")
                    continue

                if not resource_is_discoverable:
                    continue

                if resource.short_id not in found_in_discovery:
                    print(f"Resource {resource.short_id} NOT FOUND in MongoDB: adding to MongoDB Discovery Index")
                    try:
                        created = self.create_and_poll_for_item_in_mongodb(resource)
                        if created:
                            added_to_mongodb += 1
                        else:
                            print(f"WARNING: {resource.short_id} not indexed in MongoDB within timeout")
                    except Exception as e:
                        if options["debug"]:
                            raise
                        print(f"resource {resource.short_id} generated exception {str(e)}")

                # If using --force, refresh all discoverable resources, even when already in index
                elif options['force']:
                    print(f"Refreshing index (forced) for resource {resource.short_id}")
                    try:
                        resource.write_django_metadata_json_files()
                        triggered_refresh_in_mongodb += 1
                    except Exception as e:
                        if options["debug"]:
                            raise
                        print(f"resource {resource.short_id} generated exception {str(e)}")

            # Check for what is in MongoDB Discovery Index that isn't in Django and delete
            print("checking for resources in MongoDB Discovery Index that aren't in Django...")
            discovery_items_iterator = MongoDBClient.get_discovery_collection().find({}, {"identifier": 1, "_id": 1})
            found_in_discovery = set()
            for item in discovery_items_iterator:
                found_in_discovery.add((item["identifier"][0].split("/")[-1], item["_id"]))

            deleted_from_mongodb = 0

            for resource_id, discovery_id in found_in_discovery:
                try:
                    resource = get_resource_by_shortkey(resource_id, or_404=False)
                except BaseResource.DoesNotExist:
                    print(f"MongoDB resource {resource_id} NOT FOUND in Django; removing from MongoDB Discovery Index")
                    MongoDBClient.get_discovery_collection().delete_one({"_id": discovery_id})
                    deleted_from_mongodb += 1
                    continue

            print(f"Django contains {discoverable_in_django} discoverable resources")
            print(f"{added_to_mongodb} resources in Django added to MongoDB Discovery Index")
            print(f"{triggered_refresh_in_mongodb} resources were refreshed in MongoDB Discovery Index")
            print(f"{deleted_from_mongodb} resources not in Django removed from MongoDB Discovery Index")
