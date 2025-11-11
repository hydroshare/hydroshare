import asyncio
from django.core.management.base import BaseCommand
from asgiref.sync import sync_to_async
from hs_core.tasks import set_resource_files_system_metadata
from hs_core.hydroshare.utils import resource_modified, get_resource_by_shortkey


class Command(BaseCommand):
    help = 'Find and process resources modified since a given date'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            default='2025-08-18',
            help='Date in YYYY-MM-DD format (e.g., 2025-08-18)'
        )
        parser.add_argument(
            '--time',
            type=str,
            default='00:00:00 UTC',
            help='Time component (default: 00:00:00 UTC)'
        )

    async def run_mc_command(self, date_string):
        """Run the mc command and return resource IDs with their latest modification dates"""
        # Convert the date string format for mc command
        mc_date_string = date_string.replace('T', ' ', 1)

        # First, get buckets modified since the target date
        bucket_cmd = (
            f"mc ls hydroshare/ --json | "
            f"jq -r 'select(.lastModified > \"{date_string}\") | .key' | "
            f"sed 's|/$||' | "
            f"grep -v -E '^(bags|zips|tmp|published)$'"
        )

        self.stdout.write("Finding updated buckets...")

        proc = await asyncio.create_subprocess_shell(
            bucket_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            self.stderr.write(f"Error finding buckets: {stderr.decode('utf-8')}")
            return []

        buckets = stdout.decode('utf-8').strip().split('\n')
        buckets = [b for b in buckets if b.strip()]  # Remove empty lines

        if not buckets:
            self.stdout.write("No updated buckets found")
            return []

        self.stdout.write(f"Found {len(buckets)} updated bucket(s)")

        # Now process each bucket to get resource IDs and their latest dates
        resource_data = {}

        for bucket in buckets:
            self.stdout.write(f"Processing bucket: {bucket}")

            # Get all objects in this bucket with their modification dates
            # Use the formatted date string for mc find command
            resource_cmd = (
                f"mc find hydroshare/{bucket} --newer-than \"{mc_date_string}\" --json | "
                f"jq -r '[.key, .lastModified] | @tsv'"
            )

            proc = await asyncio.create_subprocess_shell(
                resource_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                self.stderr.write(f"Error processing bucket {bucket}: {stderr.decode('utf-8')}")
                continue

            output = stdout.decode('utf-8').strip()
            if not output:
                continue

            # Parse the output: each line is "key\tlastModified"
            for line in output.split('\n'):
                if line.strip():
                    try:
                        key, last_modified = line.strip().split('\t')
                        # Extract resourceId (third path component)
                        parts = key.split('/')
                        if len(parts) >= 3:
                            resource_id = parts[2]
                            # Update the latest date for this resource
                            if resource_id not in resource_data or last_modified > resource_data[resource_id]:
                                resource_data[resource_id] = last_modified
                    except ValueError:
                        continue

        # Convert to list of tuples (resource_id, last_modified)
        return list(resource_data.items())

    async def process_resources(self, resource_data):
        """Process each resource ID with its last modified date"""
        for resource_id, last_modified in resource_data:
            if resource_id.strip():  # Skip empty lines
                try:
                    # Use sync_to_async to call the synchronous Django function
                    await self.set_bag_dirty(resource_id.strip(), last_modified)
                except Exception as e:
                    self.stderr.write(f"Error processing {resource_id}: {e}")

    def handle(self, *args, **options):
        date_str = options['date']
        time_str = options['time']
        full_date_string = f"{date_str}T{time_str}"

        self.stdout.write(f"Finding resources modified since: {full_date_string}")

        # Run the async commands
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            resource_data = loop.run_until_complete(self.run_mc_command(full_date_string))
            self.stdout.write(f"Found {len(resource_data)} resource(s) to process")

            if resource_data:
                # Sort by last modified date (most recent first)
                resource_data.sort(key=lambda x: x[1], reverse=True)

                # Display found resources
                for resource_id, last_modified in resource_data:
                    self.stdout.write(f"  - {resource_id}: {last_modified}")

                loop.run_until_complete(self.process_resources(resource_data))
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully processed {len(resource_data)} resource(s)"
                    )
                )
            else:
                self.stdout.write("No resources to process")

        except Exception as e:
            self.stderr.write(f"Error: {e}")
        finally:
            loop.close()

    # Wrap the synchronous function with sync_to_async
    @sync_to_async
    def set_bag_dirty(self, resource_id, last_modified):
        """Process a single resource by updating its metadata and marking it as modified"""
        self.stdout.write(f"Processing resource: {resource_id}")

        resource = get_resource_by_shortkey(resource_id, or_404=False)
        if not resource:
            self.stderr.write(f"Resource {resource_id} does not exist, skipping.")
            return

        # Convert last_modified string to datetime for comparison
        from datetime import datetime
        minio_modified = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))

        last_updated = resource.last_updated
        if last_updated and last_updated >= minio_modified:
            self.stdout.write(f"Resource {resource_id} metadata is up to date, skipping.")
            return

        print(f"Updating resource_files_system_metadata {resource_id}")
        print(f"Minio files modified:{minio_modified}")
        print(f"Django resource has updated: {last_updated}")
        set_resource_files_system_metadata.apply_async((resource.short_id,))

        # we assume the user is the same as the last modified user
        user = resource.last_changed_by
        print(f"Marking resource {resource_id} as last modified by "
              f"{user.username}")
        resource_modified(resource, user, overwrite_bag=False)
