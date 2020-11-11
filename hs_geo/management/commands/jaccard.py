
"""test the jaccard metric for the distance between two resources
point coverage: 5057577e8573433d8045b59db91b2550
box coverage: a173f02bd00b4eceb0a9f44cc77cee6d
box coverage negative longitude: cd8bc1c38b254031854b8b8aaee08a05
"""

from django.core.management.base import BaseCommand
# from hs_core.models import BaseResource
# from hs_core.management.utils import CheckResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_core.models import BaseResource
from hs_geo.jaccard import geo_jaccard
from pprint import pprint


class Command(BaseCommand):
    help = "Print results of testing resource integrity."

    def add_arguments(self, parser):

        # a list of resource id's: none does nothing.
        parser.add_argument('r1', type=str)
        parser.add_argument('r2', type=str)

    def handle(self, *args, **options):
        r1 = options['r1']
        r2 = options['r2']
        res1 = get_resource_by_shortkey(r1)
        if r2 != 'all': 
            res2 = get_resource_by_shortkey(r2)
            out = geo_jaccard(res1, res2)
            print("jaccard({}, {}) = {}".format(r1, r2, out))
        else: 
            for r2 in BaseResource.objects.all(): 
                res2 = get_resource_by_shortkey(r2.short_id)
                print("comparing {} and {}".format(res1.short_id, res2.short_id))
                out = geo_jaccard(res1, res2)
                print("jaccard({}, {}) = {}".format(res1.short_id, res2.short_id, out))
