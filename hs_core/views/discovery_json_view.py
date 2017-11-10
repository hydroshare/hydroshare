import json
from django.http import HttpResponse
from haystack.generic_views import FacetedSearchView
from hs_core.discovery_form import DiscoveryForm
import time

# View class for generating JSON data format from Haystack
# returned JSON objects array is used for building the map view
class DiscoveryJsonView(FacetedSearchView):
    # set facet fields
    facet_fields = ['creators', 'subjects', 'resource_type', 'public', 'owners_names', 'discoverable', 'published', 'variable_names', 'sample_mediums', 'units_names']
    # declare form class to use in this view
    form_class = DiscoveryForm

    # overwrite Haystack generic_view.py form_valid() function to generate JSON response
    def form_valid(self, form):
        start1 = time.time()
        # initialize an empty array for holding the result objects with coordinate values
        coor_values = []
        # get query set
        self.queryset = form.search()
        end1 = time.time()
        elapsed_time1 = end1 - start1
        # When we have a GET request with search query, build our JSON objects array
        if len(self.request.GET):

            query_results = self.get_queryset()
            end1 = time.time()
            elapsed_time1 = end1 - start1

            start2 = time.time()
            # iterate all the search results
            for result in query_results:
                # initialize a null JSON object
                json_obj = {}

                # assign title and url values to the object
                json_obj['short_id'] = result.object.short_id;
                # This hits the Django database
                json_obj['title'] = result.object.metadata.title.value
                json_obj['resource_type'] = result.object.verbose_name
                # This hits the Django database 
                json_obj['get_absolute_url'] = result.object.get_absolute_url()
                json_obj['first_author'] = result.object.first_creator.name
                if result.object.first_creator.description:
                    json_obj['first_author_description'] = result.object.first_creator.description
                # iterate all the coverage values
                for coverage in result.object.metadata.coverages.all():

                    # if coverage type is point, assign 'east' and 'north' coordinates to the object
                    if coverage.type == 'point':
                        json_obj['coverage_type'] = coverage.type
                        json_obj['east'] = coverage.value['east']
                        json_obj['north'] = coverage.value['north']
                    # elif coverage type is box, assign 'northlimit', 'eastlimit', 'southlimit' and 'westlimit' coordinates to the object
                    elif coverage.type == 'box':
                        json_obj['coverage_type'] = coverage.type
                        json_obj['northlimit'] = coverage.value['northlimit']
                        json_obj['eastlimit'] = coverage.value['eastlimit']
                        json_obj['southlimit'] = coverage.value['southlimit']
                        json_obj['westlimit'] = coverage.value['westlimit']
                    # else, skip
                    else:
                        continue
                    # encode object to JSON format
                    coor_obj = json.dumps(json_obj)
                    # add JSON object the results array
                    coor_values.append(coor_obj)

            # encode the results results array to JSON array
            the_data = json.dumps(coor_values)
            # return JSON response
            end2 = time.time()
            elapsed_time2 = end2 - start2
            output_file = open('hs_core/views/performance_results/server_json_request.txt', 'a')
            output_file.write("solr query time: " + str(elapsed_time1) + " json building time:  "  + str(elapsed_time2) + '\n')
            output_file.close()
            return HttpResponse(the_data, content_type='application/json')