from django.core.management.base import BaseCommand
from hs_core.hydroshare.features import Features
from pprint import pprint
from datetime import datetime


class Command(BaseCommand):
    help = "Print information about a user."

    def handle(self, *args, **options):
        x = Features.visited_resources(datetime(2017, 11, 20, 0, 0, 0, 0),
                                       datetime(2018, 1, 1, 0, 0, 0, 0))
        pprint(x)
        # x = Features.resource_viewers(datetime(2017, 11, 20, 0, 0, 0, 0),
        #                               datetime(2018, 1, 1, 0, 0, 0, 0))
        # pprint(x)
        # x = Features.resource_owners()
        # pprint(x)
        # x = Features.resource_editors()
        # pprint(x)
