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

        res_show_in_discover = False
        for r in dqs.iterator():
            resource = get_resource_by_shortkey(r.short_id, or_404=False)
            res_show_in_discover = resource.show_in_discover

            if res_show_in_discover and r.short_id:
                print("Updating Mongo record for " + resource.short_id)
                try:
                    update_mongo(resource)
                except Exception as e:
                    print("failed to update Mongo record for " + resource.short_id)
                    print(e)