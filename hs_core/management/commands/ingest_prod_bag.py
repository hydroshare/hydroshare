"""
This command download a production bag and ingests into a resource.
"""
from tempfile import NamedTemporaryFile
import requests
from requests.auth import HTTPBasicAuth

from django.core.management.base import BaseCommand

from hs_composite_resource.models import CompositeResource
from hs_core.models import BaseResource
from django.conf import settings


class Command(BaseCommand):
    help = "Download and ingest a production bag into a resource"

    def add_arguments(self, parser):
        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):

        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                ingest_bag(rid)
        else:
            for r in BaseResource.objects.all():
                ingest_bag(r.short_id)


def ingest_bag(res_id):
    res = CompositeResource.objects.get(short_id=res_id)

    url = f"https://www.hydroshare.org/django_s3/rest_download/bags/{res_id}.zip"
    istorage = res.get_s3_storage()
    response = requests.get(url, auth=HTTPBasicAuth(settings.HS_AUTH_USER, settings.HS_AUTH_PASSWORD))

    if response.status_code == 200:
        with NamedTemporaryFile() as f:
            f.write(response.content)
            f.flush()
            istorage.saveFile(f.name, f"bags/{res_id}.zip")
    else:
        response.raise_for_status()

    istorage.unzip(f"bags/{res_id}.zip", f"{res_id}")
