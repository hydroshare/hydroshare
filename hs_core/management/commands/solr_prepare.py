"""
This calls all preparation routines involved in creating SOLR records.
It is used to debug SOLR harvesting. If any of these routines fails on
any resource, all harvesting ceases. This has caused many bugs.
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from hs_core.models import BaseResource
from hs_core.search_indexes import BaseResourceIndex
from pprint import pprint


def debug_harvest():
    ind = BaseResourceIndex()
    for obj in BaseResource.objects.filter(Q(raccess__discoverable=True)
                                           | Q(raccess__public=True)).distinct():
        print(("TESTING RESOURCE {}".format(obj.title)))
        print('sample_medium')
        pprint(ind.prepare_sample_medium(obj))
        print('creator')
        pprint(ind.prepare_creator(obj))
        print('title')
        pprint(ind.prepare_title(obj))
        print('abstract')
        pprint(ind.prepare_abstract(obj))
        print('author')
        pprint(ind.prepare_author(obj))
        print('author_url')
        pprint(ind.prepare_author_url(obj))
        print('creator')
        pprint(ind.prepare_creator(obj))
        print('contributor')
        pprint(ind.prepare_contributor(obj))
        print('subject')
        pprint(ind.prepare_subject(obj))
        print('organization')
        pprint(ind.prepare_organization(obj))
        print('publisher')
        pprint(ind.prepare_publisher(obj))
        print('availability')
        pprint(ind.prepare_availability(obj))
        print('replaced')
        pprint(ind.prepare_replaced(obj))
        print('coverage')
        pprint(ind.prepare_coverage(obj))
        print('coverage_type')
        pprint(ind.prepare_coverage_type(obj))
        print('east')
        pprint(ind.prepare_east(obj))
        print('north')
        pprint(ind.prepare_north(obj))
        print('northlimit')
        pprint(ind.prepare_northlimit(obj))
        print('eastlimit')
        pprint(ind.prepare_eastlimit(obj))
        print('southlimit')
        pprint(ind.prepare_southlimit(obj))
        print('westlimit')
        pprint(ind.prepare_westlimit(obj))
        print('start_date')
        pprint(ind.prepare_start_date(obj))
        print('end_date')
        pprint(ind.prepare_end_date(obj))
        print('format')
        pprint(ind.prepare_format(obj))
        print('identifier')
        pprint(ind.prepare_identifier(obj))
        print('language')
        pprint(ind.prepare_language(obj))
        print('source')
        pprint(ind.prepare_source(obj))
        print('relation')
        pprint(ind.prepare_relation(obj))
        print('geospatialrelation')
        pprint(ind.prepare_geospatialrelation(obj))
        print('resource_type')
        pprint(ind.prepare_resource_type(obj))
        print('comment')
        pprint(ind.prepare_comment(obj))
        print('owner_login')
        pprint(ind.prepare_owner_login(obj))
        print('owner')
        pprint(ind.prepare_owner(obj))
        print('geometry_type')
        pprint(ind.prepare_geometry_type(obj))
        print('field_name')
        pprint(ind.prepare_field_name(obj))
        print('field_type')
        pprint(ind.prepare_field_type(obj))
        print('field_type_code')
        pprint(ind.prepare_field_type_code(obj))
        print('variable')
        pprint(ind.prepare_variable(obj))
        print('variable_type')
        pprint(ind.prepare_variable_type(obj))
        print('variable_shape')
        pprint(ind.prepare_variable_shape(obj))
        print('variable_descriptive_name')
        pprint(ind.prepare_variable_descriptive_name(obj))
        print('variable_speciation')
        pprint(ind.prepare_variable_speciation(obj))
        print('site')
        pprint(ind.prepare_site(obj))
        print('method')
        pprint(ind.prepare_method(obj))
        print('quality_level')
        pprint(ind.prepare_quality_level(obj))
        print('data_source')
        pprint(ind.prepare_data_source(obj))
        print('sample_medium')
        pprint(ind.prepare_sample_medium(obj))
        print('units')
        pprint(ind.prepare_units(obj))
        print('units_type')
        pprint(ind.prepare_units_type(obj))
        print('absolute_url')
        pprint(ind.prepare_absolute_url(obj))
        print('extra')
        pprint(ind.prepare_extra(obj))

        # check whether this resource was found in SOLR right now.
        from haystack.query import SearchQuerySet
        found_in_solr = SearchQuerySet().filter(short_id=obj.short_id).count() > 0
        if found_in_solr:
            print("found in solr")
        else:
            print("NOT FOUND in solr")


class Command(BaseCommand):
    help = "Print debugging information about logical files."

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        debug_harvest()
