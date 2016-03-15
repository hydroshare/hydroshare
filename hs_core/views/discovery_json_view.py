import simplejson as json
from django.http import HttpResponse
from haystack.query import SearchQuerySet
from django import forms
from haystack.forms import FacetedSearchForm
from haystack.generic_views import FacetedSearchView
from django.core import serializers
from hs_core.discovery_form import DiscoveryForm

class DiscoveryJsonView(FacetedSearchView):
    facet_fields = ['author', 'subjects', 'resource_type', 'public', 'owners_names', 'discoverable']
    form_class = DiscoveryForm

    #def get_queryset(self):
    #    queryset = super(DiscoveryJsonView, self).get_queryset()
        # further filter queryset based on some set of criteria
    #    return queryset.filter(content="river")

    def form_valid(self, form):
        #the_data = []
        coor_values = []
        coordinate_dictionary = []
        self.queryset = form.search()
        if len(self.request.GET):
            #print("#############")
            #print (self.request.GET)
            for result in self.get_queryset():
                json_obj = {}
                json_obj['title'] = result.object.title
                json_obj['get_absolute_url'] = result.object.get_absolute_url()
                #print(dir(result.object.get_absolute_url))
                #print(result.object.get_absolute_url)
                # the_data.append({
                #     'result' : result.object
                # })
                #the_data.append(result.object)
                #json_obj = json.dumps(result.object,ensure_ascii=False)
                #json_objects.append(json_obj)
                for coverage in result.object.metadata.coverages.all():

                    if coverage.type == 'point':
                        json_obj['coverage_type'] = coverage.type;
                        #suggestions = [coverage.value['east']]
                        json_obj['east'] = coverage.value['east']
                        json_obj['north'] = coverage.value['north']
                    elif coverage.type == 'box':
                        json_obj['coverage_type'] = coverage.type;
                        json_obj['northlimit'] = coverage.value['northlimit']
                        json_obj['eastlimit'] = coverage.value['eastlimit']
                        json_obj['southlimit'] = coverage.value['southlimit']
                        json_obj['westlimit'] = coverage.value['westlimit']
                    else:
                        continue
                    #print(json_obj)
                    coor_obj = json.dumps(json_obj)
                    coor_values.append(coor_obj)
                        #east.append(coverage.value['east'])
                        #print(coverage.value['east'])
                        #for attr, value in coverage.value.__dict__.iteritems():
                        #    print attr, value

                #for attr, value in result.object.__dict__.iteritems():
                #    print attr, value
            #suggestions = [result.title for result in sqs]
            #urls = [result.object.get_absolute_url for result in sqs]
            the_data = json.dumps(coor_values)
            return HttpResponse(the_data, content_type='application/json')
        #else:
        #    return super(DiscoveryView, self).form_valid(form)
