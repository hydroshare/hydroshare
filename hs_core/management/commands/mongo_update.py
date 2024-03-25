from django.core.management.base import BaseCommand
from django.db.models import Q
from hs_core.hydro_realtime_signal_processor import update_mongo
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey


class Command(BaseCommand):
    help = "Update Mongo Discovery records."

    def handle(self, *args, **options):
        dqs = BaseResource.objects.filter(Q(raccess__discoverable=True)
                                            | Q(raccess__public=True)).select_related('raccess')
        print("Django count = {}".format(dqs.count()))
        for r in dqs.iterator():
            print("Updating Mongo record for " + r.short_id)
            try:
                update_mongo(r.short_id)
            except Exception as e:
                print("failed to update Mongo record for " + r.short_id)
                print(e)