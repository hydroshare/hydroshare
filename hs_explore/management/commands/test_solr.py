from django.core.management.base import BaseCommand
from hs_core.hydroshare import get_resource_by_shortkey
from hs_explore.solr import find_resources_by_subjects
from pprint import pprint


class Command(BaseCommand):
    def add_arguments(self, parser):

        # a list of resource id's: none does nothing.
        parser.add_argument('terms', nargs='*', type=str)

    def handle(self, *args, **options):
        if len(options['terms']) > 0:
            all = ""
            started = False
            for t in options['terms']: 
                print("term={}".format(t))
                if started: 
                    all += " "
                all += t
                started = True
                
            # out = find_resources_by_subjects(options['terms'])
            out = find_resources_by_subjects([all])
            for thing in out:
                pprint(thing)
                res = get_resource_by_shortkey(thing.short_id)
                subjects = ''
                started = False
                for s in res.metadata.subjects.all():
                    if started:
                        subjects += " "
                    subjects += '"' + s.value + '"'
                    started = True
                print("{} {} {}".format(res.short_id,
                                        res.title.encode('ascii', 'ignore'),
                                        subjects.encode('ascii', 'ignore')))
        else:
            print "no terms listed"
