import json

from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.core.urlresolvers import reverse

from .models import *
from .forms import RunModelForm

def _getModelRunsForModel(request, model, token=None):
    #import logging
    #logger = logging.getLogger('django')
    if token:
        model_runs = ModelRun.objects.filter(model_instance=model, docker_process__token=token)
    else:
        model_runs = ModelRun.objects.filter(model_instance=model)
        
    run_info = []
    for run in model_runs:
        my_run = {}

        my_run['token'] = run.docker_process.token
        poll_url = reverse('hs_rhessys_inst_resource-getruninfo', kwargs={
                'resource_short_id': model.short_id,
                'token': run.docker_process.token
                })
        poll_url = request.build_absolute_uri(poll_url)
        my_run['poll_url'] = poll_url
        
        my_run['title'] = run.title
        my_run['description'] = run.description
        my_run['model_command_line_parameters'] = run.model_command_line_parameters
        my_run['status'] = run.status
        my_run['date_started'] = str(run.date_started)
        my_run['date_finished'] = str(run.date_finished)
        
        if run.model_results:
            results_url = "/r/{0}/".format(run.model_results.short_id) # TODO: use reverse to build this URL
            results_url = request.build_absolute_uri(results_url)
            my_run['results_url'] = results_url
            
        run_info.append(my_run)
    return run_info


class RunModelView(View):
    template_name = 'pages/runmodel.html'

    def get(self, request, *args, **kwargs):

        my_model = get_object_or_404(InstResource, short_id=kwargs['resource_short_id'])
        if my_model.docker_profile:
            kwargs['can_run'] = True
        else:
            kwargs['can_run'] = False

        kwargs['form'] = RunModelForm()

        run_info = _getModelRunsForModel(request, my_model)
        kwargs['run_info'] = run_info

        get_run_info_url = reverse('hs_rhessys_inst_resource-getruninfo', kwargs={
                'resource_short_id': kwargs['resource_short_id']
                })
        get_run_info_url = request.build_absolute_uri(get_run_info_url)
        kwargs['get_run_info_url'] = get_run_info_url

        return render(request, self.template_name, kwargs)

    def post(self, request, *args, **kwargs):
        return render(request, self.template_name, kwargs)


class GetRunInfoJSON(View):
    def get(self, request, *args, **kwargs):
        my_model = get_object_or_404(InstResource, short_id=kwargs['resource_short_id'])
        token = None
        if kwargs.has_key('token'):
            token = kwargs['token']
        response_data = _getModelRunsForModel(request, my_model, token)
        return HttpResponse(json.dumps(response_data), content_type='application/json')
