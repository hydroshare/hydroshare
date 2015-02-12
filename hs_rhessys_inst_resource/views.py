from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.core.urlresolvers import reverse

from .models import *
from .forms import RunModelForm

class RunModelView(View):
    template_name = 'pages/runmodel.html'

    def get(self, request, *args, **kwargs):

        my_model = get_object_or_404(InstResource, short_id=kwargs['resource_short_id'])
        if my_model.docker_profile:
            kwargs['can_run'] = True
        else:
            kwargs['can_run'] = False

        kwargs['form'] = RunModelForm()

        import logging
        logger = logging.getLogger('django')
        logger.info("Model runs for model: {0}".format(kwargs['resource_short_id']))

        model_runs = ModelRun.objects.filter(model_instance=my_model)
        run_info = []
        for run in model_runs:
            my_run = {}

            docker_process_poll_url = reverse('docker-process-poll-status', kwargs={
                    'profile_name': run.docker_process.profile.name,
                    'token': run.docker_process.token
                    })
            docker_process_poll_url = request.build_absolute_uri(docker_process_poll_url)
            my_run['docker_process_poll_url'] = docker_process_poll_url

            my_run['title'] = run.title
            my_run['description'] = run.description
            my_run['model_command_line_parameters'] = run.model_command_line_parameters
            my_run['status'] = run.status
            my_run['date_started'] = str(run.date_started)
            my_run['date_finished'] = str(run.date_finished)

            if run.model_results:
                results_url = "/r/{0}/".format(run.model_results.short_id)
                results_url = request.build_absolute_uri(results_url)
                my_run['results_url'] = results_url

            run_info.append(my_run)

        kwargs['run_info'] = run_info

        return render(request, self.template_name, kwargs)

    def post(self, request, *args, **kwargs):
        return render(request, self.template_name, kwargs)
