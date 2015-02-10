from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import View

class RunModelView(View):
    template_name = 'pages/runmodel.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, kwargs)

    def post(self, request, *args, **kwargs):
        return render(request, self.template_name, kwargs)
