from django.shortcuts import render
from django.http import HttpResponseNotFound
from hs_core.page_processors import PageMock

def bad_request(request):
    return render(request, template_name='400.html', status=400, context={'page': PageMock()})

def page_not_found(request):
    return render(request, template_name='404.html', status=404, context={'page': PageMock()})

def permission_denied(request):
    return render(request, template_name='403.html', status=403, context={'page': PageMock()})

def server_error(request):
    return render(request, template_name='500.html', status=500, context={'page': PageMock()})
