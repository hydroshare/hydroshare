from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.features import Features
from datetime import datetime
from pprint import pprint


class Command(BaseCommand):
    help = "Print information about a user."

    def handle(self, *args, **options):
        # x = Features.visited_resources(datetime(2017, 11, 20, 0, 0, 0, 0),
        #                                datetime(2018, 1, 1, 0, 0, 0, 0))
        # pprint(x)
        # x = Features.resource_viewers(datetime(2017, 11, 20, 0, 0, 0, 0),
        #                               datetime(2018, 1, 1, 0, 0, 0, 0))
        # pprint(x)
        # x = Features.resource_owners()
        # pprint(x)
        # x = Features.resource_editors()
        # pprint(x)
        # x = Features.resource_downloads(datetime(2017, 11, 20, 0, 0, 0, 0),
        #                                 datetime(2018, 1, 1, 0, 0, 0, 0))
        # pprint(x)
        # x = Features.user_downloads(datetime(2017, 11, 20, 0, 0, 0, 0),
        #                             datetime(2018, 1, 1, 0, 0, 0, 0))
        # pprint(x)
        # x = Features.resource_apps(datetime(2017, 11, 20, 0, 0, 0, 0),
        #                            datetime(2018, 1, 1, 0, 0, 0, 0))
        # pprint(x)
        # x = Features.user_apps(datetime(2017, 11, 20, 0, 0, 0, 0),
        #                        datetime(2018, 1, 1, 0, 0, 0, 0))
        # pprint(x)
        # print the feature vector for all resources.

        for r in BaseResource.objects.all():
            pprint(Features.resource_features(r))
