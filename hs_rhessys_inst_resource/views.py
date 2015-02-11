from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.views.generic import View

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

        return render(request, self.template_name, kwargs)

    def post(self, request, *args, **kwargs):
        return render(request, self.template_name, kwargs)
