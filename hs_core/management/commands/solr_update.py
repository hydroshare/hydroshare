"""Update the SOLR repository for changes in resources
Optional argument --force does the update even if the record exists.
Optional argument --debug causes all exceptions to halt execution.
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_core.search_indexes import BaseResourceIndex
from haystack.query import SearchQuerySet


class Command(BaseCommand):
    help = "Update SOLR records."

    def add_arguments(self, parser):

        # Named (optional) arguments
        parser.add_argument(
            '--force',
            action='store_true',  # True for presence, False for absence
            dest='force',  # value is options['debug']
            help='force refresh for unchanged resources',
        )

        parser.add_argument(
            '--debug',
            action='store_true',  # True for presence, False for absence
            dest='debug',  # value is options['debug']
            help='debug by stopping on any exception',
        )

        # a list of resource id's: none acts on everything.
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):

        ind = BaseResourceIndex()
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                print("updating resource {}".format(rid))
                if not options['debug']:
                    try:
                        r = BaseResource.objects.get(short_id=rid)
                        if r.show_in_discover:
                            ind.update_object(r)
                    except BaseResource.DoesNotExist:
                        print("resource {} does not exist in Django".format(rid))
                    except Exception as e:
                        print("resource {} generated exception {}".format(rid, str(e)))
                else:
                    r = BaseResource.objects.get(short_id=rid)
                    if r.show_in_discover:
                        ind.update_object(r)
        else:
            sqs = SearchQuerySet().all()
            print("SOLR count = {}".format(sqs.count()))
            dqs = BaseResource.objects.filter(Q(raccess__discoverable=True)
                                              | Q(raccess__public=True)).select_related('raccess')
            print("Django count = {}".format(dqs.count()))

            # what is in Django that isn't in SOLR
            print("checking for resources in Django that aren't in SOLR...")
            found_in_solr = set()
            for r in sqs:
                found_in_solr.add(r.short_id)  # enable fast matching

            django_indexed = 0
            django_replaced = 0
            django_refreshed = 0
            res_show_in_discover = False
            for r in dqs.iterator():
                if not options['debug']:
                    try:
                        resource = get_resource_by_shortkey(r.short_id, or_404=False)
                        res_show_in_discover = resource.show_in_discover
                        if res_show_in_discover:
                            django_indexed += 1
                        else:
                            django_replaced += 1
                    except BaseResource.DoesNotExist:
                        # race condition in processing while in production
                        print("resource {} no longer found in Django.".format(r.short_id))
                        continue
                    except Exception as e:
                        print("resource {} generated exception {}".format(r.short_id, str(e)))
                else:
                    resource = get_resource_by_shortkey(r.short_id, or_404=False)
                    res_show_in_discover = resource.show_in_discover
                    if res_show_in_discover:
                        django_indexed += 1
                    else:
                        django_replaced += 1

                if res_show_in_discover and r.short_id not in found_in_solr:
                    print("{} {} NOT FOUND in SOLR: adding to index".format(
                        r.short_id, resource.discovery_content_type))
                    if not options['debug']:
                        try:
                            ind.update_object(r)
                            django_refreshed += 1
                        except Exception as e:
                            print("resource {} generated exception {}".format(r.short_id, str(e)))
                    else:
                        ind.update_object(r)
                        django_refreshed += 1

                # # This always returns True whether or not SOLR needs updating
                # # This is likely a Haystack bug.
                # elif ind.should_update(r):
                # update everything to be safe.

                elif options['force']:
                    if r.show_in_discover:
                        print("{} {}: refreshing index (forced)".format(
                              r.short_id, resource.discovery_content_type))
                        if not options['debug']:
                            try:
                                ind.update_object(r)
                                django_refreshed += 1
                            except Exception as e:
                                print("resource {} generated exception {}".format(r.short_id, str(e)))
                        else:
                            ind.update_object(r)
                            django_refreshed += 1

            # what is in SOLR that isn't in Django:
            print("checking for resources in SOLR that aren't in Django...")
            sqs = SearchQuerySet().all()  # refresh for changes from above
            solr_indexed = 0
            solr_replaced = 0
            solr_deleted = 0
            for r in sqs:
                try:
                    resource = get_resource_by_shortkey(r.short_id, or_404=False)
                    if resource.show_in_discover:
                        solr_indexed += 1
                    else:
                        solr_replaced += 1
                except BaseResource.DoesNotExist:
                    print("SOLR resource {} NOT FOUND in Django; removing from SOLR"
                          .format(r.short_id))
                    solr_key = f"hs_core.baseresource.{r.pk}"
                    ind.remove_object(solr_key)
                    solr_deleted += 1
                    continue

            print("Django contains {} discoverable resources and {} replaced resources"
                  .format(django_indexed, django_replaced))
            print("{} resources in Django refreshed in SOLR".format(django_refreshed))
            print("SOLR contains {} discoverable resources and {} replaced resources"
                  .format(solr_indexed, solr_replaced))
            print("{} resources not in Django removed from SOLR".format(solr_deleted))
