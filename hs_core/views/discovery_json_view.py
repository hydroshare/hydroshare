import json
from django.http import HttpResponse
from haystack.generic_views import FacetedSearchView
from hs_core.discovery_form import DiscoveryForm


# View class for generating JSON data format from Haystack
# returned JSON objects array is used for building the map view
class DiscoveryJsonView(FacetedSearchView):
    # set facet fields
    facet_fields = ['creator', 'subject', 'resource_type', 'public',
                    'owner', 'accessibility', 'variable', 'units', 'sample_medium']
    # declare form class to use in this view
    form_class = DiscoveryForm

    # overwrite Haystack generic_view.py form_valid() function to generate JSON response
    def form_valid(self, form):

        # initialize an empty array for holding the result objects with coordinate values
        coor_values = []
        # get query set
        self.queryset = form.search()

        # When we have a GET request with search query, build our JSON objects array
        if len(self.request.GET):

            # iterate all the search results
            for result in self.get_queryset():
                # initialize a null JSON object
                json_obj = {}

                # fetch as much information as possible from stored fields
                solr = result.get_stored_fields()

                # assign title and url values to the object
                json_obj['short_id'] = solr['short_id']
                json_obj['title'] = solr['title']
                json_obj['resource_type'] = solr['resource_type']

                json_obj['get_absolute_url'] = solr['absolute_url']
                json_obj['first_author'] = solr['author']
                # TODO: this is redundant. The value always exists but oft has value 'none'.
                if solr['author_url']:
                    json_obj['first_author_url'] = solr['author_url']

                # iterate over all the coverage values
                if solr['coverages'] is not None:
                    for coverage in solr['coverages']:
                        json_coverage = json.loads(coverage)
                        if 'east' in json_coverage:
                            json_obj['coverage_type'] = 'point'
                            json_obj['east'] = json_coverage['east']
                            json_obj['north'] = json_coverage['north']
                        elif 'northlimit' in json_coverage:
                            json_obj['coverage_type'] = 'box'
                            json_obj['northlimit'] = json_coverage['northlimit']
                            json_obj['eastlimit'] = json_coverage['eastlimit']
                            json_obj['southlimit'] = json_coverage['southlimit']
                            json_obj['westlimit'] = json_coverage['westlimit']
                        # else, skip
                        else:
                            continue

                # encode object to JSON string format
                coor_obj = json.dumps(json_obj)
                # add JSON object the results array
                coor_values.append(coor_obj)

            # encode the results results array to JSON array
            the_data = json.dumps(coor_values)
            # return JSON response

            return HttpResponse(the_data, content_type='application/json')
        else:
            return HttpResponse(json.dumps('[]'), content_type='application/json')
