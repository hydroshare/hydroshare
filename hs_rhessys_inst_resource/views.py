import json

from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.core.urlresolvers import reverse

from django_docker_processes import tasks

from .models import *
from .forms import RunModelForm

def _getModelRunsForModel(request, model, token=None):
    import logging
    logger = logging.getLogger('django')
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
        my_run['logs'] = run.docker_process.logs

        # Check for run options
        options = run.modelrunoptions_set.all()
        for option in options:
            if option.name == 'TEC_FILE':
                my_run['TEC_FILE'] = option.value
        
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

        import logging
        logger = logging.getLogger('django')
        
        form = RunModelForm()

        my_model = get_object_or_404(InstResource, short_id=kwargs['resource_short_id'])
        logger.info(str(my_model))

        if my_model.docker_profile:
            kwargs['can_run'] = True

            form = RunModelForm(request.POST)
            if form.is_valid():
                has_run_options = True
                input_url = request.build_absolute_uri(my_model.bags.first().bag.url)
                
                title = form.cleaned_data['title']
                description = form.cleaned_data['description']
                model_command_line_parameters = form.cleaned_data['model_command_line_parameters']
                tecfile = form.cleaned_data['tec_file']
                if tecfile == '':
                    tecfile = None
                    has_run_options = False

                logger.info("Running model, input_url: {0}".format(input_url))
                logger.info("Form title: {0}".format(title))
                logger.info("TEC file: |{0}|".format(tecfile))
                
                env_dict = {'INPUT_URL':input_url}

                process = DockerProcess.objects.create(profile=my_model.docker_profile)
                run = ModelRun.objects.create(model_instance=my_model,
                                              docker_process=process,
                                              status='Running',
                                              title=title,
                                              description=description,
                                              model_command_line_parameters=model_command_line_parameters)
                
                # Build run options (if needed)
                if has_run_options:
                    options = {}
                    if tecfile:
                        options['TEC_FILE'] = tecfile
                        ModelRunOptions.objects.create(model_run=run,
                                                       name='TEC_FILE',
                                                       value=tecfile)

                    env_dict['MODEL_OPTIONS'] = json.dumps(options)

                logger.info("Resource ID (for now): {0}".format(my_model.get_slug()))
                env_dict['RID'] = my_model.get_slug()
                env_dict['RHESSYS_PROJECT'] = my_model.project_name.strip(os.sep)
                env_dict['RHESSYS_PARAMS'] = model_command_line_parameters

                keyword_args = {'env': env_dict,
                                'overwrite_images': True}
                logger.info(keyword_args)
                rebuild_image = False
                logger.info("Calling tasks.run_process.apply_async for process with token {0}...".format(process.token))
                promise = tasks.run_process.apply_async(args=[process, {}, rebuild_image], 
                                                        kwargs=keyword_args)
                # Reset form
                form = RunModelForm()
            else:
                logger.info("Form is not valid")
        else:
            logger.info("No docker profile found")

        kwargs['form'] = form

        run_info = _getModelRunsForModel(request, my_model)
        kwargs['run_info'] = run_info

        get_run_info_url = reverse('hs_rhessys_inst_resource-getruninfo', kwargs={
                'resource_short_id': kwargs['resource_short_id']
                })
        get_run_info_url = request.build_absolute_uri(get_run_info_url)
        kwargs['get_run_info_url'] = get_run_info_url

        return render(request, self.template_name, kwargs)


class GetRunInfoJSON(View):
    def get(self, request, *args, **kwargs):
        my_model = get_object_or_404(InstResource, short_id=kwargs['resource_short_id'])
        token = None
        if kwargs.has_key('token'):
            token = kwargs['token']
        response_data = _getModelRunsForModel(request, my_model, token)
        return HttpResponse(json.dumps(response_data), content_type='application/json')
