from django.core.management.base import BaseCommand
from django.db.models import Q
from hs_core.hydro_realtime_signal_processor import update_mongo
from hs_core.models import BaseResource


class Command(BaseCommand):
    help = "Update Mongo Discovery records."

    def handle(self, *args, **options):
        dqs = BaseResource.objects.filter(Q(raccess__discoverable=True)
                                          | Q(raccess__public=True))
        failed_resources = []
        print("Django count = {}".format(dqs.count()))
        for r in dqs.iterator():
            print("Updating Mongo record for " + r.short_id)
            try:
                update_mongo(r.short_id)
            except Exception as e:
                failed_resources.append(r.short_id)
        for r in failed_resources:
            print("Failed to update Mongo record for " + r)
