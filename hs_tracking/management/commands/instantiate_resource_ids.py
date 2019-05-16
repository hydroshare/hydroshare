"""
Instantiate resource ID's for tracking records.
"""
from django.core.management.base import BaseCommand
import re
from datetime import datetime, timedelta
from hs_tracking.models import Variable
from hs_core.hydroshare import get_resource_by_shortkey
from hs_core.models import BaseResource


# a base RE for identifying the resource_id in a request.
RESOURCE_RE = {"visit": re.compile('resource/([0-9a-f]{32})/'),
               "download": re.compile('id=([0-9a-f]{32})\|'),
               "app_launch": re.compile('id=([0-9a-f]{32})\|'),
               "create": re.compile('id=([0-9a-f]{32})\|'),
               "delete": re.compile('id=([0-9a-f]{32})\|')}
# these two REs identify specific kinds of visits

# TODO: Move hostname to session variable to reduce runtime.
# TODO: IP_RE = re.compile('user_ip=([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\|')
LANDING_RE = re.compile('resource/([0-9a-f]{32})/$')  # reference to resource home page
REST_RE = re.compile('/hsapi/')  # reference to a REST call, except for __internal
INTERNAL_RE = re.compile('/hsapi/_internal/')  # reference to an internal page


def instantiate_timestamp_range(start, end):
    """ instantiate a range of Variable requests """
    events = 0
    ids = 0
    print("instantiating ids from -{} days to -{} days from now".format(start, end))
    for v in Variable.objects.filter(timestamp__gte=datetime.now()-timedelta(start),
                                     timestamp__lte=datetime.now()-timedelta(end)):
        events = events + 1
        value = v.get_value()
        if v.name in RESOURCE_RE:
            m = RESOURCE_RE[v.name].search(value)
            if (m and m.group(1)):
                resource_id = m.group(1)
                if(resource_id is not None):
                    v.last_resource_id = resource_id
                    try:
                        resource = get_resource_by_shortkey(resource_id, or_404=False)
                        v.resource = resource
                    except BaseResource.DoesNotExist:
                        pass
                    # print("{} for '{}' ".format(resource_id, value))
                    ids = ids + 1
                    if ids % 1000 == 0:
                        print("{} of {}".format(ids, events))

                    if v.name == 'visit':  # for visits, classify kind of visit
                        if LANDING_RE.search(value):
                            v.landing = True
                        else:
                            v.landing = False
                        if REST_RE.search(value):
                            if INTERNAL_RE.search(value):
                                v.rest = False
                            else:
                                v.rest = True
                        else:
                            v.rest = False

                    v.save()

                # else:
                #    print("NONE for '{}'".format(value))
            # else:
            #     print("NONE for '{}'".format(value))
    print("resource ids found for {} of {} events".format(ids, events))


def instantiate_resource_ids():
    """ instantiate the resource id field for older usage events """
    # This must be processed in batches because the events
    # exceed memory limits if batched all at once.
    instantiate_timestamp_range(365, 0)
    instantiate_timestamp_range(365*2, 365)
    instantiate_timestamp_range(365*3, 365*2)


class Command(BaseCommand):
    help = "Instantiate all resource id's for tracking."

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        instantiate_resource_ids()
