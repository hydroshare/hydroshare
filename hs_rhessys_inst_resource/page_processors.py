
from django.http import HttpResponseRedirect
from mezzanine.pages.page_processors import processor_for

from .models import InstResource
from .forms import InputForm

@processor_for(InstResource)
def main_page(request, page):
    print('in page_processors.main_page')
    
    import logging
    logger = logging.getLogger('django')
    logger.info('in page_processors.main_page, method: {0}'.format(request.method))

    content_model = page.get_content_model()
    if(request.method == 'POST'):
        form = InputForm(request.POST)
        if(form.is_valid()):
            content_model.name=form.cleaned_data['name']+' name set'
            content_model.git_username = form.cleaned_data['git_username']
            content_model.git_password = form.cleaned_data['git_password']
            content_model.git_branch = form.cleaned_data['git_branch']
            content_model.model_command_line_parameters = form.cleaned_data['model_command_line_parameters']
            #content_model.project_name = form.cleaned_data['project_name']
            #content_model.model_desc = form.cleaned_data['model_desc']
            #content_model.study_area_bbox = form.cleaned_data['study_area_bbox']
            #content_model.git_repo = form.cleaned_data['git_repo']
            #content_model.commit_id = form.cleaned_data['commit_id']
            content_model.save()

            input_url = content_model.bags.first().bag.url

            logger.info("Running model, input_url: {0}".format(input_url))

            env_dict = {'INPUT_URL':input_url}
            my_profile = get_object_or_404(DockerProfile, name='RHESSys_Docker_Profile')
            #my_profile = get_object_or_404(DockerProfile, name='Pandoc')
            #global process
            process = DockerProcess.objects.create(profile=my_profile) # creates a unique ID
            #promise = tasks.run_process.delay(process, **env_dict)
            promise = tasks.run_process.apply_async(args=[process, {}], **env_dict)
            logs = promise.get()
            print logs
            process.delete() # no reason to leave it hanging around in the database
        else:
            logger.info('form not valid')
    else:
        form = InputForm(initial={
            'project_name' : content_model.project_name,
            'model_desc' : content_model.model_desc,
            'git_repo' : content_model.git_repo,
            'commit_id' : content_model.commit_id,
            'study_area_bbox' : content_model.study_area_bbox
        })

    return  {'form': form}
